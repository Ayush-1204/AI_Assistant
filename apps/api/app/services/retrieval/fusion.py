from app.services.retrieval.models import RetrievalResult


class ResultFusion:
    """
    Component for merging dense semantic results and keyword search results cleanly.
    
    Responsibilities:
    - Eliminate duplicate chunk items.
    - Blend candidate algorithms natively using Reciprocal Rank Fusion (RRF).
    - Expose unified sorted arrays structurally omitting DB interactions completely.
    """

    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        dense_results: list[RetrievalResult],
        keyword_results: list[RetrievalResult],
    ) -> list[RetrievalResult]:

        dense_ranks = {res.chunk.id: rank for rank, res in enumerate(dense_results)}
        keyword_ranks = {res.chunk.id: rank for rank, res in enumerate(keyword_results)}

        unified_chunks: dict[int, RetrievalResult] = {}

        for res in dense_results + keyword_results:
            chunk_id = res.chunk.id
            if chunk_id not in unified_chunks:
                unified_chunks[chunk_id] = res
            else:
                existing = unified_chunks[chunk_id]
                if res.distance is not None:
                    existing.distance = res.distance
                if res.keyword_score is not None:
                    existing.keyword_score = res.keyword_score

        fused_results = []
        for chunk_id, res in unified_chunks.items():
            dense_score = 0.0
            if chunk_id in dense_ranks:
                dense_score = 1.0 / (dense_ranks[chunk_id] + self.k)

            keyword_score = 0.0
            if chunk_id in keyword_ranks:
                keyword_score = 1.0 / (keyword_ranks[chunk_id] + self.k)

            res.rrf_score = dense_score + keyword_score
            fused_results.append(res)

        fused_results.sort(key=lambda x: x.rrf_score, reverse=True)

        return fused_results
