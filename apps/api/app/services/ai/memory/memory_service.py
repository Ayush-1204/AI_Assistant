from app.repositories.memory_repository import MemoryRepository
from app.services.ai.memory.memory_detector import MemoryDetector

class MemoryService:
    """
    Handles long-term memory operations.

    Responsibilities
    ----------------
    - Decide whether a message should be remembered
    - Extract structured memory
    - Create or update memory
    """

    def __init__(
        self,
        repository: MemoryRepository,
    ):
        self.repository = repository

    async def process_message(
        self,
        user_id: int,
        message: str,
    ) -> None:
        """
        Process a user message.

        Current implementation:
        -----------------------
        Placeholder.

        Future implementation:
        ----------------------
        1. MemoryDetector
        2. MemoryExtractor
        3. Update/Create memory
        """

        if not MemoryDetector.should_extract(
            message,
        ):
            return

        # Memory extraction will be added
        # in the next commit.