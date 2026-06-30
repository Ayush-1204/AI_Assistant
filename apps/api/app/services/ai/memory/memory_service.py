from app.db.models import Memory
from app.repositories.memory_repository import MemoryRepository
from app.services.ai.memory.memory_detector import MemoryDetector
from app.services.ai.memory.memory_extractor import MemoryExtractor


class MemoryService:

    def __init__(
        self,
        repository: MemoryRepository,
        extractor: MemoryExtractor,
    ):
        self.repository = repository
        self.extractor = extractor

    async def process_message(
        self,
        user_id: int,
        message: str,
    ) -> None:

        if not MemoryDetector.should_extract(
            message,
        ):
            return

        memory = await self.extractor.extract(
            message,
        )

        if memory is None:
            return

        existing = await self.repository.get_by_key(
            user_id=user_id,
            category=memory["category"],
            key=memory["key"],
        )

        if existing:

            existing.value = memory["value"]
            existing.confidence = memory["confidence"]

            await self.repository.update(existing)

            return

        await self.repository.create(

            Memory(

                user_id=user_id,

                category=memory["category"],

                key=memory["key"],

                value=memory["value"],

                confidence=memory["confidence"],

            )

        )

    async def retrieve_memories(
        self,
        user_id: int,
    ) -> list[Memory]:

        return await self.repository.list_by_user(
            user_id,
        )