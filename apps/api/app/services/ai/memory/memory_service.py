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

    async def process_document_chunks(
        self,
        user_id: int,
        chunks_text: str,
    ) -> None:
        if not chunks_text or len(chunks_text.strip()) == 0:
            return

        candidate_memories = await getattr(self.extractor, "extract_from_chunks")(chunks_text)
        
        if not candidate_memories:
            return
            
        for memory in candidate_memories:
            if memory.get("confidence", 0) < 0.90:
                continue
                
            existing = await self.repository.get_by_key(
                user_id=user_id,
                category=memory["category"],
                key=memory["key"],
            )

            if existing:
                existing.value = memory["value"]
                existing.confidence = memory["confidence"]
                await self.repository.update(existing)
            else:
                await self.repository.create(
                    Memory(
                        user_id=user_id,
                        category=memory["category"],
                        key=memory["key"],
                        value=memory["value"],
                        confidence=memory["confidence"],
                    )
                )