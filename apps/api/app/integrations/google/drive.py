import io
import logging

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from app.integrations.google.auth import GoogleAuthService

logger = logging.getLogger(__name__)

class GoogleDriveService:
    def __init__(self, auth_service: GoogleAuthService):
        self.auth_service = auth_service
        
    async def _get_client(self, user_id: int):
        creds = await self.auth_service.get_credentials(user_id)
        if not creds:
            raise ValueError(f"No valid Google credentials found for user {user_id}")
        return build('drive', 'v3', credentials=creds)

    async def list_files(self, user_id: int, max_results: int = 10, page_token: str | None = None):
        service = await self._get_client(user_id)
        results = service.files().list(
            pageSize=max_results,
            pageToken=page_token,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
            q="trashed = false"
        ).execute()
        return results

    async def search_files(self, user_id: int, query: str, max_results: int = 10):
        # query e.g. "name contains 'Project'"
        service = await self._get_client(user_id)
        results = service.files().list(
            pageSize=max_results,
            q=f"trashed = false and {query}",
            fields="files(id, name, mimeType, modifiedTime)"
        ).execute()
        return results.get('files', [])

    async def read_document_metadata(self, user_id: int, file_id: str):
        service = await self._get_client(user_id)
        result = service.files().get(
            fileId=file_id,
            fields="id, name, mimeType, modifiedTime, size, owners"
        ).execute()
        return result

    async def download_file(self, user_id: int, file_id: str, mime_type: str | None = None):
        service = await self._get_client(user_id)
        request = service.files().get_media(fileId=file_id)
        
        if mime_type and mime_type.startswith('application/vnd.google-apps'):
            # It's a Google native doc, must be exported
            export_mime = 'application/pdf'
            if 'document' in mime_type:
                export_mime = 'text/plain' # Easiest text format to AI
            request = service.files().export_media(fileId=file_id, mimeType=export_mime)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            
        fh.seek(0)
        return fh.read()

    async def upload_file(self, user_id: int, filename: str, filepath: str, mime_type: str):
        service = await self._get_client(user_id)
        file_metadata = {'name': filename}
        media = MediaFileUpload(filepath, mimetype=mime_type)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        return file.get('id')

    async def delete_file(self, user_id: int, file_id: str):
        service = await self._get_client(user_id)
        service.files().delete(fileId=file_id).execute()
        return True
