from abc import ABC, abstractmethod
from typing import AsyncGenerator

class BaseSTTProvider(ABC):
    """Abstract Base Class for Speech-to-Text Providers."""

    @abstractmethod
    async def start_session(self) -> None:
        """Initialize any resources for the STT stream."""
        pass

    @abstractmethod
    async def process_audio(self, audio_chunk: bytes) -> None:
        """Push a raw audio chunk to the STT provider."""
        pass

    @abstractmethod
    async def stream_transcripts(self) -> AsyncGenerator[str, None]:
        """Continually yield full or partial transcripts from the provider."""
        pass

    @abstractmethod
    async def end_session(self) -> None:
        """Clean up resources and finalize."""
        pass
