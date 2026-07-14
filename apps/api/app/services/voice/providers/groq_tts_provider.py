import asyncio
import logging
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.config import settings

from .base_tts import BaseTTSProvider

logger = logging.getLogger(__name__)

class GroqTTSProvider(BaseTTSProvider):
    def __init__(self, voice: str = "troy"):
        self.voice = voice
        self.is_active = False
        self.text_queue: asyncio.Queue[str] = asyncio.Queue()
        self.audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self.api_key = settings.GROQ_API_KEY
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1"
        )

    async def start_session(self) -> None:
        self.is_active = True
        logger.info(f"[GroqTTS] started TTS session with voice {self.voice}.")
        asyncio.create_task(self._synthesis_loop())

    async def _synthesis_loop(self):
        while self.is_active:
            try:
                # Accumulate a decent chunk before hitting the Groq API since it requires POST
                # We'll batch up to 2 sentences or timeout
                text_buffer = ""
                chunk1 = await asyncio.wait_for(self.text_queue.get(), timeout=0.5)
                
                if chunk1 == "<FLUSH>": continue
                if chunk1.strip(): text_buffer += chunk1 + " "
                
                # try to get more closely bundled text
                try:
                    while len(text_buffer) < 80:
                        chunk2 = await asyncio.wait_for(self.text_queue.get(), timeout=0.5)
                        if chunk2 == "<FLUSH>": break
                        if chunk2.strip(): text_buffer += chunk2 + " "
                except (asyncio.TimeoutError, TimeoutError):
                    pass
                
                # Generate the TTS using Groq OpenAI wrapper
                target_text = text_buffer.strip()
                logger.info(f"[GroqTTS] Generating speech for text chunk: '{target_text}' (model: 'canopylabs/orpheus-v1-english', voice: 'diana')")
                resp = await self.client.audio.speech.create(
                    model="canopylabs/orpheus-v1-english",
                    voice="diana",
                    input=target_text,
                    response_format="wav" 
                )
                
                if self.is_active:
                    await self.audio_queue.put(resp.content)
                    
            except (asyncio.TimeoutError, TimeoutError):
                continue
            except Exception as e:
                logger.error(f"[GroqTTS] synthesis error: {repr(e)}")

    async def process_text(self, text_chunk: str) -> None:
        if self.is_active:
            await self.text_queue.put(text_chunk)

    async def stream_audio(self) -> AsyncGenerator[bytes, None]:
        while self.is_active:
            try:
                chunk = await asyncio.wait_for(self.audio_queue.get(), timeout=0.1)
                if chunk is not None:
                    # Stream chunks dynamically
                    chunk_size = 8192
                    for i in range(0, len(chunk), chunk_size):
                        yield chunk[i:i + chunk_size]
                        await asyncio.sleep(0.01)
            except TimeoutError:
                await asyncio.sleep(0.01)

    async def stop_generation(self) -> None:
        while not self.text_queue.empty():
            self.text_queue.get_nowait()
        while not self.audio_queue.empty():
            self.audio_queue.get_nowait()
        logger.info("[GroqTTS] Generation stopped (barge-in).")

    async def flush(self) -> None:
        if self.is_active:
            await self.text_queue.put("<FLUSH>")

    async def end_session(self) -> None:
        self.is_active = False
        await self.stop_generation()
        logger.info("[GroqTTS] ended TTS session.")
