from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification import Notification
from app.services.notifications.providers.base import BaseNotificationProvider


class DatabaseNotificationProvider(BaseNotificationProvider):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send(self, user_id: int, title: str, message: str, **kwargs) -> bool:
        db_notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=kwargs.get("type", "SYSTEM"),
            priority=kwargs.get("priority", 1),
            source=kwargs.get("source"),
            channels=kwargs.get("channels", ["db"])
        )
        self.db.add(db_notif)
        await self.db.commit()
        return True
