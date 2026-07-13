import base64
import logging
from email.message import EmailMessage

from googleapiclient.discovery import build

from app.integrations.google.auth import GoogleAuthService

logger = logging.getLogger(__name__)

class GoogleGmailService:
    def __init__(self, auth_service: GoogleAuthService):
        self.auth_service = auth_service
        
    async def _get_client(self, user_id: int):
        creds = await self.auth_service.get_credentials(user_id)
        if not creds:
            raise ValueError(f"No valid Google credentials found for user {user_id}")
        return build('gmail', 'v1', credentials=creds)

    async def list_unread_emails(self, user_id: int, max_results: int = 10):
        service = await self._get_client(user_id)
        results = service.users().messages().list(userId='me', q="is:unread", maxResults=max_results).execute()
        messages = results.get('messages', [])
        return messages

    async def search_emails(self, user_id: int, query: str, max_results: int = 10):
        service = await self._get_client(user_id)
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        return results.get('messages', [])

    async def read_email(self, user_id: int, message_id: str):
        service = await self._get_client(user_id)
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        return message

    async def draft_email(self, user_id: int, to: str, subject: str, body: str):
        service = await self._get_client(user_id)
        message = EmailMessage()
        message.set_content(body)
        message['To'] = to
        message['From'] = 'me'
        message['Subject'] = subject
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'message': {'raw': encoded_message}}
        draft = service.users().drafts().create(userId='me', body=create_message).execute()
        return draft

    async def send_email(self, user_id: int, to: str, subject: str, body: str):
        service = await self._get_client(user_id)
        message = EmailMessage()
        message.set_content(body)
        message['To'] = to
        message['From'] = 'me'
        message['Subject'] = subject
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        send_message = service.users().messages().send(userId='me', body=create_message).execute()
        return send_message

    async def reply(self, user_id: int, message_id: str, body: str):
        service = await self._get_client(user_id)
        original_msg = service.users().messages().get(userId='me', id=message_id, format='metadata', metadataHeaders=['Subject', 'From', 'Message-ID']).execute()
        headers = original_msg.get('payload', {}).get('headers', [])
        
        subject = ""
        to = ""
        thread_id = original_msg.get('threadId')
        msg_id_header = ""
        
        for header in headers:
            name = header.get('name', '').lower()
            if name == 'subject':
                subject = header.get('value', '')
                if not subject.lower().startswith('re:'):
                    subject = f"Re: {subject}"
            elif name == 'from':
                to = header.get('value', '')
            elif name == 'message-id':
                msg_id_header = header.get('value', '')

        message = EmailMessage()
        message.set_content(body)
        message['To'] = to
        message['From'] = 'me'
        message['Subject'] = subject
        message['In-Reply-To'] = msg_id_header
        message['References'] = msg_id_header
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message, 'threadId': thread_id}
        send_message = service.users().messages().send(userId='me', body=create_message).execute()
        return send_message

    async def archive(self, user_id: int, message_id: str):
        service = await self._get_client(user_id)
        # Assuming INBOX is the label to remove to archive it
        modify_request = {
            'removeLabelIds': ['INBOX']
        }
        service.users().messages().modify(userId='me', id=message_id, body=modify_request).execute()
        return True
