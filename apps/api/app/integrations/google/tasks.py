import logging
from typing import Any

import httpx

from app.integrations.google.auth import GoogleAuthService

logger = logging.getLogger(__name__)

class GoogleTasksService:
    def __init__(self, auth_service: GoogleAuthService):
        self.auth_service = auth_service
        
    async def get_task_lists(self, user_id: int) -> list[dict[str, Any]]:
        credentials = await self.auth_service.get_credentials(user_id)
        if not credentials:
            return []
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://tasks.googleapis.com/tasks/v1/users/@me/lists",
                    headers={"Authorization": f"Bearer {credentials.token}"}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("items", [])
        except Exception as e:
            logger.error(f"Failed to fetch Google Task Lists: {e}")
            return []

    async def get_tasks(self, user_id: int, task_list_id: str = "@default") -> list[dict[str, Any]]:
        credentials = await self.auth_service.get_credentials(user_id)
        if not credentials:
            return []
            
        try:
            # First ensure we have a valid task list if @default fails
            if task_list_id == "@default":
                lists = await self.get_task_lists(user_id)
                if lists:
                    task_list_id = lists[0]["id"]
                    
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://tasks.googleapis.com/tasks/v1/lists/{task_list_id}/tasks?showCompleted=false",
                    headers={"Authorization": f"Bearer {credentials.token}"}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("items", [])
        except Exception as e:
            logger.error(f"Failed to fetch Google Tasks: {e}")
            return []

    async def insert_task(self, user_id: int, title: str, notes: str | None = None, due: str | None = None, task_list_id: str = "@default") -> dict[str, Any]:
        credentials = await self.auth_service.get_credentials(user_id)
        if not credentials:
            raise Exception("No valid Google access token available")
            
        try:
            if task_list_id == "@default":
                lists = await self.get_task_lists(user_id)
                if lists:
                    task_list_id = lists[0]["id"]
                    
            payload = {"title": title}
            if notes:
                payload["notes"] = notes
            if due:
                payload["due"] = due
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://tasks.googleapis.com/tasks/v1/lists/{task_list_id}/tasks",
                    headers={"Authorization": f"Bearer {credentials.token}"},
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to insert Google Task: {e}")
            raise
