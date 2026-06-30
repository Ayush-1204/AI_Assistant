from app.schemas.message import MessageCreate
from app.schemas.message import MessageRole
from app.services.ai.context.context_builder import ContextBuilder
from app.services.ai.memory.memory_service import MemoryService
from app.services.ai.providers.base import BaseLLMProvider
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService


class AIService:

    def __init__(
        self,
        provider: BaseLLMProvider,
        message_service: MessageService,
        conversation_service: ConversationService,
        context_builder: ContextBuilder,
        memory_service: MemoryService,
    ):
        self.provider = provider
        self.message_service = message_service
        self.conversation_service = conversation_service
        self.context_builder = context_builder
        self.memory_service = memory_service

    async def chat(
        self,
        user_id: int,
        conversation_id: int,
        prompt: str,
    ) -> str:

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

        # -------- Context --------

        messages = await self.context_builder.build(
            user_id=user_id,
            conversation_id=conversation_id,
        )

        response = await self.provider.chat(
            messages,
        )

        await self.message_service.create(
            conversation_id,
            MessageCreate(
                role=MessageRole.ASSISTANT,
                content=response,
            ),
        )

        return response