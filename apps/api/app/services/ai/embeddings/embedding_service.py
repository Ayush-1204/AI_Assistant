from app.services.ai.embeddings.providers.base import (
    BaseEmbeddingProvider,
)


class EmbeddingService:

    def __init__(
        self,
        provider: BaseEmbeddingProvider,
    ):
        self.provider = provider

    async def embed(
        self,
        text: str,
    ) -> list[float]:

        return await self.provider.embed(
            text,
        )

    async def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        vectors = []

        for text in texts:

            vectors.append(
                await self.embed(text)
            )

        return vectors