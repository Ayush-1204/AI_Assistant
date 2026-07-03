import logging
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.device import Device
from app.services.notifications.providers.base import BaseNotificationProvider
from app.config import settings

# Wait to import firebase_admin to avoid crashing if not installed yet
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    
    if settings.FIREBASE_CREDENTIALS_PATH and not firebase_admin._apps:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
except ImportError:
    firebase_admin = None

class PushNotificationProvider(BaseNotificationProvider):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send(self, user_id: int, title: str, message: str, **kwargs) -> bool:
        if firebase_admin is None or not firebase_admin._apps:
            logging.warning("[PushProvider] Firebase not initialized. Skipping push notification.")
            return False
            
        result = await self.db.execute(select(Device).where(Device.user_id == user_id, Device.active == True))
        devices = result.scalars().all()
        
        if not devices:
            return False
            
        tokens = [device.device_token for device in devices]
        
        msg = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=message,
            ),
            tokens=tokens,
        )
        
        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: messaging.send_each_for_multicast(msg)
            )
            logging.info(f"[PushProvider] FCM Push completed. Success: {response.success_count}, Failed: {response.failure_count}")
        except Exception as e:
            logging.error(f"[PushProvider] FCM Error: {e}")
            return False
            
        return True
