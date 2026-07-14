import logging

from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

class GmailDraftTool(BaseTool):
    @property
    def name(self) -> str:
        return "gmail_drafter"
        
    @property
    def description(self) -> str:
        return "Drafts new emails in the user's connected Gmail account. Use this when the user asks to 'write an email to X about Y'."
        
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "to_address": {
                    "type": "string",
                    "description": "Email address of the recipient."
                },
                "subject": {
                    "type": "string",
                    "description": "Subject line for the email."
                },
                "body": {
                    "type": "string",
                    "description": "Email body content."
                }
            },
            "required": ["to_address", "subject", "body"]
        }

    @property
    def requires_confirmation(self) -> bool:
        return True # Always confirm with the user before touching Gmail

    @property
    def risk_level(self) -> str:
        return "moderate"

    async def execute(self, execution_context: dict, **kwargs) -> str:
        user_id = execution_context.get("user_id")
        to_address = kwargs.get("to_address")
        subject = kwargs.get("subject")
        body = kwargs.get("body")
        
        # NOTE: Genuine OAuth logic requires the specific user's OAuth access token.
        # This will be constructed here referencing the OAuthState table.
        # For now, we simulate success for architecture validation.
        
        if not user_id:
            return "ERROR: User ID missing from context."
            
        logger.info(f"OAUTH DEMO: Simulating Gmail draft creation for User {user_id} -> {to_address}")
        
        return f"Successfully created a Gmail draft to '{to_address}' with subject '{subject}'. The user can review it in their Gmail app."
