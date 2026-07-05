import logging
import asyncio
from typing import AsyncGenerator
from .base_tts import BaseTTSProvider

logger = logging.getLogger(__name__)

class EdgeTTSProvider(BaseTTSProvider):
    """
    Microsoft Edge TTS Provider implementation. (Stubbed behavior matching structure).
    """

    def __init__(self, voice: str = "en-US-AriaNeural"):
        self.voice = voice
        self.is_active = False
        self.text_queue: asyncio.Queue[str] = asyncio.Queue()
        self.audio_queue: asyncio.Queue[bytes] = asyncio.Queue()

    async def start_session(self) -> None:
        self.is_active = True
        logger.info(f"[EdgeTTS] started TTS session with voice {self.voice}.")
        asyncio.create_task(self._synthesis_loop())

    async def _synthesis_loop(self):
        """Mock loop for converting text to audio chunks"""
        while self.is_active:
            try:
                text = await asyncio.wait_for(self.text_queue.get(), timeout=0.1)
                if text == "<FLUSH>":
                    continue
                # In real code: synthesize text and stream back bytes
                await self.audio_queue.put(b"mock_audio_bytes_for: " + text.encode())
            except asyncio.TimeoutError:
                continue

    async def process_text(self, text_chunk: str) -> None:
        if self.is_active:
            await self.text_queue.put(text_chunk)

    async def stream_audio(self) -> AsyncGenerator[bytes, None]:
        while self.is_active:
            try:
                chunk = await asyncio.wait_for(self.audio_queue.get(), timeout=0.1)
                yield chunk
            except asyncio.TimeoutError:
                await asyncio.sleep(0.01)

    async def stop_generation(self) -> None:
        # Clear queues for barge-in
        while not self.text_queue.empty():
            self.text_queue.get_nowait()
        while not self.audio_queue.empty():
            self.audio_queue.get_nowait()
        logger.info("[EdgeTTS] Generation stopped (barge-in).")

    async def flush(self) -> None:
        if self.is_active:
            await self.text_queue.put("<FLUSH>")

    async def end_session(self) -> None:
        self.is_active = False
        await self.stop_generation()
        logger.info("[EdgeTTS] ended TTS session.")
