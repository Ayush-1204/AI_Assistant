import base64
import json
import logging
from collections.abc import AsyncGenerator

import websockets

from app.config import settings

from .base_tts import BaseTTSProvider

logger = logging.getLogger(__name__)

class CartesiaTTSProvider(BaseTTSProvider):
    """
    Sub-100ms Ultra-Low Latency TTS utilizing Cartesia's Sonic streaming WebSocket array.
    """
    
    def __init__(self, api_key: str = None, voice_id: str = "694f9389-aac1-45b6-b726-9d9369183238"):
        self.api_key = api_key or getattr(settings, "CARTESIA_API_KEY", "")
        self.voice_id = voice_id
        # Cartesia WebSocket URL
        self.ws_url = "wss://api.cartesia.ai/tts/websocket"

    async def generate_audio_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        if not self.api_key:
            logger.error("Cartesia API Key missing.")
            yield b""
            return
            
        try:
            async with websockets.connect(f"{self.ws_url}?api_key={self.api_key}&cartesia_version=2024-06-10") as websocket:
                request = {
                    "model_id": "sonic-english",
                    "transcript": text,
                    "voice": {
                        "mode": "id",
                        "id": self.voice_id
                    },
                    "output_format": {
                        "container": "wav",
                        "encoding": "pcm_f32le",
                        "sample_rate": 24000
                    }
                }
                
                await websocket.send(json.dumps(request))
                
                async for message in websocket:
                    response = json.loads(message)
                    if response.get("done"):
                        break
                    
                    if "data" in response:
                        chunk = base64.b64decode(response["data"])
                        yield chunk
                        
        except Exception as e:
            logger.error(f"Cartesia TTS failed: {str(e)}")
            yield b""
