import logging
import urllib.parse
from typing import Any
import httpx

from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

import asyncio

class ImageSearchTool(BaseTool):
    """
    Searches for a verified image URL for a given entity or concept.
    """

    def __init__(self):
        super().__init__()

    @property
    def name(self) -> str:
        return "image_search"

    @property
    def description(self) -> str:
        return (
            "Look up highly relevant images for a specific person, place, thing, or concept. "
            "ALWAYS use this tool when you need to include images in your response or illustrate a process (like recipe steps). "
            "Returns up to 6 verified image URLs formatted as Markdown."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The specific entity, event, or concept to search for images of."
                },
                "count": {
                    "type": "integer",
                    "description": "Number of images to return. Use 1 for inline step-by-step images. Use up to 6 to generate an image gallery for a topic.",
                    "default": 1
                }
            },
            "required": ["query"]
        }

    async def _check_valid(self, img: str) -> str | None:
        if "wikimedia" in img.lower() or "wikipedia" in img.lower() or "unsplash" in img.lower():
            return None
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.head(img, follow_redirects=True)
                if response.status_code == 200 and response.headers.get("Content-Type", "").startswith("image/"):
                    return img
                if response.status_code in [403, 404, 405, 500]:
                    response_get = await client.get(img, follow_redirects=True)
                    if response_get.status_code == 200 and response_get.headers.get("Content-Type", "").startswith("image/"):
                        return img
        except Exception:
            pass
        return None

    async def execute(self, execution_context: dict, **kwargs) -> Any:
        query = kwargs.get("query")
        if not query:
            return "Error: 'query' parameter is required."
            
        count = kwargs.get("count", 1)
        try:
            count = int(count)
        except ValueError:
            count = 1
        count = max(1, min(6, count))

        try:
            from app.integrations.search.tavily import TavilySearchProvider
            provider = TavilySearchProvider()
            
            results, images = await provider.search(query, max_results=5)
            
            if not images:
                return f"No images found for '{query}'."
                
            tasks = [self._check_valid(img) for img in images[:15]]
            checked = await asyncio.gather(*tasks)
            valid_images = [img for img in checked if img is not None]
            
            if not valid_images:
                return f"No verified images could be retrieved for '{query}'."
                
            markdown_str = "\\n".join([f"![{query}]({img})" for img in valid_images[:count]])
            return f"Successfully retrieved {len(valid_images[:count])} images for '{query}'.\\nUse Markdown to render these exactly as provided:\\n{markdown_str}"

        except Exception as e:
            logger.error(f"Error executing ImageSearchTool: {str(e)}", exc_info=True)
            return f"Error executing image search: {str(e)}"
