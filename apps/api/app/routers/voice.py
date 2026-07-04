from fastapi import APIRouter, WebSocket, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_provider_router,
    get_context_builder,
    get_tool_orchestrator,
    get_db
)
from app.services.ai.planner.planner import Planner
from app.services.ai.planner.executor import AgentExecutor
from app.services.ai.tools.strategies import NativeFunctionStrategy
from app.services.voice.session import VoiceSession
from app.services.voice.streaming import StreamingCoordinator
from app.services.voice.providers.whisper_provider import WhisperProvider
from app.services.voice.providers.edge_tts_provider import EdgeTTSProvider

router = APIRouter(prefix="/voice", tags=["Voice"])

@router.websocket("/{conversation_id}")
async def voice_websocket(
    websocket: WebSocket,
    conversation_id: int,
    provider_router = Depends(get_provider_router),
    context_builder = Depends(get_context_builder),
    tool_orchestrator = Depends(get_tool_orchestrator),
):
    # Strategy determination (Mocking Native strategy for Voice)
    strategy = NativeFunctionStrategy(tool_orchestrator.registry)
    
    planner = Planner(provider_router, strategy)
    agent = AgentExecutor(planner, tool_orchestrator, strategy)
    
    # Simple hardcoded user ID = 1 since WebSockets require query param auth normally
    session = VoiceSession(
        conversation_id=conversation_id,
        user_id=1,
    )
    
    stt = WhisperProvider()
    tts = EdgeTTSProvider()
    
    coordinator = StreamingCoordinator(
        session=session,
        stt_provider=stt,
        tts_provider=tts,
        planner=planner,
        agent_executor=agent,
        context_builder=context_builder,
        websocket=websocket
    )
    
    await coordinator.start()
