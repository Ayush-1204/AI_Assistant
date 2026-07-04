from typing import Any, Dict, List
from app.services.ai.tools.base import BaseTool
from app.integrations.google.tasks import GoogleTasksService

class GoogleTasksTool(BaseTool):
    name: str = "google_tasks"
    description: str = (
        "Use this tool to interact with Google Tasks. "
        "Allows fetching pending tasks and creating new ones. "
        "Provide action='get_tasks' to retrieve tasks or 'create_task' alongside "
        "title, notes, and due date."
    )
    parameters_schema: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["get_tasks", "create_task"],
                "description": "What to do: 'get_tasks' or 'create_task'"
            },
            "title": {
                "type": "string",
                "description": "Title of the task to create (for create_task)"
            },
            "notes": {
                "type": "string",
                "description": "Optional notes or details for a new task"
            },
            "due": {
                "type": "string",
                "description": "Optional due date in RFC3339 format"
            }
        },
        "required": ["action"]
    }

    def __init__(self, google_tasks_service: GoogleTasksService):
        self.tasks_service = google_tasks_service

    async def execute(self, execution_context: dict, **kwargs) -> Any:
        action = kwargs.get("action")
        title = kwargs.get("title")
        notes = kwargs.get("notes")
        due = kwargs.get("due")
        
        user_id = execution_context.get("user_id")
        if not user_id:
            return "Error: user_id is missing from execution context."

        if not action:
            return "Error: action is required."

        if action == "get_tasks":
            tasks = await self.tasks_service.get_tasks(user_id=user_id)
            if not tasks:
                return "No pending Google Tasks found."
            return [
                {
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "notes": t.get("notes"),
                    "status": t.get("status"),
                    "due": t.get("due")
                }
                for t in tasks
            ]
            
        elif action == "create_task":
            if not title:
                return "Error: title is required to create a task."
            task = await self.tasks_service.insert_task(user_id=user_id, title=title, notes=notes, due=due)
            return f"Successfully created Google Task: '{task.get('title')}' with ID: {task.get('id')}"
            
        return f"Unknown action: {action}"
