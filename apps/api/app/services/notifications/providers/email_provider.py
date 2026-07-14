import logging

from app.services.notifications.providers.base import BaseNotificationProvider


class EmailNotificationProvider(BaseNotificationProvider):
    async def send(self, user_id: int, title: str, message: str, **kwargs) -> bool:
        # In a real app we would query the user's email from db and use aiosmtplib/SendGrid
        logging.info(f"[EmailProvider] Enqueueing email for user {user_id}: {title}")
        return True
