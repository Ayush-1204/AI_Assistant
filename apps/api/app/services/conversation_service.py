from fastapi import HTTPException, status

from app.db.models import Conversation
from app.repositories import ConversationRepository
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
)


class ConversationService:
    def __init__(self, repository: ConversationRepository):
        self.repository = repository

    async def create(
        self,
        user_id: int,
        data: ConversationCreate,
    ) -> Conversation:
        conversation = Conversation(
            title=data.title,
            user_id=user_id,
        )

        return await self.repository.create(conversation)

    async def get_by_id(
        self,
        conversation_id: int,
        user_id: int,
    ) -> Conversation:
        conversation = await self.repository.get_by_id(conversation_id)

        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        if conversation.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        return conversation

    async def list_by_user(
        self,
        user_id: int,
    ) -> list[Conversation]:
        return await self.repository.list_by_user(user_id)

    async def update(
        self,
        conversation_id: int,
        user_id: int,
        data: ConversationUpdate,
    ) -> Conversation:
        conversation = await self.get_by_id(
            conversation_id,
            user_id,
        )

        if data.title is not None:
            conversation.title = data.title

        return await self.repository.update(conversation)

    async def delete(
        self,
        conversation_id: int,
        user_id: int,
    ) -> None:
        conversation = await self.get_by_id(
            conversation_id,
            user_id,
        )

        await self.repository.delete(conversation)