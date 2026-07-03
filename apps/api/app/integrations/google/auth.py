import logging
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow

from app.config import settings
from app.repositories.oauth_repository import OAuthRepository

logger = logging.getLogger(__name__)

class GoogleAuthService:
    def __init__(self, oauth_repo: OAuthRepository):
        self.oauth_repo = oauth_repo

        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID or "",
                "client_secret": settings.GOOGLE_CLIENT_SECRET or "",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI] if settings.GOOGLE_REDIRECT_URI else [],
            }
        }
        
        self.scopes = [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/drive"
        ]

        if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
            self.flow = Flow.from_client_config(
                client_config,
                scopes=self.scopes
            )
            if settings.GOOGLE_REDIRECT_URI:
                self.flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        else:
            self.flow = None

    def get_authorization_url(self) -> str:
        if not self.flow:
            raise ValueError("Google OAuth is not configured properly in settings")
        
        auth_url, _ = self.flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return auth_url

    async def exchange_code(self, code: str, user_id: int):
        if not self.flow:
            raise ValueError("Google OAuth is not configured properly in settings")
            
        self.flow.fetch_token(code=code)
        credentials = self.flow.credentials
        
        await self.oauth_repo.save_or_update(
            user_id=user_id,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            scopes=",".join(credentials.scopes) if credentials.scopes else None,
            expires_at=credentials.expiry,
            provider="google"
        )
        
    async def get_credentials(self, user_id: int) -> Optional[Credentials]:
        record = await self.oauth_repo.get_by_user_id(user_id, "google")
        if not record:
            return None
            
        creds = Credentials(
            token=record.access_token,
            refresh_token=record.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=record.scopes.split(",") if record.scopes else self.scopes
        )
        
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                await self.oauth_repo.save_or_update(
                    user_id=user_id,
                    access_token=creds.token,
                    refresh_token=creds.refresh_token,
                    scopes=",".join(creds.scopes) if creds.scopes else record.scopes,
                    expires_at=creds.expiry,
                    provider="google"
                )
                logger.info(f"Successfully refreshed Google OAuth credentials for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to refresh Google OAuth credentials for user {user_id}: {e}")
                
        return creds
