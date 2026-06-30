from google import genai

from app.config import get_settings
from app.services.ai.providers.base import BaseLLMProvider

settings = get_settings()


class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

        self.model = settings.GEMINI_MODEL

    async def generate(
        self,
        messages: list[dict],
    ) -> str:

        prompt = "\n".join(
            f"{m['role']}: {m['content']}"
            for m in messages
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        return response.text