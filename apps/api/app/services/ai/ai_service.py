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

    async def chat(
        self,
        user_id: int,
        conversation_id: int,
        prompt: str,
    ) -> tuple[str, list[Citation]]:

        await self.conversation_service.get_by_id(
            conversation_id,
            user_id,
        )

        await self.message_service.create(
            conversation_id,
            MessageCreate(
                role=MessageRole.USER,
                content=prompt,
            ),
        )

        # -------- Memory --------

        await self.memory_service.process_message(
            user_id=user_id,
            message=prompt,
        )

        # ---------------- Context ----------------

        messages, citations = await self.context_builder.build(
            user_id=user_id,
            conversation_id=conversation_id,
            query=prompt,
        )

        tool_extension = self.tool_orchestrator.get_system_prompt_extension()
        if tool_extension and messages and messages[0].get("role") == "system":
            messages[0]["content"] += tool_extension

        max_loops = 5
        final_response = ""
        context = {"user_id": user_id, "conversation_id": conversation_id}

        for _ in range(max_loops):
            response = await self.provider.chat(messages)
            
            has_tool, raw_call, tool_res = await self.tool_orchestrator.extract_and_execute(response, context)
            if has_tool:
                messages.append({"role": "assistant", "content": response})
                
                tool_msg_content = f"Tool execution result for:\n{raw_call}\n\n<tool_response>\n{tool_res}\n</tool_response>"
                messages.append({"role": "user", "content": tool_msg_content})
                continue
                
            final_response = response
            break

        await self.message_service.create(
            conversation_id,
            MessageCreate(
                role=MessageRole.ASSISTANT,
                content=final_response,
            ),
        )

        return final_response, citations

    async def stream_chat(
        self,
        user_id: int,
        conversation_id: int,
        prompt: str,
    ) -> AsyncGenerator[str, None]:

        await self.conversation_service.get_by_id(
            conversation_id,
            user_id,
        )

        await self.message_service.create(
            conversation_id,
            MessageCreate(
                role=MessageRole.USER,
                content=prompt,
            ),
        )

        # -------- Memory --------

        await self.memory_service.process_message(
            user_id=user_id,
            message=prompt,
        )

        # ---------------- Context ----------------

        messages, citations = await self.context_builder.build(
            user_id=user_id,
            conversation_id=conversation_id,
            query=prompt,
        )

        tool_extension = self.tool_orchestrator.get_system_prompt_extension()
        if tool_extension and messages and messages[0].get("role") == "system":
            messages[0]["content"] += tool_extension

        yield f"data: {json.dumps({'type': 'citations', 'citations': [c.model_dump() for c in citations]})}\n\n"

        max_loops = 5
        final_response = ""
        context = {"user_id": user_id, "conversation_id": conversation_id}
        
        for loop in range(max_loops):
            full_response = ""
            is_tool_call_predicted = False
            
            async for chunk in self.provider.stream_chat(messages):
                full_response += chunk
                
                if "<tool_call" in full_response:
                    is_tool_call_predicted = True
                    continue
                    
                yield f"data: {json.dumps({'type': 'content', 'delta': chunk})}\n\n"

            if is_tool_call_predicted:
                 has_tool, raw_call, tool_res = await self.tool_orchestrator.extract_and_execute(full_response, context)
                 if has_tool:
                     yield f"data: {json.dumps({'type': 'tool', 'name': 'Executing tools natively...'})}\n\n"
                     
                     messages.append({"role": "assistant", "content": full_response})
                     tool_msg_content = f"Tool execution result for:\n{raw_call}\n\n<tool_response>\n{tool_res}\n</tool_response>"
                     messages.append({"role": "user", "content": tool_msg_content})
                     continue
            
            final_response = full_response
            break

        await self.message_service.create(
            conversation_id,
            MessageCreate(
                role=MessageRole.ASSISTANT,
                content=final_response,
            ),
        )

        yield "data: [DONE]\n\n"