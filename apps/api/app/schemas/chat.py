from pydantic import BaseModel


class ChatRequest(BaseModel):
    conversation_id: int
    message: str
    images: list[str] | None = None
    is_regenerate: bool = False
    intent: str = "general"


class Citation(BaseModel):
    document_title: str
    chunk_index: int
    similarity: float


class ChatResponse(BaseModel):
    response: str
    citations: list[Citation] = []
    metadata: dict | None = None