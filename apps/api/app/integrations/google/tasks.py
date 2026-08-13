import logging
from typing import Any, cast

from googleapiclient.discovery import build

from app.integrations.google.auth import GoogleAuthService

logger = logging.getLogger(__name__)

class GoogleTasksService:
    def __init__(self, auth_service: GoogleAuthService):
        self.auth_service = auth_service
        
    async def _get_client(self, user_id: int):
        creds = await self.auth_service.get_credentials(user_id)
        if not creds:
            raise ValueError(f"No valid Google credentials found for user {user_id}")
        return build('tasks', 'v1', credentials=creds)
        
    async def get_task_lists(self, user_id: int) -> list[dict[str, Any]]:
        try:
            service = await self._get_client(user_id)
            lists_result = service.tasklists().list().execute()
            return cast(list[dict[str, Any]], lists_result.get("items", []))
        except Exception as e:
            logger.error(f"Failed to fetch Google Task Lists: {e}")
            return []

    async def get_tasks(self, user_id: int, task_list_id: str = "@default") -> list[dict[str, Any]]:
        try:
            service = await self._get_client(user_id)
            tasks_result = service.tasks().list(tasklist=task_list_id, showCompleted=False).execute()
            return cast(list[dict[str, Any]], tasks_result.get("items", []))
        except Exception as e:
            logger.error(f"Failed to fetch Google Tasks: {e}")
            return []

    async def insert_task(self, user_id: int, title: str, notes: str | None = None, due: str | None = None, task_list_id: str = "@default") -> dict[str, Any]:
        try:
            service = await self._get_client(user_id)
            payload = {"title": title}
            if notes:
                payload["notes"] = notes
            if due:
                payload["due"] = due
                
            task_result = service.tasks().insert(tasklist=task_list_id, body=payload).execute()
            return cast(dict[str, Any], task_result)
        except Exception as e:
            logger.error(f"Failed to insert Google Task: {e}")
            raise

    async def update_task(self, user_id: int, task_id: str, title: str | None = None, notes: str | None = None, due: str | None = None, status: str | None = None, task_list_id: str = "@default") -> dict[str, Any]:
        try:
            service = await self._get_client(user_id)
            payload = service.tasks().get(tasklist=task_list_id, task=task_id).execute()
            
            if title is not None:
                payload["title"] = title
            if notes is not None:
                payload["notes"] = notes
            if due is not None:
                payload["due"] = due
            if status is not None:
                payload["status"] = status
                
            task_result = service.tasks().update(tasklist=task_list_id, task=task_id, body=payload).execute()
            return cast(dict[str, Any], task_result)
        except Exception as e:
            logger.error(f"Failed to update Google Task: {e}")
            raise

    async def delete_task(self, user_id: int, task_id: str, task_list_id: str = "@default") -> bool:
        try:
            service = await self._get_client(user_id)
            service.tasks().delete(tasklist=task_list_id, task=task_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to delete Google Task: {e}")
            return False
