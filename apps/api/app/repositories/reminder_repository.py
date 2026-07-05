from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.reminder import Reminder

class ReminderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, reminder: Reminder) -> Reminder:
        self.session.add(reminder)
        await self.session.commit()
        await self.session.refresh(reminder)
        return reminder

    async def get_by_id(self, reminder_id: int, user_id: int) -> Reminder | None:
        result = await self.session.execute(
            select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[Reminder]:
        result = await self.session.execute(
            select(Reminder).where(Reminder.user_id == user_id).order_by(Reminder.reminder_time.asc())
        )
        return list(result.scalars().all())

    async def update(self, reminder: Reminder) -> Reminder:
        await self.session.commit()
        await self.session.refresh(reminder)
        return reminder

    async def delete(self, reminder: Reminder) -> None:
        await self.session.delete(reminder)
        await self.session.commit()
