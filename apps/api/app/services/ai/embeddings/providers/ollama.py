from ollama import AsyncClient

from .base import BaseEmbeddingProvider


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """
    Ollama embedding provider.

    Default model:
        nomic-embed-text

    Output dimension:
        768
    """

    def __init__(
        self,
        model: str = "nomic-embed-text",
        host: str = "http://localhost:11434",
    ):
        self.model = model
        self.client = AsyncClient(host=host)

    async def embed(
        self,
        text: str,
    ) -> list[float]:

        response = await self.client.embed(
            model=self.model,
            input=text,
        )

        return response.embeddings[0]