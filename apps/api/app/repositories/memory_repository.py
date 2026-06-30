from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Memory


class MemoryRepository:
    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

    async def create(
        self,
        memory: Memory,
    ) -> Memory:
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def get_by_id(
        self,
        memory_id: int,
    ) -> Memory | None:
        result = await self.db.execute(
            select(Memory).where(
                Memory.id == memory_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: int,
    ) -> list[Memory]:
        result = await self.db.execute(
            select(Memory)
            .where(
                Memory.user_id == user_id,
            )
            .order_by(
                Memory.updated_at.desc(),
            )
        )

        return list(result.scalars().all())

    async def get_by_key(
        self,
        user_id: int,
        category: str,
        key: str,
    ) -> Memory | None:
        result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.category == category,
                Memory.key == key,
            )
        )

        return result.scalar_one_or_none()

    async def update(
        self,
        memory: Memory,
    ) -> Memory:
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def delete(
        self,
        memory: Memory,
    ) -> None:
        await self.db.delete(memory)
        await self.db.commit()