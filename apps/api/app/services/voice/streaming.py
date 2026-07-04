import asyncio
import logging
import json
from fastapi import WebSocket, WebSocketDisconnect

from app.services.ai.planner.planner import Planner
from app.services.ai.planner.executor import AgentExecutor
from app.services.voice.session import VoiceSession, StreamingState
from app.services.voice.providers.base_stt import BaseSTTProvider
from app.services.voice.providers.base_tts import BaseTTSProvider

logger = logging.getLogger(__name__)

class StreamingCoordinator:
    def __init__(
        self,
        session: VoiceSession,
        stt_provider: BaseSTTProvider,
        tts_provider: BaseTTSProvider,
        planner: Planner,
        agent_executor: AgentExecutor,
        context_builder,
        websocket: WebSocket
    ):
        self.session = session
        self.stt = stt_provider
        self.tts = tts_provider
        self.planner = planner
        self.agent = agent_executor
        self.context_builder = context_builder
        self.websocket = websocket
        
        self.active_generation_task: asyncio.Task | None = None
        self.stt_task: asyncio.Task | None = None
        self.tts_audio_task: asyncio.Task | None = None

    async def start(self) -> None:
        await self.websocket.accept()
        await self.stt.start_session()
        await self.tts.start_session()
        
        self.stt_task = asyncio.create_task(self._listen_for_transcripts())
        self.tts_audio_task = asyncio.create_task(self._stream_tts_audio_back())
        
        try:
            while True:
                # Safely parse incoming payload, ignoring text if frontend sends pings
                message = await self.websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
                if "bytes" in message:
                    await self.stt.process_audio(message["bytes"])
        except WebSocketDisconnect:
            pass
        finally:
            await self._cleanup()

    async def _listen_for_transcripts(self) -> None:
        async for transcript in self.stt.stream_transcripts():
            if transcript.strip():
                # Barge-in detected
                if self.session.streaming_state == StreamingState.SPEAKING:
                    self.session.barge_in()
                    await self.tts.stop_generation()
                    if self.active_generation_task and not self.active_generation_task.done():
                        self.active_generation_task.cancel()
                    logger.info("[Voice] Interruption detected! Barge-in triggered.")
                
                # Execute agent on transcript aggregation.
                # In real scenario, STT provides an 'is_final' flag, assuming final here.
                self.session.partial_transcript += transcript + " "
                
                if self.active_generation_task is None or self.active_generation_task.done():
                    self.active_generation_task = asyncio.create_task(
                        self._trigger_agent_and_tts(self.session.partial_transcript)
                    )
                    self.session.partial_transcript = ""

    async def _trigger_agent_and_tts(self, user_text: str) -> None:
        self.session.ai_starts_speaking()
        
        messages, _ = await self.context_builder.build(
            user_id=self.session.user_id, 
            conversation_id=self.session.conversation_id, 
            query=user_text
        )
        context = {"user_id": self.session.user_id, "conversation_id": self.session.conversation_id}
        tools_payload = self.agent.strategy.get_tools_for_provider()
        
        try:
            # We use stream_run to get text tokens real-time and push them to TTS
            async for chunk in self.agent.stream_run(user_text, context, messages, tools_payload):
                if chunk.startswith("data: ") and '"delta"' in chunk:
                    delta_data = json.loads(chunk[6:])
                    if 'delta' in delta_data:
                        await self.tts.process_text(delta_data['delta'])
            
            # Flush TTS processing
            await self.tts.flush()
        except asyncio.CancelledError:
            logger.info("[Voice] LLM generation cancelled via interruption.")

    async def _stream_tts_audio_back(self) -> None:
        async for audio_bytes in self.tts.stream_audio():
            if self.session.interruption_state:
                continue # drop audio bytes during interrupt
            try:
                await self.websocket.send_bytes(audio_bytes)
            except WebSocketDisconnect:
                break

    async def _cleanup(self) -> None:
        if self.active_generation_task: self.active_generation_task.cancel()
        if self.stt_task: self.stt_task.cancel()
        if self.tts_audio_task: self.tts_audio_task.cancel()
        await self.stt.end_session()
        await self.tts.end_session()
        logger.info(f"[Voice] session ended for {self.session.session_id}")
