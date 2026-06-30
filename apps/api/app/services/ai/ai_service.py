from app.schemas.message import MessageCreate, MessageRole
from app.services.ai.providers.base import BaseLLMProvider
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService


class AIService:
    """
    High-level AI orchestration service.
    """

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
        Complete AI conversation pipeline.
        """

        # Validate conversation ownership
        await self.conversation_service.get_by_id(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        # Store user message
        await self.message_service.create(
            conversation_id=conversation_id,
            data=MessageCreate(
                role=MessageRole.USER,
                content=prompt,
            ),
        )

        # Load conversation history
        history = await self.message_service.get_history(
            conversation_id,
        )

        # Generate AI response
        response = await self.provider.chat(
            history,
        )

        # Store assistant response
        await self.message_service.create(
            conversation_id=conversation_id,
            data=MessageCreate(
                role=MessageRole.ASSISTANT,
                content=response,
            ),
        )

        conversation = await self.conversation_service.get_by_id(
            conversation_id,
            user_id,
        )

        if conversation.title == "New Conversation":
            title = await self.provider.generate_title(
                prompt,
            )

            await self.conversation_service.update_title(
                conversation_id=conversation_id,
                user_id=user_id,
                title=title,
            )

        return response