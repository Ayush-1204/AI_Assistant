import logging
from fastapi import APIRouter, Header, Request, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models.watch_channel import WatchChannel
from app.integrations.google.auth import GoogleAuthService
from app.integrations.google.calendar import GoogleCalendarService
from app.repositories.oauth_repository import OAuthRepository

# Optional: if you add a WebSocket manager later, you'd import it here to notify clients.
from app.routers.dashboard import calendar_ws_manager 

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

async def process_calendar_sync(user_id: int, channel_id: str):
    """Background task to fetch deltas and broadcast to the user's active WebSocket."""
    async with AsyncSessionLocal() as db:
        repo = OAuthRepository(db)
        auth = GoogleAuthService(repo)
        cal = GoogleCalendarService(auth)
        
        result = await db.execute(select(WatchChannel).where(WatchChannel.channel_id == channel_id))
        watch = result.scalar_one_or_none()
        if not watch:
            logger.error(f"Process sync failed: unknown channel_id {channel_id}")
            return
            
        try:
            # Sync delta updates the sync_token in the DB and returns changed events
            events = await cal.sync_delta(user_id, watch, db)
            if events:
                # Broadcast payload to the client!
                payload = {
                    "type": "CALENDAR_SYNC_UPDATE",
                    "channel_id": channel_id,
                    "events": events
                }
                await calendar_ws_manager.send_personal_message(payload, user_id)
        except Exception as e:
            logger.error(f"Failed to process calendar sync for user {user_id}: {e}")

@router.post("/calendar")
async def calendar_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_goog_channel_id: str = Header(default=""),
    x_goog_channel_token: str = Header(default=""),
    x_goog_resource_state: str = Header(default=""),
):
    if not x_goog_channel_id or not x_goog_channel_token:
        raise HTTPException(status_code=400, detail="Missing Google headers")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(WatchChannel).where(WatchChannel.channel_id == x_goog_channel_id))
        watch = result.scalar_one_or_none()
        
        if not watch or watch.channel_token != x_goog_channel_token:
            # Token mismatch or unknown channel -> 403
            logger.warning(f"Unauthorized webhook ping for channel {x_goog_channel_id}")
            raise HTTPException(status_code=403, detail="Forbidden")
            
        if x_goog_resource_state == "sync":
            # Initial sync notification, just return 200
            return {"status": "ok"}
            
        if x_goog_resource_state in ["exists", "update"]:
            # Normal change notification -> enqueue background task
            background_tasks.add_task(process_calendar_sync, watch.user_id, x_goog_channel_id)
            
    return {"status": "accepted"}
