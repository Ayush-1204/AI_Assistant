import asyncio
import json
import io
import logging

import httpx
from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings
from app.dependencies import (
    get_context_builder,
    get_provider_router,
    get_tool_orchestrator,
)
from app.services.ai.planner.executor import AgentExecutor
from app.services.ai.planner.planner import Planner
from app.services.ai.tools.strategies import NativeFunctionStrategy
from app.services.voice.providers.groq_tts_provider import GroqTTSProvider
from app.services.voice.providers.whisper_provider import WhisperProvider
from app.services.voice.session import VoiceSession
from app.services.voice.streaming import StreamingCoordinator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["Voice"])


def _resolve_user_id_from_token(token: str | None) -> int:
    """Decode JWT token and return user_id, or fall back to 1 for dev."""
    if not token:
        return 1
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return int(payload.get("sub", 1))
    except (JWTError, ValueError):
        return 1


class TTSRequest(BaseModel):
    text: str


@router.post("/tts")
async def tts_endpoint(request: TTSRequest):
    """
    Multi-tiered Fallback TTS Orchestrator:
    Priority: Deepgram -> ElevenLabs -> Edge TTS
    """
    audio_bytes = None
    target_text = request.text
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. DEEPGRAM (aura-2-thalia-en)
        if settings.DEEPGRAM_API_KEY:
            try:
                logger.info(f"[TTS Orchestrator] Attempting Deepgram TTS for: '{target_text[:30]}...'")
                url = "https://api.deepgram.com/v1/speak?model=aura-2-thalia-en&encoding=linear16&sample_rate=16000"
                resp = await client.post(
                    url,
                    headers={
                        "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={"text": target_text}
                )
                resp.raise_for_status()
                audio_bytes = resp.content
                logger.info("[TTS Orchestrator] Deepgram complete.")
            except Exception as e:
                logger.warning(f"[TTS Orchestrator] Deepgram failed: {e}. Falling back to ElevenLabs.")
        
        # 2. ELEVENLABS (eleven_flash_v2_5, Anika)
        if not audio_bytes and settings.ELEVENLABS_API_KEY:
            try:
                logger.info(f"[TTS Orchestrator] Attempting ElevenLabs TTS for: '{target_text[:30]}...'")
                # Using Anika's general voice fallback or a standard id
                voice_id = "piTKgcLEGmPE4e6mJC13"  
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=pcm_16000"
                resp = await client.post(
                    url,
                    headers={
                        "xi-api-key": settings.ELEVENLABS_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": target_text,
                        "model_id": "eleven_flash_v2_5"
                    }
                )
                resp.raise_for_status()
                audio_bytes = resp.content
                logger.info("[TTS Orchestrator] ElevenLabs complete.")
            except Exception as e:
                logger.warning(f"[TTS Orchestrator] ElevenLabs failed: {e}. Falling back to Edge TTS.")
                
        # 3. GROQ (canopylabs/orpheus-v1-english)
        if not audio_bytes and settings.GROQ_API_KEY:
            try:
                logger.info(f"[TTS Orchestrator] Attempting Groq TTS (Orpheus) for: '{target_text[:30]}...'")
                url = "https://api.groq.com/openai/v1/audio/speech"
                resp = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "canopylabs/orpheus-v1-english",
                        "voice": "diana",
                        "input": target_text,
                        "response_format": "wav"
                    }
                )
                resp.raise_for_status()
                audio_bytes = resp.content
                logger.info("[TTS Orchestrator] Groq (Orpheus) complete.")
            except Exception as e:
                logger.warning(f"[TTS Orchestrator] Groq TTS failed: {e}. Falling back to Edge TTS.")
                
        # 4. EDGE TTS (Fallback Native Free)
        if not audio_bytes:
            try:
                logger.info(f"[TTS Orchestrator] Attempting Edge TTS fallback for: '{target_text[:30]}...'")
                import edge_tts
                communicate = edge_tts.Communicate(target_text, "en-US-AriaNeural")
                chunks = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        chunks.append(chunk["data"])
                audio_bytes = b"".join(chunks)
                logger.info("[TTS Orchestrator] Edge TTS complete.")
            except Exception as e:
                logger.error(f"[TTS Orchestrator] Edge TTS failed: {e}")
                return Response(status_code=500, content="All TTS Providers Failed.")

    # Apply PyDub +12dB volume gain natively 
    if audio_bytes and audio_bytes.startswith(b"RIFF"):
        try:
            from pydub import AudioSegment
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="raw" if "pcm" in str(audio_bytes[:10]) else "wav")
            louder_audio = audio_segment + 12.0  # Boost volume by 12 dB
            out_f = io.BytesIO()
            louder_audio.export(out_f, format="wav")
            audio_bytes = out_f.getvalue()
        except Exception as e:
            logger.error(f"Failed to amplify TTS volume natively: {e}")
            
    return Response(content=audio_bytes, media_type="audio/wav")


@router.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    bytes_data = await file.read()
    stt = WhisperProvider()

    # Direct file transcription bypasses the buffered queue
    transcript = await stt.transcribe_file(bytes_data)

    return {"text": transcript}


@router.websocket("/dictate")
async def dictate_websocket(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    user_id = _resolve_user_id_from_token(token)
    logger.debug(f"[Dictate WS] user_id={user_id}")
    await websocket.accept()
    stt = WhisperProvider()
    await stt.start_session()

    # Text accumulator
    state = {"text": ""}

    async def flush_stt():
        async for transcript in stt.stream_transcripts():
            if transcript.strip():
                state["text"] += transcript + " "
                try:
                    await websocket.send_text(json.dumps({
                        "type": "stt",
                        "text": state["text"],
                    }))
                except Exception:
                    break

    sender = asyncio.create_task(flush_stt())

    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            if "bytes" in message:
                await stt.process_audio(message["bytes"])
    except WebSocketDisconnect:
        pass
    finally:
        sender.cancel()
        await stt.end_session()


@router.websocket("/{conversation_id}")
async def voice_websocket(
    websocket: WebSocket,
    conversation_id: int,
    token: str | None = Query(default=None),
    provider_router=Depends(get_provider_router),
    context_builder=Depends(get_context_builder),
    tool_orchestrator=Depends(get_tool_orchestrator),
):
    user_id = _resolve_user_id_from_token(token)
    logger.debug(f"[Voice WS] conversation_id={conversation_id} user_id={user_id}")

    strategy = NativeFunctionStrategy(tool_orchestrator.registry)
    planner = Planner(provider_router, strategy)
    agent = AgentExecutor(planner, tool_orchestrator, strategy)

    session = VoiceSession(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    stt = WhisperProvider()
    
    # Priority TTS Orchestration for Live WebSockets
    if settings.DEEPGRAM_API_KEY:
        from app.services.voice.providers.deepgram_tts_provider import DeepgramTTSProvider
        tts = DeepgramTTSProvider()
    elif settings.ELEVENLABS_API_KEY:
        from app.services.voice.providers.elevenlabs_tts_provider import ElevenLabsTTSProvider
        tts = ElevenLabsTTSProvider()
    elif settings.GROQ_API_KEY:
        from app.services.voice.providers.groq_tts_provider import GroqTTSProvider
        tts = GroqTTSProvider(voice="diana")
    else:
        from app.services.voice.providers.edge_tts_provider import EdgeTTSProvider
        tts = EdgeTTSProvider()

    coordinator = StreamingCoordinator(
        session=session,
        stt_provider=stt,
        tts_provider=tts,
        planner=planner,
        agent_executor=agent,
        context_builder=context_builder,
        websocket=websocket,
    )

    await coordinator.start()

