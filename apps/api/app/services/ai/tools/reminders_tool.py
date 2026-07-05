from typing import Any
from app.services.ai.tools.base import BaseTool
from app.services.reminders.reminder_service import ReminderService
from datetime import datetime

class RemindersTool(BaseTool):
    def __init__(self, reminder_service: ReminderService):
        self.reminder_service = reminder_service

    @property
    def name(self) -> str:
        return "reminders"

    @property
    def description(self) -> str:
        return "Manage user reminders."

    @property
    def parameters_schema(self) -> dict:
        return {
             "type": "object",
             "properties": {
                  "action": {"type": "string", "enum": ["create", "list", "complete", "delete"]},
                  "title": {"type": "string"},
                  "reminder_id": {"type": "integer"},
                  "reminder_time": {"type": "string", "description": "ISO format datetime"},
             },
             "required": ["action"]
        }

    async def execute(self, execution_context: dict[str, Any], **kwargs: Any) -> Any:
        user_id = execution_context.get("user_id")
        if user_id is None:
            return "Error: missing user_id"
        action = kwargs.get("action")
        
        if action == "create":
            time = datetime.fromisoformat(kwargs["reminder_time"])
            rem = await self.reminder_service.create_reminder(user_id, kwargs["title"], time)
            return f"Reminder created for {time}."
        elif action == "list":
            rems = await self.reminder_service.list_reminders(user_id)
            return [{"id": r.id, "title": r.title, "time": str(r.reminder_time), "completed": r.is_completed} for r in rems]
        elif action == "complete":
            rem = await self.reminder_service.mark_complete(kwargs["reminder_id"], user_id)
            return "Reminder completed." if rem else "Reminder not found."
        elif action == "delete":
            success = await self.reminder_service.delete_reminder(kwargs["reminder_id"], user_id)
            return "Reminder deleted." if success else "Reminder not found."
