from app.services.ai.providers.base import BaseLLMProvider


class MemoryExtractor:
    """
    Uses the configured LLM provider to extract
    structured memory from user messages.
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
    ):
        self.provider = provider

    async def extract(
        self,
        message: str,
    ) -> dict | None:

        return await self.provider.extract_memory(
            message,
        )