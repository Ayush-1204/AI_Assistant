import asyncio
import io
import json
import logging
from collections.abc import AsyncGenerator

import httpx

from app.config import settings
from .base_tts import BaseTTSProvider

logger = logging.getLogger(__name__)

class ElevenLabsTTSProvider(BaseTTSProvider):
    # Anika defaults via arbitrary hash if official string name mapping fails
    def __init__(self, model: str = "eleven_flash_v2_5", voice_id_or_name: str = "RABOvaPec1ymXz02oDQi"):
        self.model = model
        # Just use Anika if users provided it conceptually, mapping to a stable ID fallback if unknown
        # Note: ElevenLabs usually uses unique IDs like 'pNInz6obpgDQGcFmaJgB'
        self.voice_id = voice_id_or_name
        self.is_active = False
        self.text_queue: asyncio.Queue[str] = asyncio.Queue()
        self.audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self.api_key = settings.ELEVENLABS_API_KEY

    async def start_session(self) -> None:
        self.is_active = True
        logger.info(f"[ElevenLabsTTS] started session model {self.model} with voice {self.voice_id}.")
        asyncio.create_task(self._synthesis_loop())

    async def _synthesis_loop(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            while self.is_active:
                try:
                    text_buffer = ""
                    chunk1 = await asyncio.wait_for(self.text_queue.get(), timeout=0.5)
                    
                    if chunk1 == "<FLUSH>": continue
                    if chunk1.strip(): text_buffer += chunk1 + " "
                    
                    try:
                        while len(text_buffer) < 80:
                            chunk2 = await asyncio.wait_for(self.text_queue.get(), timeout=0.5)
                            if chunk2 == "<FLUSH>": break
                            if chunk2.strip(): text_buffer += chunk2 + " "
                    except (asyncio.TimeoutError, TimeoutError):
                        pass
                    
                    target_text = text_buffer.strip()
                    if not target_text:
                        continue
                        
                    logger.info(f"[ElevenLabsTTS] Generating speech chunk: '{target_text[:30]}...'")
                    
                    url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}?output_format=pcm_16000"
                    
                    response = await client.post(
                        url,
                        headers={
                            "xi-api-key": self.api_key or "",
                            "Content-Type": "application/json"
                        },
                        json={
                            "text": target_text,
                            "model_id": self.model,
                            "voice_settings": {
                                "stability": 0.5,
                                "similarity_boost": 0.75
                            }
                        }
                    )
                    response.raise_for_status()
                    
                    if self.is_active:
                        await self.audio_queue.put(response.content)
                        
                except (asyncio.TimeoutError, TimeoutError):
                    continue
                except httpx.HTTPError as e:
                    logger.error(f"[ElevenLabsTTS] API error: {repr(e)}")
                except Exception as e:
                    logger.error(f"[ElevenLabsTTS] synthesis error: {repr(e)}")

    async def process_text(self, text_chunk: str) -> None:
        if self.is_active:
            await self.text_queue.put(text_chunk)

    async def stream_audio(self) -> AsyncGenerator[bytes, None]:
        while self.is_active:
            try:
                chunk = await asyncio.wait_for(self.audio_queue.get(), timeout=0.1)
                if chunk is not None:
                    # Stream chunks
                    chunk_size = 8192
                    for i in range(0, len(chunk), chunk_size):
                        yield chunk[i:i + chunk_size]
                        await asyncio.sleep(0.01)
            except (asyncio.TimeoutError, TimeoutError):
                await asyncio.sleep(0.01)

    async def stop_generation(self) -> None:
        while not self.text_queue.empty():
            self.text_queue.get_nowait()
        while not self.audio_queue.empty():
            self.audio_queue.get_nowait()
        logger.info("[ElevenLabsTTS] Generation stopped (barge-in).")

    async def flush(self) -> None:
        if self.is_active:
            await self.text_queue.put("<FLUSH>")

    async def end_session(self) -> None:
        self.is_active = False
        await self.stop_generation()
        logger.info("[ElevenLabsTTS] ended session.")
