from collections.abc import AsyncGenerator
import json

from app.schemas.chat import Citation
from app.schemas.message import MessageCreate
from app.schemas.message import MessageRole
from app.services.ai.context.context_builder import ContextBuilder
from app.services.ai.memory.memory_service import MemoryService
from app.services.ai.providers.base import BaseLLMProvider
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService
from app.services.ai.tools.orchestrator import ToolOrchestrator
from app.services.ai.planner.planner import Planner
from app.services.ai.planner.executor import AgentExecutor

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
    ) -> tuple[str, list[Citation]]:

        await self.conversation_service.get_by_id(conversation_id, user_id)
        await self.message_service.create(conversation_id, MessageCreate(role=MessageRole.USER, content=prompt))
        await self.memory_service.process_message(user_id=user_id, message=prompt)

        messages, citations = await self.context_builder.build(user_id=user_id, conversation_id=conversation_id, query=prompt)

        strategy = await self._get_strategy()
        tool_extension = strategy.get_system_prompt_extension()
        if tool_extension and messages and messages[0].get("role") == "system":
            messages[0]["content"] += tool_extension

        context = {"user_id": user_id, "conversation_id": conversation_id}
        tools_payload = strategy.get_tools_for_provider()

        planner = Planner(self.provider, strategy)
        agent = AgentExecutor(planner, self.tool_orchestrator, strategy)
        
        final_response = await agent.run(prompt, context, messages, tools_payload)

        await self.message_service.create(conversation_id, MessageCreate(role=MessageRole.ASSISTANT, content=final_response))
        return final_response, citations


    async def stream_chat(
        self,
        user_id: int,
        conversation_id: int,
        prompt: str,
    ) -> AsyncGenerator[str, None]:

        await self.conversation_service.get_by_id(conversation_id, user_id)
        await self.message_service.create(conversation_id, MessageCreate(role=MessageRole.USER, content=prompt))
        await self.memory_service.process_message(user_id=user_id, message=prompt)

        messages, citations = await self.context_builder.build(user_id=user_id, conversation_id=conversation_id, query=prompt)

        strategy = await self._get_strategy()
        tool_extension = strategy.get_system_prompt_extension()
        if tool_extension and messages and messages[0].get("role") == "system":
            messages[0]["content"] += tool_extension

        yield f"data: {json.dumps({'type': 'citations', 'citations': [c.model_dump() for c in citations]})}\n\n"

        context = {"user_id": user_id, "conversation_id": conversation_id}
        tools_payload = strategy.get_tools_for_provider()
        
        planner = Planner(self.provider, strategy)
        agent = AgentExecutor(planner, self.tool_orchestrator, strategy)
        
        final_response = ""
        async for chunk in agent.stream_run(prompt, context, messages, tools_payload):
            if chunk.startswith("data: ") and '"delta"' in chunk:
                # Accumulate the final answer transparently for storage
                try:
                    delta = json.loads(chunk[6:])['delta']
                    final_response += delta
                except:
                    pass
            yield chunk

        await self.message_service.create(conversation_id, MessageCreate(role=MessageRole.ASSISTANT, content=final_response))
        yield "data: [DONE]\n\n"