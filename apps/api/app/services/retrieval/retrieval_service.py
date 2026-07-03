from __future__ import annotations

import logging
from time import perf_counter

from app.config import settings
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.services.ai.embeddings.embedding_service import EmbeddingService
from app.services.retrieval.models import RetrievalResult
from app.services.retrieval.fusion import ResultFusion
from app.services.retrieval.reranking import Reranker
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
        result_fusion: ResultFusion,
        reranker: Reranker,
    ):
        self.embedding_service = embedding_service
        self.chunk_repository = chunk_repository
        self.result_fusion = result_fusion
        self.reranker = reranker
        self.default_top_k = settings.rag_top_k
        self.default_similarity_threshold = settings.rag_similarity_threshold
        self.allow_best_match_fallback = settings.retrieval_allow_best_match_fallback

    async def retrieve(
        self,
        *,
        query: str,
        user_id: int,
        top_k: int | None = None,
    ) -> list[RetrievalResult]:

        resolved_top_k = self.default_top_k if top_k is None else top_k
        
        dense_results: list[RetrievalResult] = []
        keyword_results: list[RetrievalResult] = []
        
        dense_latency = 0.0
        keyword_latency = 0.0
        
        import asyncio
        retrieval_tasks = []
        
        async def fetch_dense():
            nonlocal dense_latency
            start = perf_counter()
            embedding = await self.embedding_service.embed_query(query)
            target_k = settings.dense_top_k if settings.enable_hybrid_retrieval else resolved_top_k
            rows = await self.chunk_repository.semantic_search(
                query=query, 
                embedding=embedding, 
                user_id=user_id, 
                top_k=target_k
            )
            dense_latency = (perf_counter() - start) * 1000.0
            return [RetrievalResult(chunk=c, distance=float(d)) for c, d in rows]
            
        retrieval_tasks.append(fetch_dense())
        
        async def fetch_keyword():
            nonlocal keyword_latency
            start = perf_counter()
            rows = await self.chunk_repository.keyword_search(
                query=query,
                user_id=user_id,
                top_k=settings.keyword_top_k
            )
            keyword_latency = (perf_counter() - start) * 1000.0
            return [RetrievalResult(chunk=c, keyword_score=float(rank)) for c, rank in rows]
            
        if settings.enable_hybrid_retrieval:
            retrieval_tasks.append(fetch_keyword())
            
        gathered = await asyncio.gather(*retrieval_tasks)
        all_parsed_results = gathered[0]
        
        # Apply strict similarity threshold filtering for dense
        dense_results = [
            result for result in all_parsed_results
            if result.distance is not None and result.distance <= self.default_similarity_threshold
        ]

        if not dense_results and all_parsed_results and self.allow_best_match_fallback:
            dense_results = [all_parsed_results[0]]
            logger.info("Threshold filtering returned 0 results. Fallback strategy triggered returning best match.")
            
        if settings.enable_hybrid_retrieval:
            keyword_results = gathered[1]
            
        # 2. Result Fusion
        fusion_start = perf_counter()
        if settings.enable_hybrid_retrieval:
            fused_candidates = self.result_fusion.fuse(dense_results, keyword_results)
        else:
            dense_results.sort(key=lambda r: r.distance if r.distance is not None else float('inf'))
            fused_candidates = dense_results
            for rank, c in enumerate(fused_candidates):
                c.rrf_score = 1.0 / (rank + 60)
                
        fusion_latency = (perf_counter() - fusion_start) * 1000.0
        
        # 3. Reranking
        reranking_latency = 0.0
        
        if settings.enable_reranking:
            rerank_start = perf_counter()
            candidates_to_rerank = fused_candidates[:settings.reranker_candidate_count]
            final_results = await self.reranker.rerank(
                query=query, 
                candidates=candidates_to_rerank, 
                top_n=settings.reranker_output_count
            )
            reranking_latency = (perf_counter() - rerank_start) * 1000.0
        else:
            final_results = fused_candidates[:resolved_top_k]

        logger.info(
            "Hybrid Retrieval Pipeline complete.",
            extra={
                "query": query,
                "config": {
                    "hybrid_enabled": settings.enable_hybrid_retrieval,
                    "reranking_enabled": settings.enable_reranking,
                    "dense_top_k": settings.dense_top_k,
                    "keyword_top_k": settings.keyword_top_k,
                },
                "metrics_latency_ms": {
                    "dense_ms": round(dense_latency, 2),
                    "keyword_ms": round(keyword_latency, 2),
                    "fusion_ms": round(fusion_latency, 2),
                    "reranking_ms": round(reranking_latency, 2),
                },
                "counts": {
                    "dense_results": len(dense_results),
                    "keyword_results": len(keyword_results),
                    "merged_results": len(fused_candidates),
                    "final_results": len(final_results),
                },
                "final_documents_returned": [
                    document_title(r.chunk.document) for r in final_results
                ],
            },
        )

        return final_results