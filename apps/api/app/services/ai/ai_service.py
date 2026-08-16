import json
import logging
import typing
from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)

from app.schemas.chat import Citation
from app.schemas.message import MessageCreate, MessageRole
from app.services.ai.context.context_builder import ContextBuilder
from app.services.ai.memory.memory_service import MemoryService
from app.services.ai.planner.agents.deep_research import DeepResearchAgent
from app.services.ai.planner.executor import AgentExecutor
from app.services.ai.planner.planner import Planner
from app.services.ai.providers.base import BaseLLMProvider
from app.services.ai.tools.orchestrator import ToolOrchestrator
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService
from app.db.session import AsyncSessionLocal

class AIService:

    def __init__(
        self,
        provider: BaseLLMProvider,
        message_service: MessageService,
        conversation_service: ConversationService,
        context_builder: ContextBuilder,
        memory_service: MemoryService,
        tool_orchestrator: ToolOrchestrator,
    ):
        self.provider = provider
        self.message_service = message_service
        self.conversation_service = conversation_service
        self.context_builder = context_builder
        self.memory_service = memory_service
        self.tool_orchestrator = tool_orchestrator

    async def _get_strategy(self):
        metadata = await self.provider.get_metadata()
        if metadata.supports_native_tools:
            from app.services.ai.tools.strategies import NativeFunctionStrategy
            return NativeFunctionStrategy(self.tool_orchestrator.registry)
        else:
            from app.services.ai.tools.strategies import XmlFunctionStrategy
            return XmlFunctionStrategy(self.tool_orchestrator.registry)

    async def chat(
        self,
        user_id: int,
        conversation_id: int,
        prompt: str,
        location_lat: float | None = None,
        location_lon: float | None = None,
        is_regenerate: bool = False,
        images: list[str] | None = None,
        intent: str = "general",
        user_name: str | None = None,
    ) -> tuple[str, list[Citation], dict]:

        import time
        start_time = time.perf_counter()

        logger.info(f"[AIService] Non-streaming chat query received: '{prompt}'")
        await self.conversation_service.get_by_id(conversation_id, user_id)
        if is_regenerate:
            await self.message_service.delete_last_n_messages(conversation_id, count=2)
            
        import re
        clean_prompt = re.sub(r"!\[attachment\]\(data:image\/[^;]+;base64,[^\)]+\)", "[Attached Image]", prompt)
            
        await self.message_service.create(conversation_id, MessageCreate(role=MessageRole.USER, content=clean_prompt, images=images))
        await self.memory_service.process_message(user_id=user_id, message=clean_prompt)

        messages, citations = await self.context_builder.build(user_id=user_id, conversation_id=conversation_id, query=prompt, location_lat=location_lat, location_lon=location_lon, user_name=user_name)

        strategy = await self._get_strategy()
        tool_extension = strategy.get_system_prompt_extension()
        if tool_extension and messages and messages[0].get("role") == "system":
            messages[0]["content"] += tool_extension

        context = {"user_id": user_id, "conversation_id": conversation_id, "images": images}
        tools_payload = strategy.get_tools_for_provider()
        
        # Override intent dynamically
        if intent == "general":
            from app.services.ai.intent_classifier import IntentClassifier
            intent = await IntentClassifier().classify(prompt, images=images)
            logger.info(f"[AIService] Analyzed intent: '{intent}'")
            
        logger.info(f"[AIService] Dispatching execution loop with intent: '{intent}'")
        if intent == "VISION" and images:
            import typing
            from app.services.ai.providers.router import ProviderRouter
            router_inst = typing.cast(ProviderRouter, self.provider)
            
            # OPTION B: Inject live image data specifically for the vision path
            if messages and messages[-1].get("role") == "user":
                messages[-1]["images"] = images
                logger.info(f"[AIService] DEBUG VISION: Injected {len(images)} images into live payload.")
            
            final_response = await router_inst.chat(messages, intent="vision")
        elif intent == "deep_research":
            import typing

            from app.services.ai.providers.router import ProviderRouter
            router_inst = typing.cast(ProviderRouter, self.provider)
            agent = DeepResearchAgent(router_inst)
            final_response = await agent.run(prompt, context_messages=messages)
        elif intent == "swarm":
            import typing
            from app.services.ai.providers.router import ProviderRouter
            from app.services.ai.planner.agents.swarm.swarm import SwarmOrchestrator
            from app.services.ai.planner.agents.swarm.agents import router_agent
            
            router_inst = typing.cast(ProviderRouter, self.provider)
            swarm_engine = SwarmOrchestrator(router_inst)
            final_response = await swarm_engine.run(router_agent, messages)
        elif intent == "antigravity":
            from app.services.ai.planner.agents.antigravity import AntigravityAgent
            ag_agent = AntigravityAgent()
            final_response = await ag_agent.run(prompt, images=images, context_messages=messages)
        elif intent == "IMAGE_GENERATION":
            from app.services.ai.tools.image_generation import handle_image_generation
            from app.services.storage_service import StorageService
            
            clean_prompt = prompt.lower()
            for prefix in ["generate an image of", "create a picture of", "draw me a", "picture of", "draw", "edit the attached image", "edit this image"]:
                if prefix in clean_prompt:
                    clean_prompt = clean_prompt.split(prefix, 1)[-1].strip()
                    break
            if clean_prompt.startswith("a "): clean_prompt = clean_prompt[2:]
            
            storage_service = StorageService()
            result = await handle_image_generation(clean_prompt or prompt, user_id, storage_service)
            final_response = json.dumps([result], indent=2)
        else:
            planner = Planner(self.provider, strategy, intent=intent)
            executor = AgentExecutor(planner, self.tool_orchestrator, strategy, intent=intent)
            final_response = await executor.run(prompt, context, messages, tools_payload)

        # Self-Correction Pass (Corrective RAG)
        if final_response and len(citations) > 0 and intent != "deep_research":
            verify_msgs = [
                {"role": "system", "content": "You are a critical RAG verification engine. If the Draft Answer hallucinates facts unsupported by the Context, output the EXACT FULL CORRECTED ANSWER. If it perfectly matches, return 'PASS'."},
                {"role": "user", "content": f"Context: {messages[0].get('content')}\\n\\nDraft Answer: {final_response}"}
            ]
            router_inst = typing.cast(ProviderRouter, self.provider)
            verification = await router_inst.chat(verify_msgs, intent="general")
            if verification.strip().upper() != "PASS":
                final_response = verification

        await self.message_service.create(conversation_id, MessageCreate(role=MessageRole.ASSISTANT, content=final_response))
        
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        metadata = {
            "model_used": f"Provider Router ({intent.upper()})",
            "retrieval_chunks": len(citations),
            "latency_ms": round(latency_ms, 2),
            "memories": getattr(self.context_builder, "last_metadata", {}).get("memories_list", [])
        }
        return final_response, citations, metadata


    async def stream_chat(
        self,
        user_id: int,
        conversation_id: int,
        prompt: str,
        location_lat: float | None = None,
        location_lon: float | None = None,
        is_regenerate: bool = False,
        images: list[str] | None = None,
        intent: str = "general",
        user_name: str | None = None,
        fastapi_request: typing.Any | None = None,
    ) -> typing.AsyncGenerator[str, None]:

        import time
        start_time = time.perf_counter()

        logger.info(f"[AIService] Streaming chat query received: '{prompt}'")
        await self.conversation_service.get_by_id(conversation_id, user_id)
        if is_regenerate:
            await self.message_service.delete_last_n_messages(conversation_id, count=2)
            
        await self.message_service.create(conversation_id, MessageCreate(role=MessageRole.USER, content=prompt, images=images))
        await self.memory_service.process_message(user_id=user_id, message=prompt)

        messages, citations = await self.context_builder.build(user_id=user_id, conversation_id=conversation_id, query=prompt, location_lat=location_lat, location_lon=location_lon, user_name=user_name)

        strategy = await self._get_strategy()
        tool_extension = strategy.get_system_prompt_extension()
        if tool_extension and messages and messages[0].get("role") == "system":
            messages[0]["content"] += tool_extension

        yield f"data: {json.dumps({'type': 'citations', 'citations': [c.model_dump() for c in citations]})}\n\n"

        context = {"user_id": user_id, "conversation_id": conversation_id, "lat": location_lat, "lon": location_lon}
        tools_payload = strategy.get_tools_for_provider()
        
        # Override intent dynamically
        if intent == "general":
            from app.services.ai.intent_classifier import IntentClassifier
            intent = await IntentClassifier().classify(prompt, images=images)
            logger.info(f"[AIService] Analyzed streaming intent: '{intent}'")
        
        logger.info(f"[AIService] Dispatching streaming execution loop with intent: '{intent}'")
        final_response = ""
        
        import asyncio
        try:
            if intent == "VISION" and images:
                import typing
                from app.services.ai.providers.router import ProviderRouter
                router_inst = typing.cast(ProviderRouter, self.provider)
                
                # OPTION B: Inject live image data specifically for the vision path
                if messages and messages[-1].get("role") == "user":
                    messages[-1]["images"] = images
                    logger.info(f"[AIService] DEBUG VISION: Injected {len(images)} images into live payload.")
                
                yield f"data: {json.dumps({'type': 'tool', 'name': 'Analyzing Image...'})}\n\n"
                async for chunk in router_inst.stream_chat(messages, intent="vision"):
                    if isinstance(chunk, str):
                        payload = json.dumps({"type": "content", "delta": chunk})
                        yield f"data: {payload}\n\n"
                        final_response += chunk
                yield f"data: {json.dumps({'type': 'tool', 'name': 'Image Analysis completed.'})}\n\n"
            elif intent == "deep_research":
                import typing
    
                from app.services.ai.providers.router import ProviderRouter
                router_inst = typing.cast(ProviderRouter, self.provider)
                agent = DeepResearchAgent(router_inst)
                
                yield f"data: {json.dumps({'type': 'tool', 'name': 'Initiating Multi-Hop Tavily Research...'})}\n\n"
                final_response = await agent.run(prompt)
                yield f"data: {json.dumps({'type': 'content', 'delta': final_response})}\n\n"
                yield f"data: {json.dumps({'type': 'tool', 'name': 'Research completed.'})}\n\n"
            elif intent == "swarm":
                import typing
                from app.services.ai.providers.router import ProviderRouter
                from app.services.ai.planner.agents.swarm.swarm import SwarmOrchestrator
                from app.services.ai.planner.agents.swarm.agents import router_agent
                
                router_inst = typing.cast(ProviderRouter, self.provider)
                swarm_engine = SwarmOrchestrator(router_inst)
                
                yield f"data: {json.dumps({'type': 'tool', 'name': 'Spinning up Multi-Agent Swarm (Router, Coder, Reviewer)'})}\n\n"
                final_response = await swarm_engine.run(router_agent, messages)
                yield f"data: {json.dumps({'type': 'content', 'delta': final_response})}\n\n"
                yield f"data: {json.dumps({'type': 'tool', 'name': 'Swarm execution converged successfully.'})}\n\n"
            elif intent == "antigravity":
                from app.services.ai.planner.agents.antigravity import AntigravityAgent
                ag_agent = AntigravityAgent()
                async for chunk in ag_agent.stream_run(prompt, images=images, context_messages=messages):
                    if chunk.startswith("data: ") and '"delta"' in chunk:
                        try:
                            delta = json.loads(chunk[6:])['delta']
                            final_response += delta
                        except:
                            pass
                    yield chunk
            elif intent == "IMAGE_GENERATION":
                from app.services.ai.tools.image_generation import handle_image_generation
                from app.services.storage_service import StorageService
                
                clean_prompt = prompt.lower()
                for prefix in ["generate an image of", "create a picture of", "draw me a", "picture of", "draw", "edit the attached image", "edit this image"]:
                    if prefix in clean_prompt:
                        clean_prompt = clean_prompt.split(prefix, 1)[-1].strip()
                        break
                if clean_prompt.startswith("a "): clean_prompt = clean_prompt[2:]
                
                yield f"data: {json.dumps({'type': 'tool', 'name': 'Generating image with Pollinations.ai...'})}\n\n"
                storage_service = StorageService()
                result = await handle_image_generation(clean_prompt or prompt, user_id, storage_service)
                final_response = json.dumps(result)
                payload = {
                    "type": "presentation_node",
                    "node": result
                }
                yield f"data: {json.dumps(payload)}\n\n"
                yield f"data: {json.dumps({'type': 'tool', 'name': 'Image generated successfully.'})}\n\n"
            else:
                planner = Planner(self.provider, strategy, intent=intent)
                executor = AgentExecutor(planner, self.tool_orchestrator, strategy, intent=intent)
                
                async for chunk in executor.stream_run(prompt, context, messages, tools_payload, fastapi_request=fastapi_request):
                    if fastapi_request and await fastapi_request.is_disconnected():
                        raise asyncio.CancelledError("Client disconnected")
                    
                    if chunk.startswith("data: "):
                        try:
                            data_payload = json.loads(chunk[6:])
                            if data_payload.get("type") == "content":
                                final_response += data_payload.get("delta", "")
                            elif data_payload.get("type") == "presentation_node":
                                # Accumulate JSON lines as the final text
                                final_response += json.dumps(data_payload["node"]) + "\n"
                        except Exception as parse_e:
                            pass
                    yield chunk
                    
        except asyncio.CancelledError:
            logger.warning("[AIService] Client aborted stream manually. Synchronizing partial response to memory.")
            
        finally:
            if final_response:
                try:
                    async with AsyncSessionLocal() as fresh_db:
                        from app.repositories import MessageRepository, ConversationRepository
                        fresh_msg_svc = MessageService(
                            message_repository=MessageRepository(fresh_db),
                            conversation_repository=ConversationRepository(fresh_db)
                        )
                        await fresh_msg_svc.create(conversation_id, MessageCreate(role=MessageRole.ASSISTANT, content=final_response))
                except Exception as e:
                    logger.error(f"[AIService] Failed to save assistant message during teardown: {e}")
            
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            metadata_dump = {
                "type": "metadata",
                "model_used": f"Provider Router ({intent.upper()})",
                "retrieval_chunks": len(citations),
                "latency_ms": round(latency_ms, 2),
                "memories": getattr(self.context_builder, "last_metadata", {}).get("memories_list", [])
            }
            try:
                yield f"data: {json.dumps(metadata_dump)}\n\n"
                yield "data: [DONE]\n\n"
            except asyncio.CancelledError:
                pass