import json
import logging
import re
import uuid
from typing import Any

from app.schemas.ai_pipeline import CuratedContext
from app.services.ai.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


def _build_news_index(raw_data: dict) -> list[dict]:
    """Extracts the article list from raw news_search tool data."""
    news_raw = raw_data.get("news_search", {})
    if isinstance(news_raw, str):
        try:
            news_raw = json.loads(news_raw)
        except Exception:
            return []
    return news_raw.get("articles", [])


def _inject_news_data(node: dict, articles: list[dict]) -> dict:
    """
    Matches a NewsCard node to the closest article by title similarity
    and overwrites url / imageUrl with the exact values from raw data.
    """
    if not articles:
        return node

    node_title = node.get("title", "").lower().strip()

    best_article = None
    best_score = 0

    for article in articles:
        article_title = article.get("title", "").lower().strip()
        # Count common words (simple overlap score)
        node_words = set(node_title.split())
        art_words = set(article_title.split())
        score = len(node_words & art_words)
        if score > best_score:
            best_score = score
            best_article = article

    # Fallback: use first article if no title match
    if best_article is None:
        best_article = articles[0]

    # Always overwrite with exact raw data — never trust LLM for URLs
    exact_url = best_article.get("url", "")
    if exact_url:
        node["url"] = exact_url

    og_image = best_article.get("imageUrl")
    if og_image:
        node["imageUrl"] = og_image
    else:
        node.pop("imageUrl", None)  # remove if LLM hallucinated one

    if not node.get("source"):
        node["source"] = best_article.get("source", "")

    return node


class PresentationPlanner:
    """
    Transforms a final drafted text (and its CuratedContext) into a structured 
    PresentationModel JSON array that the Flutter frontend will render natively.
    """
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def plan_layout(self, query: str, context: CuratedContext) -> list[dict[str, Any]]:
        """
        Step 1: Decide the UI structure first based on the query and curated context.
        Returns a list of node schemas with just 'id', 'type', and 'purpose', NO CONTENT.
        """
        prompt = f"""You are a UI Layout Designer. Decide the best visual layout for the user's query based on the Curated Context.
DO NOT generate the actual text/content yet. Only generate the structural blueprint.

User Query: {query}

Curated Context Summary:
{context.summary}

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

Return ONLY a JSON array of objects. EVERY object must have:
- 'id': unique string
- 'type': exact type from the list above
- 'purpose': brief instruction on what this node will contain (e.g. "Main title", "Compare speed and cost")

CRITICAL INSTRUCTION: If you use a rich card (like WeatherCard or NewsCard), you MUST also include a 'Paragraph' node either before or after it to provide a conversational, descriptive brief to the user.

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
                layout = json.loads(result[start:end])
                logger.info(f"[PresentationPlanner] Designed layout with {len(layout)} nodes.")
                return layout
        except Exception as e:
            logger.warning(f"[PresentationPlanner] Failed to plan layout: {str(e)}")
            
        return [{"id": "fallback_1", "type": "Paragraph", "purpose": "Display raw response"}]

    async def generate_content(self, query: str, layout: list[dict[str, Any]], context: CuratedContext) -> list[dict[str, Any]]:
        """
        Step 2: Generate the content to perfectly fit the decided UI layout.
        """
        prompt = f"""You are a UI Content Writer. Your job is to fill in the exact content for a predefined UI Layout.
You must use the Curated Context to populate the fields. DO NOT invent facts.

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
- NewsCard: 'id', 'type', 'title', 'summary', 'source', 'url' (required - use the real article URL from raw data), 'imageUrl' (use og:image URL from raw data if available, else omit), 'category' (e.g. "Technology", "Business" - infer from content), 'publishedAt' (if available from raw data)
- IMPORTANT for NewsCard: Always populate 'url' and 'source' from the raw news_search article data. Use 'imageUrl' from the article's imageUrl field. Do NOT invent URLs.
- WeatherCard: 'id', 'type', 'location', 'temperature_c', 'condition', 'forecast' (array of {{day, condition, high, low, hourly: array of {{time, temp}}}})
- ComparisonTable: 'id', 'type', 'headers' (array), 'rows' (array of arrays)
- CodeBlock: 'id', 'type', 'language', 'code'
- ImageGallery: 'id', 'type', 'images' (array of {{url, alt}})
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
                nodes = json.loads(result[start:end])
                
                # If LLM returns a single object instead of an array, wrap it in a list
                if isinstance(nodes, dict):
                    nodes = [nodes]
                    
                # Post-process to inject exact raw data for complex cards to prevent LLM truncation
                articles = _build_news_index(context.raw_data) if context.raw_data else []
                for node in nodes:
                    if not isinstance(node, dict):
                        continue

                    if node.get("type") == "NewsCard":
                        node = _inject_news_data(node, articles)

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
            
        return [
            {
                "id": "fallback_1",
                "type": "Paragraph",
                "text": "Failed to format content. Check curated context."
            }
        ]

    async def generate_content_stream(self, query: str, layout: list[dict[str, Any]], context: CuratedContext):
        """
        Step 2 (Streaming): Generates content progressively and yields each PresentationNode as soon as it is complete.
        """
        prompt = f"""You are a UI Content Writer. Your job is to fill in the exact content for a predefined UI Layout.
You must use the Curated Context to populate the fields. DO NOT invent facts.

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
- NewsCard: 'id', 'type', 'title', 'summary', 'source', 'url' (required - use the real article URL from raw data), 'imageUrl' (use og:image URL from raw data if available, else omit), 'category' (e.g. "Technology", "Business" - infer from content), 'publishedAt' (if available from raw data)
- IMPORTANT for NewsCard: Always populate 'url' and 'source' from the raw news_search article data. Use 'imageUrl' from the article's imageUrl field. Do NOT invent URLs.
- WeatherCard: 'id', 'type', 'location', 'temperature_c', 'condition', 'forecast' (array of {{day, condition, high, low, hourly: array of {{time, temp}}}})
- ComparisonTable: 'id', 'type', 'headers' (array), 'rows' (array of arrays)
- CodeBlock: 'id', 'type', 'language', 'code'
- ImageGallery: 'id', 'type', 'images' (array of {{url, alt}})
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
            
            async for chunk in router_inst.stream_chat(messages, intent="structured"):
                buffer += chunk
                objects, buffer = parse_json_objects_from_stream(buffer)
                
                for node in objects:
                    if not isinstance(node, dict):
                        continue

                    if node.get("type") == "NewsCard" and context.raw_data:
                        articles = _build_news_index(context.raw_data)
                        node = _inject_news_data(node, articles)

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
                                
                    yield node
                    
        except Exception as e:
            logger.warning(f"[PresentationPlanner] Failed to generate content stream: {str(e)}")
            yield {
                "id": "fallback_1",
                "type": "Paragraph",
                "text": "Failed to format content progressively. Check curated context."
            }


