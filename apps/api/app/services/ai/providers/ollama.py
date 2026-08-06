from collections.abc import AsyncGenerator
from typing import Any

import httpx
import ollama

from app.services.ai.prompts import PromptBuilder
from app.services.ai.providers.base import BaseLLMProvider
from app.services.ai.providers.exceptions import ProviderTransientError
from app.services.ai.providers.metadata import ProviderMetadata


class OllamaProvider(BaseLLMProvider):

    def __init__(self, model_name: str = "qwen3:8b", provider_name: str = "ollama"):
        self.model = model_name
        self.provider_name = provider_name

    @property
    def name(self) -> str:
        return self.provider_name

    async def get_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            supported_models=[self.model],
            context_window=8192,
            supports_streaming=True,
            supports_vision=False,
            supports_native_tools=False,
            supports_parallel_tools=False,
            supports_tool_streaming=False,
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
        tools: list[dict] | None = None,
        intent: str = "general",
    ) -> str:
        try:
            import re
            response = ollama.chat(
                model=self.model,
                messages=messages,
            )
            content = response["message"]["content"]
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            return content
        except Exception as e:
            raise ProviderTransientError(f"Ollama chat error: {str(e)}")

    async def stream_chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        intent: str = "general",
    ) -> AsyncGenerator[Any, None]:
        try:
            stream = ollama.chat(
                model=self.model,
                messages=messages,
                stream=True,
            )

            is_thinking = False
            for chunk in stream:
                text = chunk["message"]["content"]
                
                if "<think>" in text:
                    is_thinking = True
                    parts = text.split("<think>", 1)
                    if parts[0].strip():
                        yield parts[0]
                    text = parts[1] if len(parts) > 1 else ""
                    
                if "</think>" in text:
                    is_thinking = False
                    parts = text.split("</think>", 1)
                    text = parts[1] if len(parts) > 1 else ""
                    
                # In case the model generates thinking tags perfectly delimited, the above works. 
                # If they are chunked partially, Ollama commonly yields them as whole tokens `<think>`.
                if not is_thinking and text:
                    yield text
        except Exception as e:
            raise ProviderTransientError(f"Ollama stream error: {str(e)}")

    async def generate_title(
        self,
        ai_response: str,
    ) -> str:

        prompt = PromptBuilder.title(
            ai_response,
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
