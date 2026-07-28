import asyncio
import json
import logging
import random

from fastapi import WebSocket, WebSocketDisconnect

from app.services.ai.planner.executor import AgentExecutor
from app.services.ai.planner.planner import Planner
from app.services.voice.providers.base_stt import BaseSTTProvider
from app.services.voice.providers.base_tts import BaseTTSProvider
from app.services.voice.session import StreamingState, VoiceSession

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
                self.session.partial_transcript += transcript + " "
                
                # Instantly transmit phrase chunks down to the frontend for Real-Time UI display
                try:
                    await self.websocket.send_text(json.dumps({
                        "type": "stt",
                        "text": self.session.partial_transcript
                    }))
                except Exception as e:
                    logger.warning(f"[Voice] failed to stream text: {e}")
                
                if self.active_generation_task is None or self.active_generation_task.done():
                    logger.info(f"[Voice Streaming] User phrase breakpoint reached. Dispatching to agent: '{self.session.partial_transcript.strip()}'")
                    self.active_generation_task = asyncio.create_task(
                        self._trigger_agent_and_tts(self.session.partial_transcript)
                    )
                    self.session.partial_transcript = ""

    async def _trigger_agent_and_tts(self, user_text: str) -> None:
        self.session.ai_starts_speaking()
        try:
            await self.websocket.send_text(json.dumps({
                "type": "stt_agent_clear",
                "text": "AI: "
            }))
        except:
            pass
        
        # Fast Brain Preemptive Audio Injection
        # We instantly fill the async WebSockets channel with TTS bytes to drop Time-To-First-Audio to ~0ms.
        # This completely masks the ~3-5 seconds of RAG and DB operations.
        conversational_fillers = [
            "Let me check on that...",
            "Hmm, let me see...",
            "One moment...",
            "Looking into it...",
            "Give me a second...",
        ]
        filler_task = asyncio.create_task(
            self.tts.process_text(random.choice(conversational_fillers))
        )
        
        messages, _ = await self.context_builder.build(
            user_id=self.session.user_id, 
            conversation_id=self.session.conversation_id, 
            query=user_text
        )
        context = {"user_id": self.session.user_id, "conversation_id": self.session.conversation_id}
        tools_payload = self.agent.strategy.get_tools_for_provider()
        
        try:
            logger.info("[Voice Streaming] Invoking LLM Agent via streaming router for live text token derivation...")
            # We use stream_run to get text tokens real-time and push them to TTS
            sentence_buffer = ""
            async for chunk in self.agent.stream_run(user_text, context, messages, tools_payload):
                if chunk.startswith("data: ") and '"delta"' in chunk:
                    delta_data = json.loads(chunk[6:])
                    if 'delta' in delta_data:
                        text_tok = delta_data['delta']
                        sentence_buffer += text_tok
                        
                        try:
                            await self.websocket.send_text(json.dumps({
                                "type": "stt_agent",
                                "text": text_tok
                            }))
                        except:
                            pass
                            
                        # Flush when we hit boundary punctuation to ensure smooth sentence synthesis
                        if sentence_buffer.endswith((".", "!", "?", "\n")) and len(sentence_buffer) > 15:
                            await self.tts.process_text(sentence_buffer)
                            sentence_buffer = ""
                elif chunk.startswith("data: ") and '"presentation_node"' in chunk:
                    try:
                        p_data = json.loads(chunk[6:])
                        if p_data.get("type") == "presentation_node":
                            node = p_data.get("node", {})
                            node_type = node.get("type")
                            if node_type in ["Heading", "Paragraph", "Math", "Code", "Markdown"]:
                                node_text = node.get("text", "")
                                if node_text:
                                    sentence_buffer += node_text + " "
                                    if sentence_buffer.strip().endswith((".", "!", "?", "\n")) and len(sentence_buffer) > 15:
                                        await self.tts.process_text(sentence_buffer)
                                        sentence_buffer = ""
                            elif node_type == "Timeline":
                                events = node.get("events", [])
                                node_text = " ".join([f"{e.get('time', '')}. {e.get('title', '')}. {e.get('description', '')}" for e in events])
                                if node_text:
                                    sentence_buffer += node_text + " "
                                    if sentence_buffer.strip().endswith((".", "!", "?", "\n")) and len(sentence_buffer) > 15:
                                        await self.tts.process_text(sentence_buffer)
                                        sentence_buffer = ""
                            elif node_type == "Accordion":
                                node_text = f"{node.get('title', '')}. {node.get('content', '')}"
                                if node_text:
                                    sentence_buffer += node_text + " "
                                    if sentence_buffer.strip().endswith((".", "!", "?", "\n")) and len(sentence_buffer) > 15:
                                        await self.tts.process_text(sentence_buffer)
                                        sentence_buffer = ""
                    except Exception as e:
                        logger.warning(f"[Voice] Error parsing presentation node for TTS: {e}")
            
            # Flush any remaining buffer
            if sentence_buffer:
                await self.tts.process_text(sentence_buffer)
                
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
