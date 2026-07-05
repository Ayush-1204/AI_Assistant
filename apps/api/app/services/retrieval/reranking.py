import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any

from app.services.retrieval.models import RetrievalResult

logger = logging.getLogger(__name__)


class Reranker(ABC):
    """
    Abstract interface for re-ranking dense and keyword fusion chunks efficiently.
    """

    @abstractmethod
    async def rerank(
        self, query: str, candidates: list[RetrievalResult], top_n: int
    ) -> list[RetrievalResult]:
        pass


class CrossEncoderReranker(Reranker):
    """
    Evaluates chunk contents against origin queries predicting contextual scores cleanly!
    Lazily imports `sentence_transformers` avoiding Python trace crashes if dependencies aren't built.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-TinyBERT-L-2-v2"):
        self.model_name = model_name
        self.encoder: Optional[Any] = None
        self._initialized = False
        self._disabled = False

    def _lazy_init(self) -> None:
        if self._initialized or self._disabled:
            return

        try:
            from sentence_transformers import CrossEncoder  # type: ignore

            self.encoder = CrossEncoder(self.model_name)
            self._initialized = True
            logger.info("Successfully loaded CrossEncoder %s", self.model_name)
        except ImportError:
            logger.warning(
                "sentence_transformers natively missing! CrossEncoderReranker '%s' gracefully disabled.",
                self.model_name,
            )
            self._disabled = True

    async def rerank(
        self, query: str, candidates: list[RetrievalResult], top_n: int
    ) -> list[RetrievalResult]:
        
        if not candidates:
            return []

        self._lazy_init()

        if self._disabled or self.encoder is None:
            # Native RRF ordering is already applied gracefully fallback to top_n slice
            return candidates[:top_n]

        loop = asyncio.get_event_loop()
        pairs = [[query, c.chunk.content] for c in candidates]

        def _predict() -> Any:
            return self.encoder.predict(pairs)

        scores = await loop.run_in_executor(None, _predict)

        for c, score in zip(candidates, scores):
            c.rerank_score = float(score)

        # Re-sort evaluating precise metrics safely
        candidates.sort(
            key=lambda x: x.rerank_score if x.rerank_score is not None else float("-inf"),
            reverse=True,
        )

        return candidates[:top_n]
