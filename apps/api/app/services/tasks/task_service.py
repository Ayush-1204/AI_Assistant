from datetime import datetime

from app.db.models.task import Task
from app.repositories.task_repository import TaskRepository


class TaskService:
    def __init__(self, task_repository: TaskRepository):
        self.task_repository = task_repository

    async def create_task(self, user_id: int, title: str, priority: int = 1, due_date: datetime | None = None, project: str | None = None, tags: list[str] | None = None) -> Task:
        task = Task(
            user_id=user_id,
            title=title,
            priority=priority,
            due_date=due_date,
            project=project,
            tags=tags or []
        )
        return await self.task_repository.create(task)

    async def get_task(self, task_id: int, user_id: int) -> Task | None:
        return await self.task_repository.get_by_id(task_id, user_id)

    async def list_tasks(self, user_id: int) -> list[Task]:
        return await self.task_repository.list_by_user(user_id)

    async def mark_complete(self, task_id: int, user_id: int) -> Task | None:
        task = await self.task_repository.get_by_id(task_id, user_id)
        if not task:
            return None
        task.is_completed = True
        return await self.task_repository.update(task)

    async def update_task(self, task_id: int, user_id: int, updates: dict) -> Task | None:
        task = await self.task_repository.get_by_id(task_id, user_id)
        if not task:
            return None
        
        for k, v in updates.items():
            if hasattr(task, k):
                setattr(task, k, v)
                
        return await self.task_repository.update(task)

    async def delete_task(self, task_id: int, user_id: int) -> bool:
        task = await self.task_repository.get_by_id(task_id, user_id)
        if not task:
            return False
        await self.task_repository.delete(task)
        return True
