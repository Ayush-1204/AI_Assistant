from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from app.services.ai.providers.metadata import ProviderMetadata


class BaseLLMProvider(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier representing this provider."""
        pass

    @abstractmethod
    async def get_metadata(self) -> ProviderMetadata:
        """Returns capabilities regarding this provider."""
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """Ping tests resolving API up status natively."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        intent: str = "general",
    ) -> str:
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        intent: str = "general",
    ) -> AsyncGenerator[Any, None]:
        yield ""

    @abstractmethod
    async def generate_title(
        self,
        first_message: str,
    ) -> str:
        pass

    @abstractmethod
    async def extract_memory(
        self,
        message: str,
    ) -> dict | None:
        """
        Return structured memory.

        Returns None if no memory should be stored.
        """
        pass