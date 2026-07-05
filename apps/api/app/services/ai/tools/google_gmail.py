import json
from app.services.ai.tools.base import BaseTool
from app.integrations.google.gmail import GoogleGmailService

class GmailTool(BaseTool):
    def __init__(self, service: GoogleGmailService):
        self.service = service
        
    @property
    def name(self) -> str:
        return "google_gmail"
        
    @property
    def description(self) -> str:
        return "Manage user's Gmail. Actions: list_unread, search, read, draft, send, reply, archive."
        
    @property
    def parameters_schema(self) -> dict:
        return {
            "action": "string (list_unread | search | read | draft | send | reply | archive)",
            "query": "string (optional): standard Gmail search query",
            "message_id": "string (optional): for read, reply, archive",
            "to": "string (optional): email address for send, draft",
            "subject": "string (optional): for send, draft",
            "body": "string (optional): email body for send, draft, reply",
            "max_results": "integer (optional): limit for searches"
        }
        
    async def execute(self, execution_context: dict, **kwargs) -> str:
        action = kwargs.get("action")
        user_id = execution_context.get("user_id")
        if not user_id:
            return "Error: Unauthorized."
            
        try:
            if action == "list_unread":
                rv = await self.service.list_unread_emails(user_id, kwargs.get('max_results', 5))
                return f"Unread IDs: {json.dumps(rv)}"
            elif action == "search":
                rv = await self.service.search_emails(user_id, kwargs.get('query', ''), kwargs.get('max_results', 5))
                return f"Found IDs: {json.dumps(rv)}"
            elif action == "read":
                rv = await self.service.read_email(user_id, kwargs['message_id'])
                return json.dumps(rv.get('snippet', ''))
            elif action == "draft":
                await self.service.draft_email(user_id, kwargs['to'], kwargs['subject'], kwargs.get('body', ''))
                return "Draft saved successfully."
            elif action == "send":
                await self.service.send_email(user_id, kwargs['to'], kwargs['subject'], kwargs.get('body', ''))
                return "Email sent successfully."
            elif action == "reply":
                await self.service.reply(user_id, kwargs['message_id'], kwargs['body'])
                return "Reply sent."
            elif action == "archive":
                await self.service.archive(user_id, kwargs['message_id'])
                return "Thread archived."
            else:
                return f"Error: Unknown gmail action {action}."
        except Exception as e:
            return f"Gmail execution error: {str(e)}"
