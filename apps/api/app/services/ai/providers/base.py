from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator



class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def generate_title(
        self,
        first_message: str,
    ) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict],
    ) -> AsyncGenerator[str, None]:
        raise NotImplementedError