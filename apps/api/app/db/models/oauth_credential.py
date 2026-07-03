from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base import Base

class OAuthCredential(Base):
    __tablename__ = "oauth_credentials"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    
    provider: Mapped[str] = mapped_column(
        String(50), 
        default="google", 
        nullable=False,
        index=True
    )
    
    access_token: Mapped[str] = mapped_column(
        String(2048), 
        nullable=False
    )
    
    refresh_token: Mapped[str] = mapped_column(
        String(2048), 
        nullable=True
    )
    
    scopes: Mapped[str] = mapped_column(
        String(1024), 
        nullable=True
    )
    
    expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
