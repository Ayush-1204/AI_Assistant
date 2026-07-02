import logging

from app.config import settings
from app.schemas.chat import Citation
from app.services.ai.memory.memory_service import MemoryService
from app.services.message_service import MessageService
from app.services.retrieval.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


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
    ) -> tuple[list[dict], list[Citation]]:

        context: list[dict] = []
        citations: list[Citation] = []

        # -----------------------------
        # 1. System Prompt
        # -----------------------------
        
        context.append(
            {
                "role": "system",
                "content": "You are a helpful AI assistant. Use the following context to answer the user's query.",
            }
        )

        # -----------------------------
        # 2. Long-term memory
        # -----------------------------

        memories = await self.memory_service.retrieve_memories(
            user_id,
        )

        if memories:
            memories = memories[:settings.context_max_memories]

            memory_items = "\n\n".join(
                f"• {memory.value}"
                for memory in memories
            )

            context.append(
                {
                    "role": "system",
                    "content": (
                        "=== RELEVANT MEMORIES ===\n\n"
                        f"{memory_items}"
                    ),
                }
            )

        # -----------------------------
        # 3. RAG (Relevant Documents)
        # -----------------------------

        retrieval_results = (
            await self.retrieval_service.retrieve(
                query=query,
                user_id=user_id,
            )
        )

        if retrieval_results:
            retrieval_results = retrieval_results[:settings.rag_max_context_chunks]

            rag_sections: list[str] = []

            for result in retrieval_results:

                chunk = result.chunk
                document = chunk.document
                
                print(f"\n[DEBUG] Retrieved Chunk Content (First 300 chars): {chunk.content[:300]}\n")

                document_name = (
                    getattr(document, "title", None)
                    or getattr(document, "original_filename", None)
                    or getattr(document, "filename", None)
                    or "Untitled Document"
                )

                rag_sections.append(
                    (
                        f"Document: {document_name}\n\n"
                        f"Chunk: {chunk.chunk_index}\n\n"
                        f"Similarity: {result.distance:.3f}\n\n"
                        f"{chunk.content}"
                    )
                )

                citations.append(
                    Citation(
                        document_title=document_name,
                        chunk_index=chunk.chunk_index,
                        similarity=round(result.distance, 3)
                    )
                )

            context.append(
                {
                    "role": "system",
                    "content": (
                        "=== RELEVANT DOCUMENTS ===\n\n"
                        + "\n\n-------------------------------------\n\n".join(rag_sections)
                        + "\n\n-------------------------------------"
                    ),
                }
            )

        # -----------------------------
        # 4. Conversation history (and current User message)
        # -----------------------------

        history = (
            await self.message_service.list_by_conversation(
                conversation_id,
            )
        )

        if history and settings.context_max_history > 0:
            history = history[-settings.context_max_history:]
        elif not history or settings.context_max_history <= 0:
            history = []

        for message in history:

            context.append(
                {
                    "role": message.role,
                    "content": message.content,
                }
            )

        logger.debug(
            f"Context built: memories={len(memories) if memories else 0}, "
            f"documents={len(retrieval_results) if retrieval_results else 0}, "
            f"history={len(history) if history else 0}"
        )

        return context, citations