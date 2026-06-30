from fastapi import HTTPException, status

from app.db.models import Message
from app.repositories import (
    ConversationRepository,
    MessageRepository,
)
from app.schemas.message import MessageCreate, MessageUpdate


class MessageService:
    def __init__(
        self,
        message_repository: MessageRepository,
        conversation_repository: ConversationRepository,
    ):
        self.message_repository = message_repository
        self.conversation_repository = conversation_repository

    async def create(
        self,
        conversation_id: int,
        data: MessageCreate,
    ) -> Message:
        conversation = await self.conversation_repository.get_by_id(
            conversation_id
        )

        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        message = Message(
            conversation_id=conversation_id,
            role=data.role.value,
            content=data.content,
        )

        return await self.message_repository.create(message)

    async def get_by_id(
        self,
        message_id: int,
    ) -> Message:
        message = await self.message_repository.get_by_id(message_id)

        if message is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        return message

    async def list_by_conversation(
        self,
        conversation_id: int,
    ) -> list[Message]:
        conversation = await self.conversation_repository.get_by_id(
            conversation_id
        )

        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        return await self.message_repository.list_by_conversation(
            conversation_id
        )

    async def update(
        self,
        message_id: int,
        data: MessageUpdate,
    ) -> Message:
        message = await self.get_by_id(message_id)

        if data.content is not None:
            message.content = data.content

        return await self.message_repository.update(message)
    
    async def get_history(
        self,
        conversation_id: int,
    ) -> list[dict]:
        """
        Return the conversation history formatted
        for the LLM provider.
        """

        messages = await self.list_by_conversation(
            conversation_id,
        )

        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
        ]

    async def delete(
        self,
        message_id: int,
    ) -> None:
        message = await self.get_by_id(message_id)

        await self.message_repository.delete(message)