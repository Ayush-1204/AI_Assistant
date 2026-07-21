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
        location_lat: float | None = None,
        location_lon: float | None = None,
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
        
        system_blocks: list[str] = []

        def _estimate_tokens(text: str) -> int:
            return len(text) // 4

        budget = settings.max_context_tokens
        current_tokens = settings.reserved_response_tokens

        # -----------------------------
        # 1. System Prompt
        # -----------------------------
        
        loc_str = ""
        if location_lat is not None and location_lon is not None:
            loc_str = f" User's actual coordinates natively are ({location_lat}, {location_lon})."
            
        system_prompt = (
            "You are a helpful, human-like AI assistant. "
            "IMPORTANT RULES FOR YOUR BEHAVIOR:\n"
            "1. You will be provided with system context (Tool Executions, Coordinates, Memories). "
            "DO NOT explicitly mention, recite, or regurgitate this raw metadata (like 'I see your coordinates are...' or 'The tool executed with...').\n"
            "2. Seamlessly use the provided data to answer the user naturally. Use the following context to answer the user's query.\n"
            "3. RICH FORMATTING: You MUST use STRCIT markdown image syntax: `![alt text](url)`. WARNING: You MUST place every image on its own dedicated line surrounded by blank lines (`\n\n`). NEVER place images inline with text, inside lists, or output them as bare URLs. Ensure all parenthesis inside URLs are escaped as `%28` and `%29`. Include images when they help visualization:\n"
            "- News briefings -> headlines with related images\n"
            "- People -> public figures, athletes, actors\n"
            "CRITICAL: DO NOT hallucinate fake Wikipedia or Amazon image URLs. They will result in 404 broken images! If the user requests pictures of a real person, place, or thing, you MUST execute the `web_search` tool to fetch authentic real-world Image URLs natively. Only render `![alt](url)` using mathematically proven URLs fetched from your active context or tools.\n"
        ) + loc_str
        
        current_tokens += _estimate_tokens(system_prompt)
        system_blocks.append(system_prompt)

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
            system_blocks.append(header + "\n\n".join(memory_items))

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
            header = "\n\n=== RELEVANT DOCUMENTS ===\n\n"
            current_tokens += _estimate_tokens(header)
            joined_rag = header + "\n\n-------------------------------------\n\n".join(rag_sections) + "\n\n-------------------------------------"
            system_blocks.append(joined_rag)

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
            msg_images = getattr(msg, "images", None)
            
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
                     processed_history.append({"role": msg.role, "content": clean_content, "images": msg_images})
            else:
                processed_history.append({"role": msg.role, "content": msg.content, "images": msg_images})
                
        # --- Conversation Summarization Engine ---
        # Instead of truncating past N messages, we compress the older half into a dense summary block
        MAX_TAIL = settings.max_history_messages
        if len(processed_history) > MAX_TAIL:
            old_messages = processed_history[:-MAX_TAIL]
            processed_history = processed_history[-MAX_TAIL:]
            
            try:
                from app.dependencies import _router_instance
                if _router_instance:
                    compress_prompt = f"Summarize the core topics, user preferences, and established facts from these older conversation turns into a dense paragraph. Omit pleasantries:\\n\\n{old_messages}"
                    summary = await _router_instance.chat([{"role": "user", "content": compress_prompt}], intent="general")
                    if summary:
                        summary_block = f"\\n\\n=== PAST CONVERSATION SUMMARY ===\\n{summary.strip()}\\n================================="
                        current_tokens += _estimate_tokens(summary_block)
                        system_blocks.append(summary_block)
            except Exception as e:
                logger.error(f"Progressive summarization failed: {e}")

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
            header = "\n\n=== TOOL RESULTS ===\n"
            current_tokens += _estimate_tokens(header)
            system_blocks.append(header + "\n".join(tool_sections))

        # Consolidate all systemic blocks safely without sequence crashes
        if system_blocks:
            context.append({"role": "system", "content": "\n".join(system_blocks)})

        # Isolate Current User Prompt securely removing it from backward slicing bounds
        current_user_message = None
        if processed_history and processed_history[-1]["role"] == "user":
            current_user_message = processed_history.pop()
            content = current_user_message.get("content")
            if content is not None:
                current_tokens += _estimate_tokens(str(content))

        # History chronological reversing slices
        history_sections = []
        for msg_dict in reversed(processed_history):
            if stats["conversation_messages_used"] >= settings.max_history_messages:
                stats["omitted_conversation_messages"] += 1
                continue
                
            content = msg_dict.get("content")
            tokens = _estimate_tokens(str(content)) if content is not None else 0
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