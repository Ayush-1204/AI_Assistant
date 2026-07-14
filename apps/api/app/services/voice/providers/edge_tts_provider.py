import asyncio
import logging
from collections.abc import AsyncGenerator

import edge_tts

from .base_tts import BaseTTSProvider

logger = logging.getLogger(__name__)

class EdgeTTSProvider(BaseTTSProvider):
    def __init__(self, voice: str = "en-US-AriaNeural"):
        self.voice = voice
        self.is_active = False
        self.text_queue: asyncio.Queue[str] = asyncio.Queue()
        self.audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()

    async def start_session(self) -> None:
        self.is_active = True
        logger.info(f"[EdgeTTS] started TTS session with voice {self.voice}.")
        asyncio.create_task(self._synthesis_loop())

    async def _synthesis_loop(self):
        while self.is_active:
            try:
                text = await asyncio.wait_for(self.text_queue.get(), timeout=0.1)
                if text == "<FLUSH>":
                    continue
                if not text.strip():
                    continue

                communicate = edge_tts.Communicate(text, self.voice)
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio" and self.is_active:
                        await self.audio_queue.put(chunk["data"])
                    
            except (asyncio.TimeoutError, TimeoutError):
                continue
            except Exception as e:
                logger.error(f"[EdgeTTS] synthesis error: {repr(e)}")

    async def process_text(self, text_chunk: str) -> None:
        if self.is_active:
            await self.text_queue.put(text_chunk)

    async def stream_audio(self) -> AsyncGenerator[bytes, None]:
        while self.is_active:
            try:
                chunk = await asyncio.wait_for(self.audio_queue.get(), timeout=0.1)
                if chunk is not None:
                    yield chunk
            except (asyncio.TimeoutError, TimeoutError):
                await asyncio.sleep(0.01)

    async def stop_generation(self) -> None:
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

