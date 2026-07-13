from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class BaseTTSProvider(ABC):
    """Abstract Base Class for Text-to-Speech Providers."""

    @abstractmethod
    async def start_session(self) -> None:
        """Initialize TTS connection/resources."""
        pass

    @abstractmethod
    async def process_text(self, text_chunk: str) -> None:
        """Push a text chunk to synthesize."""
        pass

    @abstractmethod
    async def stream_audio(self) -> AsyncGenerator[bytes, None]:
        """Continually yield raw audio bytes as they are synthesized."""
        yield b""

    @abstractmethod
    async def stop_generation(self) -> None:
        """Immediately stop current TTS generation (e.g. for barge-in)."""
        pass
        
    @abstractmethod
    async def flush(self) -> None:
        """Signal that text pushes are finished for this turn."""
        pass
        
    @abstractmethod
    async def end_session(self) -> None:
        """Clean up resources."""
        pass
