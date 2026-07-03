from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.oauth_credential import OAuthCredential

class OAuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int, provider: str = "google") -> Optional[OAuthCredential]:
        stmt = select(OAuthCredential).where(
            OAuthCredential.user_id == user_id,
            OAuthCredential.provider == provider
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
        
    async def save_or_update(
        self,
        user_id: int,
        access_token: str,
        refresh_token: Optional[str] = None,
        scopes: Optional[str] = None,
        expires_at=None,
        provider: str = "google"
    ) -> OAuthCredential:
        
        existing = await self.get_by_user_id(user_id, provider)
        if existing:
            existing.access_token = access_token
            if refresh_token is not None:
                existing.refresh_token = refresh_token
            if scopes is not None:
                existing.scopes = scopes
            if expires_at is not None:
                existing.expires_at = expires_at
                
            self.db.add(existing)
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            new_cred = OAuthCredential(
                user_id=user_id,
                provider=provider,
                access_token=access_token,
                refresh_token=refresh_token,
                scopes=scopes,
                expires_at=expires_at
            )
            self.db.add(new_cred)
            await self.db.commit()
            await self.db.refresh(new_cred)
            return new_cred

    async def delete_by_user_id(self, user_id: int, provider: str = "google") -> bool:
        existing = await self.get_by_user_id(user_id, provider)
        if existing:
            await self.db.delete(existing)
            await self.db.commit()
            return True
        return False
