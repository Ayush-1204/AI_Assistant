from .base_tts import BaseTTSProvider
from typing import AsyncGenerator

class GeminiTTSProvider(BaseTTSProvider):
    """
    Stubbed Gemini TTS Provider.
    """

    async def start_session(self) -> None:
        pass

    async def process_text(self, text_chunk: str) -> None:
        pass

    async def stream_audio(self) -> AsyncGenerator[bytes, None]:
        yield b""

    async def stop_generation(self) -> None:
        pass

    async def flush(self) -> None:
        pass

    async def end_session(self) -> None:
        pass
