from datetime import datetime
from typing import Any

from app.services.ai.tools.base import BaseTool
from app.services.tasks.task_service import TaskService


class TasksTool(BaseTool):
    def __init__(self, task_service: TaskService):
        self.task_service = task_service

    @property
    def name(self) -> str:
        return "tasks"

    @property
    def description(self) -> str:
        return "Manage user tasks. Use to fetch due dates, create tasks, or mark tasks as completed."

    @property
    def parameters_schema(self) -> dict:
        return {
             "type": "object",
             "properties": {
                  "action": {"type": "string", "enum": ["create", "list", "complete", "delete"]},
                  "title": {"type": "string"},
                  "task_id": {"type": "integer"},
                  "due_date": {"type": "string", "description": "ISO format date"},
             },
             "required": ["action"]
        }
    
    async def execute(self, execution_context: dict[str, Any], **kwargs: Any) -> Any:
        user_id = execution_context.get("user_id")
        if user_id is None:
            return "Error: missing user_id"
        action = kwargs.get("action")
        
        if action == "create":
            due_date = datetime.fromisoformat(kwargs["due_date"].replace("Z", "+00:00")) if "due_date" in kwargs else None
            task = await self.task_service.create_task(user_id, kwargs["title"], due_date=due_date)
            return f"Task '{task.title}' created with ID {task.id}."
        elif action == "list":
            tasks = await self.task_service.list_tasks(user_id)
            return [{"id": t.id, "title": t.title, "due": str(t.due_date), "completed": t.is_completed} for t in tasks]
        elif action == "complete":
            task = await self.task_service.mark_complete(kwargs["task_id"], user_id)
            return "Task completed." if task else "Task not found."
        elif action == "delete":
            success = await self.task_service.delete_task(kwargs["task_id"], user_id)
            return "Task deleted." if success else "Task not found."
