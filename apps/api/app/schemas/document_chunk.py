from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentChunkResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    chunk_index: int

    content: str

    token_count: int

    chunk_metadata: dict | None

    created_at: datetime