import json
import logging
import uuid
from typing import Any

from app.schemas.ai_pipeline import CuratedContext
from app.services.ai.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

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
- NewsCard: 'id', 'type', 'title', 'summary', 'source', 'url' (optional), 'imageUrl' (optional)
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
                
                # Post-process to inject exact raw data for complex cards to prevent LLM truncation
                for node in nodes:
                    if node.get("type") == "WeatherCard" and context.raw_data:
                        weather_data = context.raw_data.get("get_weather", {})
                        if weather_data:
                            node["location"] = weather_data.get("location", node.get("location"))
                            node["temperature_c"] = weather_data.get("temperature_c", node.get("temperature_c"))
                            node["condition"] = weather_data.get("condition", node.get("condition"))
                            node["forecast"] = weather_data.get("forecast", node.get("forecast"))
                            
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


