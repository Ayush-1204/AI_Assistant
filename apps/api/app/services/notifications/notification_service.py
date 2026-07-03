import asyncio
import logging
from typing import List
from app.services.notifications.providers.base import BaseNotificationProvider

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Central dispatcher coordinating multi-channel notification fan-out.
    """
    def __init__(self, providers: List[BaseNotificationProvider]):
        self.providers = providers

    async def notify(self, user_id: int, title: str, message: str, **kwargs) -> None:
        tasks = [
            provider.send(user_id, title, message, **kwargs)
            for provider in self.providers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, res in enumerate(results):
            provider_name = self.providers[i].__class__.__name__
            if isinstance(res, Exception):
                logger.error(f"[{provider_name}] Dispatch failed: {res}")
            else:
                logger.debug(f"[{provider_name}] Successfully dispatched.")
