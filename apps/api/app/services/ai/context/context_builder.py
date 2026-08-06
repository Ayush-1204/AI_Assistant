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
        user_name: str | None = None,
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
            
        name_str = f" The user's name is '{user_name}'." if user_name else ""
        
        system_prompt = (
            "You are a warm, highly personal, and buddy-like AI assistant. Speak to the user as a close, highly capable friend. "
            "IMPORTANT RULES FOR YOUR BEHAVIOR:\n"
            "1. You will be provided with system context (Tool Executions, Coordinates, Memories). "
            "DO NOT explicitly mention, recite, or regurgitate this raw metadata (like 'I see your coordinates are...' or 'The tool executed with...'). HOWEVER, you MUST proactively seamlessly use the provided Memories to personalize your conversation. For example, if you know their name, greet them by their name. If they ask 'what's my name', just tell them without saying 'I have a memory of...'. Always weave their preferences into your natural responses.\n"
            "2. Seamlessly use the provided data to answer the user naturally. Use the following context to answer the user's query.\n"
            "3. RICH FORMATTING & IMAGES: You MUST use STRICT markdown image syntax (example: ![alt text](url)). DO NOT wrap images in backticks or code blocks. IMPORTANT: If you have multiple related images (e.g., for a news story or summary), output them consecutively (example: ![alt1](url1)\n![alt2](url2)). The frontend will automatically group consecutive images into a beautiful image grid! Ensure all parenthesis inside URLs are escaped as `%28` and `%29`.\n"
            "CRITICAL: DO NOT hallucinate fake image URLs (like google.com/search, imgur.com, unsplash, or placeholder image sites). You are STRICTLY FORBIDDEN from generating ANY image URL that you did not explicitly retrieve from a tool execution (like `image_search` or `web_search`) in this very turn. NEVER invent or guess your own image URLs! FAIL-SAFE: If the provided system context does NOT contain any retrieved image URLs, you MUST NOT attempt to display any images. Just output text normally and do NOT apologize for not having images.\n"
            "PROACTIVE SEARCH & IMAGES: If the user's query or your response involves news, current events, real-time information, or is about a specific person, place, product, recipe, recent event, or notable entity, you MUST actively and CONCURRENTLY invoke BOTH the `web_search` tool (to verify facts and fetch the latest information) AND the `image_search` tool (to fetch verified images) in the SAME step!\n"
            "NEVER hallucinate news or current events! You MUST ONLY summarize concrete, retrieved articles.\n"
            "- For step-by-step processes (like recipes), invoke `image_search` for the different steps and output all the images CONSECUTIVELY at the top or bottom of the process so they automatically form a beautiful carousel or gallery! Do NOT separate them with text.\n"
            "- For news briefings or multi-topic responses, you MUST first invoke multiple parallel, highly targeted `web_search` queries matching the user's requested sections (e.g., one search for 'AI technology news', one for 'World politics news'). If a search returns no recent articles for a category, you MUST explicitly state 'No major updates today' rather than inventing general trends! Then, you MUST invoke `image_search` SEPARATELY for EACH individual topic/news item! (e.g., if you have 5 news stories, you MUST invoke `image_search` 5 distinct times with specific queries for each story). Do NOT make just one generic image search for the whole briefing! Set `count=3` or `count=6` to generate a gallery for each topic, and place the resulting gallery directly underneath that specific topic's heading! Do NOT group all images at the very top of the response! Include the images to make it visually engaging! Do not rely solely on your internal training data.\n"
            "4. FATAL WARNING: NEVER USE CONVERSATIONAL ANGLE BRACKETS! DO NOT use internal monologues, `<thought>` tags, or conversational reasoning bounded by `< >` (e.g., `<It appears...`). Angle brackets are STRICTLY RESERVED for tool invocations and literal markdown code blocks. Any conversational use of angle brackets will instantly crash the rendering pipeline!\n"
            "5. NO REFUSALS FOR SCRAPING: You MUST obey user requests to extract, scrape, or search public websites (including Wikipedia). DO NOT hallucinate policies or restrictions about scraping public knowledge bases. Always invoke the `browser` or `web_search` tools to accomplish the task rather than lecturing the user.\n"
            "6. RESPONSE FORMATTING RULES (GFM):\n"
            "- PREMIUM LAYOUT: When providing news, summaries, or briefings, use a highly visual magazine style. Use `###` headings for article titles. For each article/topic, place its corresponding image gallery IMMEDIATELY underneath the heading. Use bolding for key takeaways (e.g., `**Why it matters:**`). Separate stories cleanly with horizontal rules (`---`). DO NOT just output a plain numbered list of text.\n"
            "- Produce valid GitHub-Flavored Markdown only. Break long answers into logical sections. Avoid walls of text. Prefer lists over long paragraphs. Prefer tables when comparing information.\n"
            "- Use lists properly: `- Item`, `- [x] Task`. Keep formatting minimal and purposeful. Do not use HTML unless requested.\n"
            "- ONLY generate code blocks if the user's query is explicitly about programming, software, or terminal commands. Always wrap multi-line code inside fenced code blocks and specify language (e.g. `dart`, `python`). Use inline code (backticks) for commands, filenames, APIs.\n"
            "- Mathematics: Use LaTeX. Inline equations `$...$`, `\\(...\\)`. Display equations `$$...$$`, `\\[...\\]`.\n"
            "- Links: Use Markdown links. Do not expose bare URLs. Images: Always use Markdown image syntax.\n"
            "- Quotes: Use Markdown blockquotes `>`. Use horizontal rules `---` only to separate major sections.\n"
            "- Tone: Responses should be clean, structured, concise, easy to scan, professional, natural.\n"
            "- Code Quality: Ensure all code examples use the latest, most modern library syntax (e.g., OpenAI v1.x) and strictly avoid deprecated patterns.\n"
            "- Output Rules: Never explain your formatting. Never mention Markdown. Never mention LaTeX. Simply produce the correctly formatted response.\n"
            "7. EXECUTION PLAN: You may receive an UPFRONT EXECUTION PLAN at the bottom of your context. If provided, you MUST obey its output structure and execute its listed tool tasks BEFORE generating your final response.\n"
        ) + loc_str + name_str
        
        from datetime import datetime
        now = datetime.now()
        hour = now.hour
        if 5 <= hour < 12:
            greeting_context = "Morning"
        elif 12 <= hour < 17:
            greeting_context = "Afternoon"
        elif 17 <= hour < 22:
            greeting_context = "Evening"
        else:
            greeting_context = "Night"
            
        time_str = f" The current local date and time is {now.isoformat(timespec='seconds')} (Time of day: {greeting_context})."
        system_prompt += time_str
        
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
                    
                line = f"• {memory.key}: {memory.value}"
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
        # 3. RAG (Relevant Documents) - REMOVED
        # Documents are now only accessed via the search_documents tool to prevent
        # context leaking and hallucinations in general chat.
        # -----------------------------

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
                    else:
                        tool_results.append(res)
                    
                clean_content = re.sub(pattern, "", msg.content, flags=re.DOTALL).strip()
                # Scrub massive base64 markdown images added by frontend for UI rendering
                clean_content = re.sub(r"!\[attachment\]\(data:image\/[^;]+;base64,[^\)]+\)", "[Attached Image]", clean_content)
                
                if clean_content:
                     processed_history.append({"role": msg.role, "content": clean_content, "images": msg_images})
            else:
                # Scrub massive base64 markdown images added by frontend for UI rendering
                clean_content = re.sub(r"!\[attachment\]\(data:image\/[^;]+;base64,[^\)]+\)", "[Attached Image]", msg.content)
                processed_history.append({"role": msg.role, "content": clean_content, "images": msg_images})
                
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