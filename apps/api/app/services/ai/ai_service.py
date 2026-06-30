from app.services.ai.providers.base import BaseLLMProvider


class AIService:
    def __init__(
        self,
        provider: BaseLLMProvider,
    ):
        self.provider = provider

    async def chat(
        self,
        prompt: str,
    ) -> str:

        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        return await self.provider.generate(messages)