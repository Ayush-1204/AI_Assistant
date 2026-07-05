import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.oauth_state import OAuthState

class OAuthStateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_state(self, user_id: Optional[int] = None, expires_in_minutes: int = 15) -> str:
        state_str = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        
        state_record = OAuthState(
            state=state_str,
            user_id=user_id,
            expires_at=expires_at
        )
        self.db.add(state_record)
        await self.db.commit()
        return state_str
        
    async def consume_state(self, state: str) -> Tuple[bool, Optional[int]]:
        stmt = select(OAuthState).where(OAuthState.state == state)
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        
        if not record:
            # State is either invalid or was already used/invalidated
            return False, None
            
        user_id = record.user_id
        
        exp_time = record.expires_at
        is_expired = True
        if isinstance(exp_time, datetime):
            if exp_time.tzinfo is None:
                exp_time = exp_time.replace(tzinfo=timezone.utc)
            is_expired = datetime.now(timezone.utc) > exp_time
        
        # Invalidate state securely to prevent replay attacks (Single-use property)
        await self.db.delete(record)
        await self.db.commit()
        
        if is_expired:
            return False, None
            
        return True, user_id
