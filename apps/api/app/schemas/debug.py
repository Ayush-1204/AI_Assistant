from pydantic import BaseModel


class RetrievalDebugResult(BaseModel):
    document_title: str
    chunk_id: int
    chunk_index: int
    token_count: int
    distance: float
    content: str


class RetrievalDebugResponse(BaseModel):
    query: str
    embedding_dimension: int
    threshold: float
    retrieved: int
    results: list[RetrievalDebugResult]