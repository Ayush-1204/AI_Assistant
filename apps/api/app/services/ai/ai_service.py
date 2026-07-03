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

        max_loops = 5
        final_response = ""
        context = {"user_id": user_id, "conversation_id": conversation_id}
        tools_payload = strategy.get_tools_for_provider()

        for _ in range(max_loops):
            response_obj = await self.provider.chat(messages, tools=tools_payload)
            
            has_tool, tool_requests = strategy.extract_requests(response_obj)
            if has_tool:
                messages.extend(strategy.format_assistant_message(response_obj))
                tool_responses = await self.tool_orchestrator.execute_all(tool_requests, context)
                messages.extend(strategy.format_responses_to_messages(tool_responses, raw_tool_call=response_obj))
                continue
                
            final_response = strategy.get_text_from_response(response_obj)
            break

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

        max_loops = 5
        final_response = ""
        context = {"user_id": user_id, "conversation_id": conversation_id}
        tools_payload = strategy.get_tools_for_provider()
        
        for loop in range(max_loops):
            collected_response_obj = None
            full_text = ""
            is_tool_call_predicted = False
            
            async for chunk in self.provider.stream_chat(messages, tools=tools_payload):
                if not isinstance(chunk, str):
                    # Native object chunks from SDK supporting function_calls
                    is_tool_call_predicted = True
                    collected_response_obj = chunk
                    continue
                    
                full_text += chunk
                
                if "<tool_call" in full_text:
                    is_tool_call_predicted = True
                    continue
                    
                yield f"data: {json.dumps({'type': 'content', 'delta': chunk})}\n\n"

            if is_tool_call_predicted:
                 has_tool, tool_requests = False, []
                 
                 source_payload = collected_response_obj if collected_response_obj else full_text
                 has_tool, tool_requests = strategy.extract_requests(source_payload)
                 
                 if has_tool:
                     yield f"data: {json.dumps({'type': 'tool', 'name': 'Executing tools natively...'})}\n\n"
                     
                     messages.extend(strategy.format_assistant_message(source_payload))
                     tool_responses = await self.tool_orchestrator.execute_all(tool_requests, context)
                     messages.extend(strategy.format_responses_to_messages(tool_responses, raw_tool_call=source_payload))
                     continue
            
            final_response = full_text
            break

        await self.message_service.create(conversation_id, MessageCreate(role=MessageRole.ASSISTANT, content=final_response))
        yield "data: [DONE]\n\n"