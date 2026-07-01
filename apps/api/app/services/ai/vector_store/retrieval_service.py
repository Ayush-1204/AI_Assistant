from app.services.ai.embeddings import EmbeddingService
from app.services.ai.vector_store.base import BaseVectorStore


class RetrievalService:

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: BaseVectorStore,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    async def retrieve(
        self,
        *,
        collection: str,
        query: str,
        limit: int = 5,
    ) -> list[dict]:

        vector = await self.embedding_service.embed(
            query,
        )

        return await self.vector_store.search(
            collection=collection,
            vector=vector,
            limit=limit,
        )