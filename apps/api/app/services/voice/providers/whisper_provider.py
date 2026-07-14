import asyncio
import io
import logging
import wave
from collections.abc import AsyncGenerator

from groq import AsyncGroq

from app.config import settings

from .base_stt import BaseSTTProvider

logger = logging.getLogger(__name__)

class WhisperProvider(BaseSTTProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.is_active = False
        self._queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._transcript_queue: asyncio.Queue[str] = asyncio.Queue()
        
        self.client = AsyncGroq(
            api_key=self.api_key,
        )

    def _create_wav_buffer(self, pcm_data: bytes, sample_rate: int = 48000, channels: int = 1, sample_width: int = 2) -> io.BytesIO:
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)
        wav_io.seek(0)
        wav_io.name = "audio.wav"
        return wav_io

    async def start_session(self) -> None:
        self.is_active = True
        logger.info("[WhisperProvider] started STT session mapped to Groq.")
        asyncio.create_task(self._process_loop())

    async def _process_loop(self):
        while self.is_active:
            try:
                # Buffer incoming chunks for some duration or until an accumulation marker
                audio_buffer = bytearray()
                first_chunk = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                audio_buffer.extend(first_chunk)
                
                # Consume remaining rapid stream events within a short silence window
                while True:
                    try:
                        chunk = await asyncio.wait_for(self._queue.get(), timeout=0.5)
                        audio_buffer.extend(chunk)
                    except (asyncio.TimeoutError, TimeoutError):
                        break # End of this audio phrase
                if len(audio_buffer) < 48000:
                    continue # Drop sub-1sec audio phrases (pure noise) to prevent Whisper hallucinations
                    
                logger.info(f"[WhisperProvider] Submitting audio chunk ({len(audio_buffer)} bytes) to 'whisper-large-v3-turbo'...")
                file_io = self._create_wav_buffer(bytes(audio_buffer), sample_rate=48000)
                res = await self.client.audio.transcriptions.create(
                    file=("audio.wav", file_io.read()),
                    model="whisper-large-v3-turbo",
                    temperature=0.16,
                    language="en",
                    response_format="verbose_json"
                )
                
                transcript_text = ""
                if hasattr(res, "text"): transcript_text = res.text
                elif isinstance(res, dict) and res.get("text"): transcript_text = res["text"]
                elif isinstance(res, str): transcript_text = res
                
                if transcript_text.strip():
                    logger.info(f"[WhisperProvider] Transcribed text: '{transcript_text.strip()}'")
                    await self._transcript_queue.put(transcript_text)
                    
            except (asyncio.TimeoutError, TimeoutError):
                continue
            except Exception as e:
                logger.error(f"[WhisperProvider] failed transcription: {repr(e)}")

    async def process_audio(self, audio_chunk: bytes) -> None:
        if self.is_active:
            await self._queue.put(audio_chunk)

    async def stream_transcripts(self) -> AsyncGenerator[str, None]:
        while self.is_active:
            try:
                transcript = await asyncio.wait_for(self._transcript_queue.get(), timeout=0.1)
                yield transcript
            except (asyncio.TimeoutError, TimeoutError):
                await asyncio.sleep(0.01)

    async def transcribe_file(self, audio_data: bytes) -> str:
        logger.info(f"[WhisperProvider] Direct file transcription requested: {len(audio_data)} bytes using 'whisper-large-v3-turbo'")
        file_io = self._create_wav_buffer(audio_data, sample_rate=48000)
        try:
            res = await self.client.audio.transcriptions.create(
                file=("audio.wav", file_io.read()),
                model="whisper-large-v3-turbo",
                temperature=0.16,
                language="en",
                response_format="verbose_json"
            )
            if hasattr(res, "text"): return res.text
            if isinstance(res, dict) and res.get("text"): return res["text"]
            return res if isinstance(res, str) else str(res)
        except Exception as e:
            logger.error(f"[WhisperProvider] file transcription failed: {repr(e)}")
            return ""

    async def end_session(self) -> None:
        self.is_active = False
        logger.info("[WhisperProvider] ended STT session.")

