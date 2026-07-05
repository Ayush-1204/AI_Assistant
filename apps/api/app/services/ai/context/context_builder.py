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
        
        stats = {
            "conversation_messages_used": 0,
            "memories_used": 0,
            "documents_used": 0,
            "tool_results_used": 0,
            "approximate_context_size": 0,
            "omitted_conversation_messages": 0,
            "omitted_memories": 0,
            "omitted_document_chunks": 0,
            "omitted_tool_outputs": 0,
        }

        def _estimate_tokens(text: str) -> int:
            return len(text) // 4

        budget = settings.max_context_tokens
        current_tokens = settings.reserved_response_tokens

        # -----------------------------
        # 1. System Prompt
        # -----------------------------
        
        system_prompt = "You are a helpful AI assistant. Use the following context to answer the user's query."
        current_tokens += _estimate_tokens(system_prompt)
        context.append({"role": "system", "content": system_prompt})

        # -----------------------------
        # 2. Long-term memory
        # -----------------------------

        memories = await self.memory_service.retrieve_memories(user_id)
        memory_items = []

        if memories:
            for memory in memories:
                if stats["memories_used"] >= settings.max_memory_items:
                    stats["omitted_memories"] += 1
                    continue
                    
                line = f"• {memory.value}"
                tokens = _estimate_tokens(line)
                
                if current_tokens + tokens > budget:
                    stats["omitted_memories"] += 1
                    continue
                    
                current_tokens += tokens
                memory_items.append(line)
                stats["memories_used"] += 1

        if memory_items:
            header = "=== RELEVANT MEMORIES ===\n\n"
            current_tokens += _estimate_tokens(header)
            context.append(
                {
                    "role": "system",
                    "content": header + "\n\n".join(memory_items),
                }
            )

        # -----------------------------
        # 3. RAG (Relevant Documents)
        # -----------------------------

        retrieval_results = await self.retrieval_service.retrieve(
            query=query,
            user_id=user_id,
        )

        rag_sections = []
        if retrieval_results:
            for result in retrieval_results:
                if stats["documents_used"] >= settings.max_document_chunks:
                    stats["omitted_document_chunks"] += 1
                    continue

                chunk = result.chunk
                document = chunk.document
                
                doc_name = (
                    getattr(document, "title", None)
                    or getattr(document, "original_filename", None)
                    or getattr(document, "filename", None)
                    or "Untitled Document"
                )

                chunk_content = (
                    f"Document: {doc_name}\n\n"
                    f"Chunk: {chunk.chunk_index}\n\n"
                    f"Similarity: {result.distance:.3f}\n\n"
                    f"{chunk.content}"
                )
                
                tokens = _estimate_tokens(chunk_content)
                if current_tokens + tokens > budget:
                    stats["omitted_document_chunks"] += 1
                    continue
                    
                current_tokens += tokens
                rag_sections.append(chunk_content)
                stats["documents_used"] += 1

                citations.append(
                    Citation(
                        document_title=doc_name,
                        chunk_index=chunk.chunk_index,
                        similarity=round(result.distance, 3) if result.distance is not None else 0.0
                    )
                )

        if rag_sections:
            header = "=== RELEVANT DOCUMENTS ===\n\n"
            current_tokens += _estimate_tokens(header)
            joined_rag = header + "\n\n-------------------------------------\n\n".join(rag_sections) + "\n\n-------------------------------------"
            context.append({"role": "system", "content": joined_rag})

        # -----------------------------
        # 4. Tool Results & Conversation History
        # -----------------------------

        history = await self.message_service.list_by_conversation(
            conversation_id,
        )
        
        tool_results = []
        processed_history = []
        import re

        for msg in history:
            if "<tool_response>" in msg.content:
                pattern = r"(Tool execution result for:.*?)?<tool_response>(.*?)</tool_response>"
                matches = list(re.finditer(pattern, msg.content, re.DOTALL))
                for match in matches:
                    res = match.group(2).strip()
                    if len(res) > settings.max_tool_output_length:
                        res = res[:settings.max_tool_output_length] + "...[TRUNCATED]"
                    tool_results.append(res)
                    
                clean_content = re.sub(pattern, "", msg.content, flags=re.DOTALL).strip()
                if clean_content:
                     processed_history.append({"role": msg.role, "content": clean_content})
            else:
                processed_history.append({"role": msg.role, "content": msg.content})

        # Process Tools budget
        tool_sections = []
        if tool_results:
            for res in tool_results:
                if stats["tool_results_used"] >= settings.max_tool_results:
                    stats["omitted_tool_outputs"] += 1
                    continue
                    
                tokens = _estimate_tokens(res)
                if current_tokens + tokens > budget:
                    stats["omitted_tool_outputs"] += 1
                    continue
                    
                current_tokens += tokens
                tool_sections.append(res)
                stats["tool_results_used"] += 1
                
        if tool_sections:
            header = "=== TOOL RESULTS ===\n"
            current_tokens += _estimate_tokens(header)
            context.append({"role": "system", "content": header + "\n".join(tool_sections)})

        # Isolate Current User Prompt securely removing it from backward slicing bounds
        current_user_message = None
        if processed_history and processed_history[-1]["role"] == "user":
            current_user_message = processed_history.pop()
            current_tokens += _estimate_tokens(current_user_message["content"])

        # History chronological reversing slices
        history_sections = []
        for msg_dict in reversed(processed_history):
            if stats["conversation_messages_used"] >= settings.max_history_messages:
                stats["omitted_conversation_messages"] += 1
                continue
                
            tokens = _estimate_tokens(msg_dict["content"])
            if current_tokens + tokens > budget:
                stats["omitted_conversation_messages"] += 1
                continue
                
            current_tokens += tokens
            history_sections.append(msg_dict)
            stats["conversation_messages_used"] += 1
            
        history_sections.reverse()
        for h_msg in history_sections:
            context.append(h_msg)

        if current_user_message:
            context.append(current_user_message)

        # -----------------------------
        # Analytics & Return
        # -----------------------------
        
        stats["approximate_context_size"] = current_tokens
        
        logger.info(
            f"Context Statistics built: "
            f"usage=[mem:{stats['memories_used']}/{settings.max_memory_items}, "
            f"docs:{stats['documents_used']}/{settings.max_document_chunks}, "
            f"tools:{stats['tool_results_used']}/{settings.max_tool_results}, "
            f"history:{stats['conversation_messages_used']}/{settings.max_history_messages}], "
            f"omitted=[mem:{stats['omitted_memories']}, docs:{stats['omitted_document_chunks']}, "
            f"tools:{stats['omitted_tool_outputs']}, hist:{stats['omitted_conversation_messages']}], "
            f"tokens_used: {current_tokens}/{budget}"
        )
        
        # Attach securely without crashing native unpack loops
        self.last_metadata = stats

        return context, citations