import logging
from collections.abc import AsyncGenerator

from .base_tts import BaseTTSProvider

logger = logging.getLogger(__name__)

class KokoroTTSProvider(BaseTTSProvider):
    """
    Completely Local Offline TTS based on Kokoro Engine.
    Extremely lightweight ~82M parameters.
    """
    def __init__(self, voice: str = "af"):
        self.voice = voice

    async def generate_audio_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        try:
            import kokoro
        except ImportError:
            logger.error("Kokoro TTS not installed natively. Defaulting to empty byte chunks.")
            yield b""
            return
            
        try:
            # Depending on how the local Kokoro wheel is initialized:
            pipeline = kokoro.KPipeline(lang_code="a") 
            generator = pipeline(text, voice=self.voice, speed=1, split_pattern=r'\n+')
            for i, (gs, ps, audio) in enumerate(generator):
                import io

                import soundfile as sf
                
                wav_io = io.BytesIO()
                sf.write(wav_io, audio, 24000, format='WAV')
                wav_io.seek(0)
                
                # Streaming chunk-by-chunk natively to UI
                yield wav_io.read()
        except Exception as e:
            logger.error(f"Kokoro local TTS failed: {str(e)}")
            yield b""
