from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    EXTRACTING = "EXTRACTING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    READY = "READY"
    FAILED = "FAILED"


class DocumentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    title: str

    original_filename: str

    mime_type: str

    file_size: int

    status: DocumentStatus

    page_count: int | None

    language: str | None

    created_at: datetime