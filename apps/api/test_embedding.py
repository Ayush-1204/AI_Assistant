import asyncio

from app.services.ai.embeddings import (
    EmbeddingService,
)

from app.services.ai.embeddings.providers import (
    GeminiEmbeddingProvider,
)


async def main():

    service = EmbeddingService(
        GeminiEmbeddingProvider(),
    )

    vector = await service.embed(
        "Artificial Intelligence",
    )

    print(len(vector))

    print(vector[:10])


asyncio.run(main())