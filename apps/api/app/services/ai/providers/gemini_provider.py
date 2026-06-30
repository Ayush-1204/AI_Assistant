from collections.abc import AsyncGenerator

from google import genai

from app.config import get_settings
from app.services.ai.prompts import PromptBuilder
from app.services.ai.providers.base import BaseLLMProvider

settings = get_settings()


class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

        self.model = settings.GEMINI_MODEL

    async def chat(
        self,
        messages: list[dict],
    ) -> str:

        prompt = PromptBuilder.chat(messages)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        return response.text

    async def generate_title(
        self,
        first_message: str,
    ) -> str:

        prompt = PromptBuilder.title(
            first_message,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        return response.text.strip()

    async def stream_chat(
        self,
        messages: list[dict],
    ) -> AsyncGenerator[str, None]:
        raise NotImplementedError