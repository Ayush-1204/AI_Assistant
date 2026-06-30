from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class BaseLLMProvider(ABC):

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
    ) -> str:
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict],
    ) -> AsyncGenerator[str, None]:
        pass

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