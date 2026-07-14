from datetime import datetime

from app.db.models.reminder import Reminder
from app.repositories.reminder_repository import ReminderRepository


class ReminderService:
    def __init__(self, reminder_repository: ReminderRepository):
        self.reminder_repository = reminder_repository

    async def create_reminder(self, user_id: int, title: str, reminder_time: datetime, is_recurring: bool = False) -> Reminder:
        reminder = Reminder(
            user_id=user_id,
            title=title,
            reminder_time=reminder_time,
            is_recurring=is_recurring
        )
        return await self.reminder_repository.create(reminder)

    async def get_reminder(self, reminder_id: int, user_id: int) -> Reminder | None:
        return await self.reminder_repository.get_by_id(reminder_id, user_id)

    async def list_reminders(self, user_id: int) -> list[Reminder]:
        return await self.reminder_repository.list_by_user(user_id)

    async def mark_complete(self, reminder_id: int, user_id: int) -> Reminder | None:
        reminder = await self.reminder_repository.get_by_id(reminder_id, user_id)
        if not reminder:
            return None
        reminder.is_completed = True
        return await self.reminder_repository.update(reminder)

    async def delete_reminder(self, reminder_id: int, user_id: int) -> bool:
        reminder = await self.reminder_repository.get_by_id(reminder_id, user_id)
        if not reminder:
            return False
        await self.reminder_repository.delete(reminder)
        return True
