import logging

import httpx

from app.config import settings

from .base_stt import BaseSTTProvider

logger = logging.getLogger(__name__)

class DeepgramSTTProvider(BaseSTTProvider):
    """
    Deepgram Nova API Provider for extremely fast STT generation.
    """
    def __init__(self):
        self.api_key = getattr(settings, "DEEPGRAM_API_KEY", "")
        self.url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true"

    async def transcribe(self, audio_data: bytes) -> str:
        if not self.api_key:
            logger.warning("Deepgram API Key missing, STT aborted.")
            return ""

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "audio/wav"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(self.url, content=audio_data, headers=headers)
                res.raise_for_status()
                data = res.json()
                transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
                return transcript
        except Exception as e:
            logger.error(f"Deepgram HTTP Error: {str(e)}")
            return ""
