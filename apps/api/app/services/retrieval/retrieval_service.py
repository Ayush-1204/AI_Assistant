from __future__ import annotations

import logging

from app.config import settings
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.services.ai.embeddings.embedding_service import EmbeddingService
from app.services.retrieval.models import RetrievalResult

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service responsible for semantic retrieval.

    Responsibilities:
    - Generate query embeddings
    - Execute semantic search
    - Apply similarity threshold
    - Convert repository results into RetrievalResult
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        chunk_repository: DocumentChunkRepository,
    ):
        self.embedding_service = embedding_service
        self.chunk_repository = chunk_repository
        self.default_top_k = settings.rag_top_k
        self.default_similarity_threshold = (
            settings.rag_similarity_threshold
        )

    async def retrieve(
        self,
        *,
        query: str,
        user_id: int,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve the most relevant document chunks.

        Parameters
        ----------
        query
            User query.

        user_id
            Owner of the documents.

        top_k
            Number of chunks to retrieve before filtering.

        similarity_threshold
            Maximum cosine distance allowed.

        Returns
        -------
        list[RetrievalResult]
        """

        resolved_top_k = (
            self.default_top_k if top_k is None else top_k
        )

        resolved_similarity_threshold = (
            self.default_similarity_threshold
            if similarity_threshold is None
            else similarity_threshold
        )

        embedding = await self.embedding_service.embed_query(
            query,
        )

        rows = await self.chunk_repository.semantic_search(
            embedding=embedding,
            user_id=user_id,
            top_k=resolved_top_k,
        )

        retrieval_results: list[RetrievalResult] = []

        for result in rows:

            if result.distance > resolved_similarity_threshold:
                continue

            retrieval_results.append(
                RetrievalResult(
                    chunk=result.chunk,
                    distance=float(result.distance),
                )
            )

        retrieval_results.sort(key=lambda result: result.distance)

        logger.info(
            "Semantic retrieval complete.",
            extra={
                "query": query,
                "retrieved": len(rows),
                "accepted": len(retrieval_results),
                "threshold": resolved_similarity_threshold,
                "best_distance": (
                    retrieval_results[0].distance
                    if retrieval_results
                    else None
                ),
            },
        )

        return retrieval_results