from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from app.dependencies import get_current_user
from app.dependencies import get_retrieval_service
from app.schemas.debug import (
    RetrievalDebugResponse,
    RetrievalDebugResult,
)
from app.services.retrieval.retrieval_service import RetrievalService

router = APIRouter(
    prefix="/debug",
    tags=["Debug"],
)


def _document_title(document) -> str:
    return (
        getattr(document, "title", None)
        or getattr(document, "original_filename", None)
        or getattr(document, "filename", None)
        or "Untitled Document"
    )

@router.get(
    "/retrieval",
    response_model=RetrievalDebugResponse,
)
async def retrieval_debug(
    query: str = Query(
        ...,
        min_length=1,
    ),
    top_k: int = Query(
        5,
        ge=1,
        le=20,
    ),
    current_user=Depends(
        get_current_user,
    ),
    retrieval_service: RetrievalService = Depends(
        get_retrieval_service,
    ),
):

    results = await retrieval_service.retrieve(
        query=query,
        user_id=current_user.id,
        top_k=top_k,
    )

    return RetrievalDebugResponse(
        query=query,
        embedding_dimension=768,
        threshold=retrieval_service.default_similarity_threshold,
        retrieved=len(results),
        results=[
            RetrievalDebugResult(
                document_title=_document_title(result.chunk.document),
                chunk_id=result.chunk.id,
                chunk_index=result.chunk.chunk_index,
                token_count=result.chunk.token_count,
                distance=result.distance,
                content=result.chunk.content,
            )
            for result in results
        ],
    )