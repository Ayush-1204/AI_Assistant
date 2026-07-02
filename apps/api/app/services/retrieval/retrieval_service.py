from __future__ import annotations

import logging
from time import perf_counter

from app.config import settings
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.services.ai.embeddings.embedding_service import EmbeddingService
from app.services.retrieval.models import RetrievalResult
from app.services.retrieval.ranking import document_title

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
        self.allow_best_match_fallback = (
            settings.retrieval_allow_best_match_fallback
        )

    async def retrieve(
        self,
        *,
        query: str,
        user_id: int,
        top_k: int | None = None,
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

        Returns
        -------
        list[RetrievalResult]
        """

        resolved_top_k = (
            self.default_top_k if top_k is None else top_k
        )

        query_embedding_started_at = perf_counter()
        embedding = await self.embedding_service.embed_query(
            query,
        )
        query_embedding_latency_ms = (
            perf_counter() - query_embedding_started_at
        ) * 1000.0

        retrieval_started_at = perf_counter()
        rows = await self.chunk_repository.semantic_search(
            query=query,
            embedding=embedding,
            user_id=user_id,
            top_k=resolved_top_k,
        )
        retrieval_latency_ms = (
            perf_counter() - retrieval_started_at
        ) * 1000.0

        all_parsed_results: list[RetrievalResult] = []
        for chunk, distance in rows:
            all_parsed_results.append(
                RetrievalResult(
                    chunk=chunk,
                    distance=float(distance),
                )
            )

        # Sort all results by distance ascending so the best matches are first
        all_parsed_results.sort(key=lambda result: result.distance)

        # Apply strict similarity threshold filtering
        retrieval_results = [
            result for result in all_parsed_results
            if result.distance <= self.default_similarity_threshold
        ]

        fallback_triggered = False

        # Apply best match fallback if active, search found rows, and zero survived threshold filtering
        if not retrieval_results and all_parsed_results and self.allow_best_match_fallback:
            retrieval_results = [all_parsed_results[0]]
            fallback_triggered = True
            logger.info("Threshold filtering returned 0 results. Fallback strategy triggered returning best match.")

        logger.info(
            "Semantic retrieval complete.",
            extra={
                "query": query,
                "top_k_requested": resolved_top_k,
                "results_after_filtering": len(retrieval_results),
                "threshold": self.default_similarity_threshold,
                "fallback_triggered": fallback_triggered,
                "query_embedding_latency_ms": round(
                    query_embedding_latency_ms,
                    2,
                ),
                "retrieval_latency_ms": round(
                    retrieval_latency_ms,
                    2,
                ),
                "distances": [
                    round(result.distance, 6)
                    for result in retrieval_results
                ],
                "documents_returned": [
                    document_title(result.chunk.document)
                    for result in retrieval_results
                ],
                "best_distance": (
                    retrieval_results[0].distance
                    if retrieval_results
                    else None
                ),
            },
        )

        return retrieval_results