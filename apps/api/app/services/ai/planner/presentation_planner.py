import json
import logging
import re
import uuid
import typing
from typing import Any, AsyncGenerator

from app.schemas.ai_pipeline import CuratedContext
from app.services.ai.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


def _build_news_index(raw_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extracts the article list from raw news_search tool data."""
    news_raw = raw_data.get("news_search", {})
    if isinstance(news_raw, str):
        try:
            news_raw = json.loads(news_raw)
        except Exception:
            return []
            
    if isinstance(news_raw, dict):
        articles = news_raw.get("articles", [])
        if isinstance(articles, list):
            return [a for a in articles if isinstance(a, dict)]
    return []


def _match_and_inject_article(node: dict, articles: list[dict]) -> dict:
    """
    Matches a NewsCard node to the correct raw article using URL or Title,
    then injects the correct URL, Source, and Image.
    """
    if not articles:
        return node

    node_url = node.get("url", "").lower().strip()
    node_title = node.get("title", "").lower().strip()

    best_article = None
    
    # 1. Try to match by exact or partial URL
    if node_url:
        for art in articles:
            art_url = art.get("url", "").lower().strip()
            if art_url and (node_url in art_url or art_url in node_url):
                best_article = art
                break
                
    # 2. Fallback to title overlap scoring
    if not best_article and node_title:
        best_score = 0
        for art in articles:
            art_title = art.get("title", "").lower().strip()
            node_words = set(node_title.split())
            art_words = set(art_title.split())
            score = len(node_words & art_words)
            if score > best_score and score > 2:  # require at least 3 words to match
                best_score = score
                best_article = art

    # 3. If still no match, we can't reliably inject, but we'll use the first as a last resort
    if not best_article:
        best_article = articles[0]

    # Inject exact data
    node["title"] = best_article.get("title") or node.get("title", "")
    node["url"] = best_article.get("url", "")
    node["source"] = best_article.get("source", node.get("source", ""))
    
    img = best_article.get("imageUrl")
    if img:
        node["imageUrl"] = img
    else:
        node.pop("imageUrl", None)

    return node


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

def _hoist_image_gallery(layout: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Move all ImageGallery nodes to just after the first Heading node (or to the
    front of the list if there is no Heading). This ensures images always appear
    near the top of the response rather than at the bottom where the LLM tends
    to place them.
    """
    galleries = [n for n in layout if n.get("type") == "ImageGallery"]
    rest = [n for n in layout if n.get("type") != "ImageGallery"]
    if not galleries:
        return rest
    insert_at = 1 if rest and rest[0].get("type") == "Heading" else 0
    for g in reversed(galleries):
        rest.insert(insert_at, g)
    return rest


# ---------------------------------------------------------------------------
# Intra-node text streaming helpers
# ---------------------------------------------------------------------------

# Node types whose primary text field should be streamed token-by-token.
# Other types (WeatherCard, NewsCard, ImageGallery, …) appear fully-formed.
_TEXT_FIELDS_BY_TYPE: dict[str, str] = {
    "paragraph": "text",
    "heading": "text",
    "codeblock": "code",
}


class _StreamPartialState:
    """Mutable state tracking a single in-flight JSON object during streaming."""
    __slots__ = ("node_start_emitted", "current_id", "current_type",
                 "streaming_field", "text_emitted_len")

    def __init__(self) -> None:
        self.node_start_emitted: bool = False
        self.current_id: str | None = None
        self.current_type: str | None = None
        self.streaming_field: str | None = None
        self.text_emitted_len: int = 0

    def reset(self) -> None:
        self.node_start_emitted = False
        self.current_id = None
        self.current_type = None
        self.streaming_field = None
        self.text_emitted_len = 0


def _get_partial_text(buf: str, field: str) -> str | None:
    """
    Extract the current (possibly incomplete) decoded string value of `field`
    from a partial JSON object buffer. Returns None if the field key hasn't
    appeared yet. Handles basic JSON escape sequences.
    """
    pattern = re.compile(rf'"{re.escape(field)}"\s*:\s*"')
    m = pattern.search(buf)
    if not m:
        return None
    parts: list[str] = []
    i = m.end()
    esc_map = {'n': '\n', 't': '\t', '"': '"', '\\': '\\'}
    while i < len(buf):
        ch = buf[i]
        if ch == '\\' and i + 1 < len(buf):
            parts.append(esc_map.get(buf[i + 1], buf[i + 1]))
            i += 2
        elif ch == '"':
            break  # closing quote — string done
        else:
            parts.append(ch)
            i += 1
    return "".join(parts)


def _extract_partial_events(
    buf: str, state: _StreamPartialState
) -> list[dict[str, Any]]:
    """
    Inspect the current in-flight partial buffer (the content AFTER the last
    complete JSON object) and return any new SSE events to emit:
      - node_start  : emitted once per object when id & type are readable
      - node_text_delta : emitted for each new chunk of text in the streaming field
    """
    events: list[dict[str, Any]] = []
    if '{' not in buf:
        return events

    if not state.node_start_emitted:
        id_m = re.search(r'"id"\s*:\s*"([^"\\]+)"', buf)
        type_m = re.search(r'"type"\s*:\s*"([^"\\]+)"', buf)
        if id_m and type_m:
            state.current_id = id_m.group(1)
            state.current_type = type_m.group(1)
            state.node_start_emitted = True
            state.streaming_field = _TEXT_FIELDS_BY_TYPE.get(state.current_type.lower())
            if state.streaming_field:  # only announce text-bearing nodes
                events.append({
                    "event_type": "node_start",
                    "id": state.current_id,
                    "node_type": state.current_type,
                })

    if state.streaming_field and state.node_start_emitted:
        partial_text = _get_partial_text(buf, state.streaming_field)
        if partial_text is not None and len(partial_text) > state.text_emitted_len:
            delta = partial_text[state.text_emitted_len:]
            state.text_emitted_len = len(partial_text)
            events.append({
                "event_type": "node_text_delta",
                "id": state.current_id,
                "delta": delta,
            })

    return events


class PresentationPlanner:
    """
    Transforms a final drafted text (and its CuratedContext) into a structured 
    PresentationModel JSON array that the Flutter frontend will render natively.
    """
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def plan_layout(self, query: str, context: CuratedContext, context_messages: list[dict] | None = None) -> list[dict[str, Any]]:
        """
        Step 1: Decide the UI structure first based on the query and curated context.
        Returns a list of node schemas with just 'id', 'type', and 'purpose', NO CONTENT.
        """
        memory_context = ""
        if context_messages and len(context_messages) > 0 and context_messages[0].get("role") == "system":
            sys_content = context_messages[0].get("content", "")
            if "=== RELEVANT MEMORIES ===" in sys_content:
                memory_parts = sys_content.split("=== RELEVANT MEMORIES ===")
                if len(memory_parts) > 1:
                    memory_context = "=== RELEVANT MEMORIES ===" + memory_parts[1].split("===")[0]

        prompt = f"""You are a UI Layout Designer. Decide the best visual layout for the user's query based on the Curated Context.
DO NOT generate the actual text/content yet. Only generate the structural blueprint.

{memory_context}

User Query: {query}

Curated Context Summary:
{context.summary}

Distinct Facts/Stories:
{json.dumps(context.merged_facts, indent=2)}

Available Node Types:
- Heading
- Paragraph
- BulletList
- NumberedList
- NewsCard
- WeatherCard
- ComparisonTable
- CodeBlock
- ImageGallery
- Timeline
- Accordion

Available Images:
{json.dumps([{"url": img.url, "alt": img.alt_text} for img in context.curated_images], indent=2)}

Return ONLY a JSON array of objects. EVERY object must have:
- 'id': unique string
- 'type': exact type from the list above
- 'purpose': brief instruction on what this node will contain (e.g. "Main title", "Compare speed and cost")

CRITICAL INSTRUCTION: If you use a rich card (like WeatherCard or NewsCard), you MUST also include a 'Paragraph' node either before or after it to provide a conversational, descriptive brief to the user.
CRITICAL INSTRUCTION FOR NEWS: If the user specifically asked for news or current events, and the context contains multiple distinct news stories, you MUST generate a separate NewsCard for EACH distinct story. If the user did NOT ask for news, DO NOT output NewsCards, even if news stories are present in the context!
CRITICAL INSTRUCTION FOR IMAGES: If "Available Images" is empty, you are STRICTLY FORBIDDEN from generating an 'ImageGallery' node! If it is not empty, you MUST include an 'ImageGallery' node.
CRITICAL INSTRUCTION FOR COMPARISON: If the user asks to compare entities or options, you MUST include a 'ComparisonTable' node.
ImageGallery Layout Heuristics:
- Use 'bento' layout for: Single famous person/place/product, Introduction to one topic (acts as a visual cover page). Requires at least 4 images.
- Use 'carousel' layout for: User browsing options, Comparing multiple entities, Explaining a process, Visual inspiration.

Example:
[
  {{"id": "h1", "type": "Heading", "purpose": "Main title summarizing the topic"}},
  {{"id": "t1", "type": "ComparisonTable", "purpose": "Compare Framework A and Framework B"}}
]
"""
        messages = [
            {"role": "system", "content": "You are a UI Layout Designer outputting ONLY a JSON array."},
            {"role": "user", "content": prompt}
        ]

        try:
            import typing
            from app.services.ai.providers.router import ProviderRouter
            router_inst = typing.cast(ProviderRouter, self.provider)
            
            result = await router_inst.chat(messages, intent="structured")
            start = result.find("[")
            end = result.rfind("]") + 1
            if start != -1 and end != -1:
                layout_raw = json.loads(result[start:end])
                if isinstance(layout_raw, list):
                    layout = [n for n in layout_raw if isinstance(n, dict)]
                    layout = _hoist_image_gallery(layout)
                    logger.info(f"[PresentationPlanner] Designed layout with {len(layout)} nodes.")
                    return layout
        except Exception as e:
            logger.warning(f"[PresentationPlanner] Failed to plan layout: {str(e)}")
            
        fallback: list[dict[str, Any]] = [{"id": "fallback_1", "type": "Paragraph", "purpose": "Display raw response"}]
        return fallback

    async def generate_content(self, query: str, layout: list[dict[str, Any]], context: CuratedContext, context_messages: list[dict] | None = None) -> list[dict[str, Any]]:
        """
        Step 2: Generate the content to perfectly fit the decided UI layout.
        """
        memory_context = ""
        if context_messages and len(context_messages) > 0 and context_messages[0].get("role") == "system":
            sys_content = context_messages[0].get("content", "")
            if "=== RELEVANT MEMORIES ===" in sys_content:
                memory_parts = sys_content.split("=== RELEVANT MEMORIES ===")
                if len(memory_parts) > 1:
                    memory_context = "=== RELEVANT MEMORIES ===" + memory_parts[1].split("===")[0]
                    
        prompt = f"""You are a UI Content Writer. Your job is to fill in the exact content for a predefined UI Layout.
You must use the Curated Context to populate the fields. DO NOT invent facts.

{memory_context}

Curated Context Summary & Facts:
{json.dumps(context.model_dump(exclude={'raw_data'}), indent=2)}

Raw Tool Data (Use this for precise arrays, charts, forecasts, etc):
{json.dumps(context.raw_data, indent=2)}

Predefined UI Layout:
{json.dumps(layout, indent=2)}

Node Field Requirements:
- Heading: 'id', 'type', 'text', 'level' (1, 2, or 3)
- Paragraph: 'id', 'type', 'text'
- BulletList: 'id', 'type', 'items' (array of strings)
- NumberedList: 'id', 'type', 'items' (array of strings)
- NewsCard: 'id', 'type', 'title', 'summary' (Write a clean, detailed 3-4 sentence paragraph summary based on the snippet. DO NOT copy raw navigation text, menus, or garbage text), 'source', 'url' (required - use the real article URL from raw data), 'imageUrl' (use og:image URL from raw data if available, else omit), 'imageUrls' (array of strings - pass the imageUrls list from raw data exactly if available), 'category' (e.g. "Technology", "Business" - infer from content), 'publishedAt' (if available from raw data)
- IMPORTANT for NewsCard: Always populate 'url' and 'source' from the raw news_search article data. Use 'imageUrl' and 'imageUrls' from the article's data. Do NOT invent URLs.
- WeatherCard: 'id', 'type', 'location', 'temperature_c', 'condition', 'forecast' (array of {{day, condition, high, low, hourly: array of {{time, temp}}}})
- ComparisonTable: 'id', 'type', 'headers' (array), 'rows' (array of arrays)
- CodeBlock: 'id', 'type', 'language', 'code'
- ImageGallery: 'id', 'type', 'layout' ('bento' or 'carousel'), 'images' (array of {{url, alt}})
- Timeline: 'id', 'type', 'events' (array of {{time, title, description}})
- Accordion: 'id', 'type', 'title', 'content'

Return ONLY a JSON array containing the fully populated nodes from the Predefined UI Layout. Do not change the IDs or Types.
"""
        messages = [
            {"role": "system", "content": "You are a UI Content Writer outputting ONLY a populated JSON array."},
            {"role": "user", "content": prompt}
        ]

        try:
            import typing
            from app.services.ai.providers.router import ProviderRouter
            router_inst = typing.cast(ProviderRouter, self.provider)
            
            result = await router_inst.chat(messages, intent="structured")
            start = result.find("[")
            end = result.rfind("]") + 1
            if start != -1 and end != -1:
                nodes_raw = json.loads(result[start:end])
                
                # If LLM returns a single object instead of an array, wrap it in a list
                if isinstance(nodes_raw, dict):
                    nodes_raw = [nodes_raw]
                    
                if isinstance(nodes_raw, list):
                    nodes = [n for n in nodes_raw if isinstance(n, dict)]
                else:
                    nodes = []
                    
                # Post-process: inject exact raw data for complex cards
                articles = _build_news_index(context.raw_data) if context.raw_data else []
                
                for node in nodes:
                    if node.get("type") == "NewsCard":
                        _match_and_inject_article(node, articles)
                    elif node.get("type") == "WeatherCard" and context.raw_data:
                        weather_data = context.raw_data.get("get_weather", {})
                        if weather_data:
                            node["location"] = weather_data.get("location", node.get("location"))
                            
                            # Extract current temperature/condition from nested dict if present
                            current_data = weather_data.get("current", {})
                            if "temperature" in current_data:
                                # try to extract number from "32°C"
                                import re
                                temp_str = str(current_data["temperature"])
                                match = re.search(r'-?\d+(?:\.\d+)?', temp_str)
                                if match:
                                    try:
                                        node["temperature_c"] = float(match.group(0))
                                    except ValueError:
                                        node["temperature_c"] = temp_str
                                else:
                                    node["temperature_c"] = temp_str
                            if "condition" in current_data:
                                node["condition"] = current_data["condition"]
                                
                            # The raw tool outputs "forecast_7_days" but UI expects "forecast"
                            if "forecast_7_days" in weather_data:
                                node["forecast"] = weather_data["forecast_7_days"]
                            
                logger.info(f"[PresentationPlanner] Populated content for {len(nodes)} nodes.")
                return nodes
        except Exception as e:
            logger.warning(f"[PresentationPlanner] Failed to generate content: {str(e)}")
            
        fallback: list[dict[str, Any]] = [
            {
                "id": "fallback_1",
                "type": "Paragraph",
                "text": "Failed to format content. Check curated context."
            }
        ]
        return fallback

    async def generate_content_stream(self, query: str, layout: list[dict[str, Any]], context: CuratedContext, context_messages: list[dict] | None = None) -> typing.AsyncGenerator[dict[str, Any], None]:
        """
        Step 2 (Streaming): Generates content progressively and yields each PresentationNode as soon as it is complete.
        """
        memory_context = ""
        if context_messages and len(context_messages) > 0 and context_messages[0].get("role") == "system":
            sys_content = context_messages[0].get("content", "")
            if "=== RELEVANT MEMORIES ===" in sys_content:
                memory_parts = sys_content.split("=== RELEVANT MEMORIES ===")
                if len(memory_parts) > 1:
                    memory_context = "=== RELEVANT MEMORIES ===" + memory_parts[1].split("===")[0]
                    
        prompt = f"""You are a UI Content Writer. Your job is to fill in the exact content for a predefined UI Layout.
You must use the Curated Context to populate the fields. DO NOT invent facts.

{memory_context}

Curated Context Summary & Facts:
{json.dumps(context.model_dump(exclude={'raw_data'}), indent=2)}

Raw Tool Data (Use this for precise arrays, charts, forecasts, etc):
{json.dumps(context.raw_data, indent=2)}

Predefined UI Layout:
{json.dumps(layout, indent=2)}

Node Field Requirements (CRITICAL: You MUST output 'id' and 'type' FIRST, before any other fields like 'text', to allow proper streaming):
- Heading: 'id', 'type', 'text', 'level' (1, 2, or 3)
- Paragraph: 'id', 'type', 'text'
- BulletList: 'id', 'type', 'items' (array of strings)
- NumberedList: 'id', 'type', 'items' (array of strings)
- NewsCard: 'id', 'type', 'title', 'summary' (Write a clean, detailed 3-4 sentence paragraph summary based on the snippet. DO NOT copy raw navigation text, menus, or garbage text), 'source', 'url' (required - use the real article URL from raw data), 'imageUrl' (use og:image URL from raw data if available, else omit), 'imageUrls' (array of strings - pass the imageUrls list from raw data exactly if available), 'category' (e.g. "Technology", "Business" - infer from content), 'publishedAt' (if available from raw data)
- IMPORTANT for NewsCard: Always populate 'url' and 'source' from the raw news_search article data. Use 'imageUrl' and 'imageUrls' from the article's data. Do NOT invent URLs.
- WeatherCard: 'id', 'type', 'location', 'temperature_c', 'condition', 'forecast' (array of {{day, condition, high, low, hourly: array of {{time, temp}}}})
- ComparisonTable: 'id', 'type', 'headers' (array), 'rows' (array of arrays)
- CodeBlock: 'id', 'type', 'language', 'code'
- ImageGallery: 'id', 'type', 'layout' ('bento' or 'carousel'), 'images' (array of {{url, alt}})
- Timeline: 'id', 'type', 'events' (array of {{time, title, description}})
- Accordion: 'id', 'type', 'title', 'content'

Return ONLY a JSON array containing the fully populated nodes from the Predefined UI Layout. Do not change the IDs or Types.
"""
        messages = [
            {"role": "system", "content": "You are a UI Content Writer outputting ONLY a populated JSON array."},
            {"role": "user", "content": prompt}
        ]

        from app.services.ai.planner.json_streamer import parse_json_objects_from_stream
        import typing
        from app.services.ai.providers.router import ProviderRouter
        
        try:
            router_inst = typing.cast(ProviderRouter, self.provider)
            buffer = ""
            articles_for_stream = _build_news_index(context.raw_data) if context.raw_data else []
            state = _StreamPartialState()

            async for chunk in router_inst.stream_chat(messages, intent="structured"):
                new_events = _extract_partial_events(buffer + chunk, state)
                for event in new_events:
                    yield event

                buffer += chunk
                objects, buffer = parse_json_objects_from_stream(buffer)

                for node in objects:
                    if not isinstance(node, dict):
                        continue

                    if node.get("type") == "NewsCard":
                        _match_and_inject_article(node, articles_for_stream)

                    elif node.get("type") == "WeatherCard" and context.raw_data:
                        weather_data = context.raw_data.get("get_weather", {})
                        if weather_data:
                            node["location"] = weather_data.get("location", node.get("location"))
                            
                            current_data = weather_data.get("current", {})
                            if "temperature" in current_data:
                                import re
                                temp_str = str(current_data["temperature"])
                                match = re.search(r'-?\d+(?:\.\d+)?', temp_str)
                                if match:
                                    try:
                                        node["temperature_c"] = float(match.group(0))
                                    except ValueError:
                                        node["temperature_c"] = temp_str
                                else:
                                    node["temperature_c"] = temp_str
                            if "condition" in current_data:
                                node["condition"] = current_data["condition"]
                                
                            if "forecast_7_days" in weather_data:
                                node["forecast"] = weather_data["forecast_7_days"]
                                
                    yield {"event_type": "presentation_node", "node": node}
                    state.reset()
                    
        except Exception as e:
            logger.warning(f"[PresentationPlanner] Failed to generate content stream: {str(e)}")
            fallback: dict[str, Any] = {
                "id": "fallback_1",
                "type": "Paragraph",
                "text": "Failed to format content progressively. Check curated context."
            }
            yield {"event_type": "presentation_node", "node": fallback}


