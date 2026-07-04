from .base_stt import BaseSTTProvider
from typing import AsyncGenerator

class GeminiSTTProvider(BaseSTTProvider):
    """
    Stubbed Gemini STT Provider.
    """

    async def start_session(self) -> None:
        pass

    async def process_audio(self, audio_chunk: bytes) -> None:
        pass

    async def stream_transcripts(self) -> AsyncGenerator[str, None]:
        yield ""

    async def end_session(self) -> None:
        pass
