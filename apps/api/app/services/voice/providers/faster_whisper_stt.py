import logging

from .base_stt import BaseSTTProvider

logger = logging.getLogger(__name__)

class FasterWhisperSTTProvider(BaseSTTProvider):
    """
    Local-first transcribing using `faster-whisper`.
    Runs CTranslate2 highly optimized quantized models directly on CPU/GPU.
    """
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None

    def _load_model(self):
        if self.model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info(f"Loading faster-whisper model '{self.model_size}'...")
                self.model = WhisperModel(self.model_size, device="auto", compute_type="int8")
            except ImportError:
                logger.error("faster-whisper package not installed. Install via pip install faster-whisper.")

    async def transcribe(self, audio_data: bytes) -> str:
        self._load_model()
        if not self.model:
            return ""
            
        import os
        import tempfile
        
        # Buffer to temp file for faster-whisper which prefers file paths or numpy arrays
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
            
        try:
            segments, info = self.model.transcribe(tmp_path, beam_size=5)
            transcript = " ".join([segment.text for segment in segments])
            return transcript.strip()
        except Exception as e:
            logger.error(f"Faster-Whisper error: {str(e)}")
            return ""
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
