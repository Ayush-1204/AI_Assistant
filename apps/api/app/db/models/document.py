from enum import Enum

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql import func

from app.db.base import Base


class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    EXTRACTING = "EXTRACTING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    READY = "READY"
    INDEXING = "INDEXING"
    SEARCHABLE = "SEARCHABLE"
    FAILED = "FAILED"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    storage_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.UPLOADED,
        nullable=False,
    )

    page_count: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    language: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
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

    user = relationship(
        "User",
        back_populates="documents",
    )

    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )