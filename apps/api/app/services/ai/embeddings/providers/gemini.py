from google import genai

from app.config import get_settings

from .base import BaseEmbeddingProvider


settings = get_settings()


class GeminiEmbeddingProvider(
    BaseEmbeddingProvider,
):

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

        self.model = (
            "gemini-embedding-001"
        )

    async def embed(
        self,
        text: str,
    ) -> list[float]:

        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
        )

        return response.embeddings[0].values