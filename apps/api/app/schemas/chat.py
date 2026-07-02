from pydantic import BaseModel


class ChatRequest(BaseModel):
    conversation_id: int
    message: str


class Citation(BaseModel):
    document_title: str
    chunk_index: int
    similarity: float


class ChatResponse(BaseModel):
    response: str
    citations: list[Citation] = []