from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, conversation: Conversation) -> Conversation:
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def get_by_id(self, conversation_id: int) -> Conversation | None:
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, conversation: Conversation) -> Conversation:
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def delete(self, conversation: Conversation) -> None:
        await self.db.delete(conversation)
        await self.db.commit()