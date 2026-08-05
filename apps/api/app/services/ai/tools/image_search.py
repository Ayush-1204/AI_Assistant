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
                    "default": 6
                }
            },
            "required": ["query"]
        }

    async def execute(self, execution_context: dict, **kwargs) -> Any:
        query = kwargs.get("query") or kwargs.get("entity") or kwargs.get("topic") or kwargs.get("search_term")
        if not query:
            return "Error: 'query' parameter is required."
            
        count = kwargs.get("count", 6)
        try:
            count = int(count)
        except ValueError:
            count = 6
        count = max(1, min(6, count))

        try:
            from duckduckgo_search import DDGS
            
            # Run the synchronous DDGS call in a background thread to not block the event loop
            valid_images = await asyncio.to_thread(self._fetch_ddg_images, query, count)
            
            if not valid_images:
                logger.warning(f"DDGS returned 0 images for '{query}'. Falling back to Tavily.")
                from app.integrations.search.tavily import TavilySearchProvider
                provider = TavilySearchProvider()
                _, tavily_images = await provider.search(query, max_results=count)
                forbidden = ["instagram.com", "facebook.com", "fb.com", "reel", "video", "tiktok.com"]
                valid_images = [img for img in tavily_images if isinstance(img, str) and img.startswith("http") and not any(f in img.lower() for f in forbidden)]
                valid_images = valid_images[:count]
            
            if not valid_images:
                return f"No images found for '{query}'."
                
            markdown_str = "\\n".join([f"![{query}]({img})" for img in valid_images])
            
            from app.schemas.ai_pipeline import NormalizedToolResult, ImageReference
            image_refs = [
                ImageReference(url=img, alt_text=query, relevance_score=1.0)
                for img in valid_images
            ]
            
            return NormalizedToolResult(
                tool_name=self.name,
                source=self.name,
                rawData=f"Successfully retrieved {len(valid_images)} images for '{query}'.\\nUse Markdown to render these exactly as provided:\\n{markdown_str}",
                normalizedData={"content": markdown_str},
                images=image_refs
            )

        except Exception as e:
            logger.error(f"Error executing ImageSearchTool: {str(e)}", exc_info=True)
            return f"Error executing image search: {str(e)}"
            
    def _fetch_ddg_images(self, query: str, count: int) -> list[str]:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = ddgs.images(
                    query,
                    max_results=count * 3,  # Fetch a few extra just in case
                )
                
                # Filter out svg images and forbidden domains (social media/videos)
                valid_urls = []
                forbidden = ["instagram.com", "facebook.com", "fb.com", "reel", "video", "tiktok.com"]
                for res in results:
                    url = res.get("image", "")
                    if url and not url.lower().endswith(".svg") and not any(f in url.lower() for f in forbidden):
                        valid_urls.append(url)
                        if len(valid_urls) == count:
                            break
                            
                return valid_urls
        except Exception as e:
            logger.error(f"DDGS error: {e}")
            return []

