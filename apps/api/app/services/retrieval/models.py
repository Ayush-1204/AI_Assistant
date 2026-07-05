from __future__ import annotations

from dataclasses import dataclass

from app.db.models import DocumentChunk


@dataclass(slots=True)
class RetrievalResult:
    """
    Internal retrieval result used by RetrievalService.

    This is a service/domain model, not an API schema.
    """

    chunk: DocumentChunk
    distance: float | None = None
    keyword_score: float | None = None
    rrf_score: float = 0.0
    rerank_score: float | None = None

    @property
    def similarity(self) -> float:
        if self.distance is not None:
            return max(
                0.0,
                1.0 - self.distance,
            )
        return 0.0