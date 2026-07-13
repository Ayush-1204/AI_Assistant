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
    Collect full MP3 audio from Groq and return it as a single buffered response.
    Flutter Web's audioplayers requires the complete bytes blob — streaming chunks
    are not compatible with BytesSource on the web platform.
    """
    chunks: list[bytes] = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream(
            "POST",
            "https://api.groq.com/openai/v1/audio/speech",
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            json={
                "model": "canopylabs/orpheus-v1-english",
                "input": request.text,
                "voice": "diana",
                "response_format": "wav",
            },
        ) as response:
            async for chunk in response.aiter_bytes():
                chunks.append(chunk)

    audio_bytes = b"".join(chunks)
    
    # Do not attempt to amplify if it's an error JSON payload instead of a valid WAV RIFF header
    if audio_bytes.startswith(b"RIFF"):
        try:
            from pydub import AudioSegment
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
            louder_audio = audio_segment + 12.0  # Boost volume by 12 dB
            out_f = io.BytesIO()
            louder_audio.export(out_f, format="wav")
            audio_bytes = out_f.getvalue()
        except Exception as e:
            logger.error(f"Failed to amplify TTS volume natively: {e}")
    else:
        logger.error(f"Groq API returned invalid audio payload: {audio_bytes[:100]}")
        
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
    tts = GroqTTSProvider()

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

