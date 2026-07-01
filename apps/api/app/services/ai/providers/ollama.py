from collections.abc import AsyncGenerator

import ollama

from app.services.ai.prompts import PromptBuilder
from app.services.ai.providers.base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):

    def __init__(self):

        self.model = "qwen3:8b"

    async def chat(
        self,
        messages: list[dict],
    ) -> str:

        response = ollama.chat(
            model=self.model,
            messages=messages,
        )

        return response["message"]["content"]

    async def stream_chat(
        self,
        messages: list[dict],
    ) -> AsyncGenerator[str, None]:

        stream = ollama.chat(
            model=self.model,
            messages=messages,
            stream=True,
        )

        for chunk in stream:

            yield chunk["message"]["content"]

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