import asyncio
import logging

from app.services.notifications.providers.base import BaseNotificationProvider

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Central dispatcher coordinating multi-channel notification fan-out.
    """
    def __init__(self, providers: list[BaseNotificationProvider]):
        self.providers = providers

    async def notify(self, user_id: int, title: str, message: str, **kwargs) -> None:
        for provider in self.providers:
            provider_name = provider.__class__.__name__
            try:
                res = await provider.send(user_id, title, message, **kwargs)
                logger.debug(f"[{provider_name}] Successfully dispatched.")
            except Exception as e:
                logger.error(f"[{provider_name}] Dispatch failed: {e}")
