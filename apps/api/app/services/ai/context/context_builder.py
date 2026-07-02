from app.services.ai.memory.memory_service import MemoryService
from app.services.message_service import MessageService
from app.services.retrieval.retrieval_service import RetrievalService


class ContextBuilder:
    """
    Builds the complete context sent to the LLM.

    Context order
    -------------
    1. Long-term memories
    2. Retrieved document context (RAG)
    3. Conversation history

    Future
    ------
    - Calendar
    - Email
    - Tool outputs
    """

    def __init__(
        self,
        message_service: MessageService,
        memory_service: MemoryService,
        retrieval_service: RetrievalService,
    ):
        self.message_service = message_service
        self.memory_service = memory_service
        self.retrieval_service = retrieval_service

    async def build(
        self,
        *,
        user_id: int,
        conversation_id: int,
        query: str,
    ) -> list[dict]:

        context: list[dict] = []

        # -----------------------------
        # Long-term memory
        # -----------------------------

        memories = await self.memory_service.retrieve_memories(
            user_id,
        )

        if memories:

            memory_text = "\n".join(
                f"- {memory.key}: {memory.value}"
                for memory in memories
            )

            context.append(
                {
                    "role": "system",
                    "content": (
                        "Long-term user memories:\n\n"
                        f"{memory_text}"
                    ),
                }
            )

        # -----------------------------
        # RAG
        # -----------------------------

        retrieval_results = (
            await self.retrieval_service.retrieve(
                query=query,
                user_id=user_id,
            )
        )

        if retrieval_results:

            rag_sections: list[str] = []

            for result in retrieval_results:

                chunk = result.chunk

                document = chunk.document

                document_name = (
                    getattr(document, "title", None)
                    or getattr(document, "original_filename", None)
                    or "Untitled Document"
                )

                rag_sections.append(
                    (
                        f"Document: {document_name}\n"
                        f"Chunk: {chunk.chunk_index}\n"
                        f"Similarity: {result.similarity:.3f}\n\n"
                        f"{chunk.content}"
                    )
                )

            context.append(
                {
                    "role": "system",
                    "content": (
                        "Relevant document context:\n\n"
                        + "\n\n---\n\n".join(rag_sections)
                    ),
                }
            )

        # -----------------------------
        # Conversation history
        # -----------------------------

        history = (
            await self.message_service.list_by_conversation(
                conversation_id,
            )
        )

        for message in history:

            context.append(
                {
                    "role": message.role,
                    "content": message.content,
                }
            )

        return context