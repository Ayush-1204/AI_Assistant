from collections.abc import AsyncGenerator

import ollama

import httpx
from app.services.ai.prompts import PromptBuilder
from app.services.ai.providers.base import BaseLLMProvider
from app.services.ai.providers.metadata import ProviderMetadata
from app.services.ai.providers.exceptions import ProviderTransientError


class OllamaProvider(BaseLLMProvider):

    def __init__(self):

        self.model = "qwen3:8b"

    @property
    def name(self) -> str:
        return "ollama"

    async def get_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            supported_models=[self.model],
            context_window=8192,
            supports_streaming=True,
            supports_vision=False,
            supports_function_calling=False,
            estimated_cost_tier=1,
            is_local=True,
        )

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get("http://localhost:11434/api/tags", timeout=2.0)
                return res.status_code == 200
        except Exception:
            return False

    async def chat(
        self,
        messages: list[dict],
    ) -> str:

        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
            )
            return response["message"]["content"]
        except Exception as e:
            raise ProviderTransientError(f"Ollama chat error: {str(e)}")

    async def stream_chat(
        self,
        messages: list[dict],
    ) -> AsyncGenerator[str, None]:

        try:
            stream = ollama.chat(
                model=self.model,
                messages=messages,
                stream=True,
            )

            for chunk in stream:

                yield chunk["message"]["content"]
        except Exception as e:
            raise ProviderTransientError(f"Ollama stream error: {str(e)}")

    async def generate_title(
        self,
        first_message: str,
    ) -> str:

        prompt = PromptBuilder.title(
            first_message,
        )

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response["message"]["content"].strip()

    async def extract_memory(
        self,
        message: str,
    ):

        raise NotImplementedError(
            "Will migrate to Instructor later."
        )