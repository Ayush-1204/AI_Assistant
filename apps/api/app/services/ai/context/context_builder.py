from app.services.message_service import MessageService
from app.services.ai.memory.memory_service import MemoryService


class ContextBuilder:
    """
    Builds the complete context sent to the LLM.

    Current Context
    ---------------
    1. Long-term memories
    2. Conversation history

    Future
    ------
    - RAG
    - Calendar
    - Email
    - Tool outputs
    """

    def __init__(
        self,
        message_service: MessageService,
        memory_service: MemoryService,
    ):
        self.message_service = message_service
        self.memory_service = memory_service

    async def build(
        self,
        user_id: int,
        conversation_id: int,
    ) -> list[dict]:

        context = []

        memories = await self.memory_service.retrieve_memories(
            user_id,
        )

        if memories:

            memory_text = "\n".join(
                f"- {m.key}: {m.value}"
                for m in memories
            )

            context.append(
                {
                    "role": "system",
                    "content": (
                        "Long-term user memories:\n"
                        f"{memory_text}"
                    ),
                }
            )

        history = await self.message_service.list_by_conversation(
            conversation_id,
        )

        for message in history:

            context.append(
                {
                    "role": message.role,
                    "content": message.content,
                }
            )

        return context