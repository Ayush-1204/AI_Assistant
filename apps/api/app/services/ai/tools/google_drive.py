import json
from app.services.ai.tools.base import BaseTool
from app.integrations.google.drive import GoogleDriveService

class DriveTool(BaseTool):
    def __init__(self, service: GoogleDriveService):
        self.service = service
        
    @property
    def name(self) -> str:
        return "google_drive"
        
    @property
    def description(self) -> str:
        return "Manage user's Google Drive. List files, search, download file contents, read metadata, and delete files."
        
    @property
    def parameters_schema(self) -> dict:
        return {
            "action": "string (list | search | metadata | download | delete)",
            "query": "string (optional): search query",
            "file_id": "string (optional): Google Drive file ID",
            "mime_type": "string (optional): For downloading native Google Docs",
        }
        
    async def execute(self, execution_context: dict, **kwargs) -> str:
        action = kwargs.get("action")
        user_id = execution_context.get("user_id")
        if not user_id:
            return "Error: Unauthorized."
            
        try:
            if action == "list":
                rv = await self.service.list_files(user_id)
                return json.dumps(rv.get('files', []))[:2000]
            elif action == "search":
                rv = await self.service.search_files(user_id, kwargs.get('query', ''))
                return json.dumps(rv)[:2000]
            elif action == "metadata":
                file_id = kwargs.get('file_id')
                if not file_id: return "Error: Missing file_id"
                rv = await self.service.read_document_metadata(user_id, str(file_id))
                return json.dumps(rv)[:2000]
            elif action == "download":
                file_id = kwargs.get('file_id')
                if not file_id: return "Error: Missing file_id"
                rv = await self.service.download_file(user_id, str(file_id), kwargs.get('mime_type'))
                if isinstance(rv, bytes):
                    # Attempt decode
                    return f"File Content Prefix: {rv.decode('utf-8', errors='ignore')[:3000]}"
                return f"File downloaded"
            elif action == "delete":
                await self.service.delete_file(user_id, kwargs['file_id'])
                return "File deleted."
            else:
                return f"Error: Unknown drive action {action}."
        except Exception as e:
            return f"Drive execution error: {str(e)}"
