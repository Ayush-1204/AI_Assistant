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
    distance: float

    @property
    def similarity(self) -> float:
        return max(
            0.0,
            1.0 - self.distance,
        )