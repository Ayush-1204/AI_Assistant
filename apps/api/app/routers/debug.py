from fastapi import APIRouter, Depends

from app.dependencies import (
    get_current_user,
    get_retrieval_service,
)

from app.services.retrieval.retrieval_service import RetrievalService


def _document_title(document) -> str:
    return (
        getattr(document, "title", None)
        or getattr(document, "original_filename", None)
        or getattr(document, "filename", None)
        or getattr(document, "stored_filename", None)
        or "Untitled Document"
    )

router = APIRouter(
    prefix="/debug",
    tags=["Debug"],
)


@router.post("/search")
async def debug_search(

    query: str,

    current_user=Depends(
        get_current_user,
    ),

    retrieval: RetrievalService = Depends(
        get_retrieval_service,
    ),

):

    chunks = await retrieval.retrieve(
        query=query,
        user_id=current_user.id,
    )

    return [
        {
            "document_title": _document_title(c.chunk.document),
            "chunk_index": c.chunk.chunk_index,
            "token_count": c.chunk.token_count,
            "distance": c.distance,
            "content": c.chunk.content,
        }
        for c in chunks
    ]