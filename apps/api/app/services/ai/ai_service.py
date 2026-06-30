from app.schemas.message import MessageCreate, MessageRole
from app.services.ai.providers.base import BaseLLMProvider
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService


class AIService:
    def __init__(
        self,
        provider: BaseLLMProvider,
        message_service: MessageService,
        conversation_service: ConversationService,
    ):
        self.provider = provider
        self.message_service = message_service
        self.conversation_service = conversation_service

    async def chat(
        self,
        user_id: int,
        conversation_id: int,
        prompt: str,
    ) -> str:
        """
        AI Conversation Pipeline

        Current Sprint
        --------------
        ✓ Validate conversation
        ✓ Store user message
        ✓ Load history
        ✓ Generate AI response
        """

        await self.conversation_service.get_by_id(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        await self.message_service.create(
            conversation_id=conversation_id,
            data=MessageCreate(
                role=MessageRole.USER,
                content=prompt,
            ),
        )

        history = await self.message_service.get_history(
            conversation_id,
        )

        response = await self.provider.generate(
            history,
        )

        return response