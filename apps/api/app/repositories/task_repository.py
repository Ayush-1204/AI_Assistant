from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.task import Task

class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, task: Task) -> Task:
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_by_id(self, task_id: int, user_id: int) -> Task | None:
        result = await self.session.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[Task]:
        result = await self.session.execute(
            select(Task).where(Task.user_id == user_id).order_by(Task.due_date.asc().nulls_last(), Task.priority.desc())
        )
        return list(result.scalars().all())

    async def update(self, task: Task) -> Task:
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        await self.session.delete(task)
        await self.session.commit()
