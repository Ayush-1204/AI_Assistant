import json
import logging
import urllib.parse
from typing import Any
import httpx
from datetime import datetime

from app.schemas.ai_pipeline import NormalizedToolResult, ImageReference
from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

class WikipediaTool(BaseTool):
    """
    Retrieves precise factual summaries from Wikipedia.
    """

    def __init__(self):
        super().__init__()

    @property
    def name(self) -> str:
        return "wikipedia"

    @property
    def description(self) -> str:
        return (
            "Look up factual, objective information about people, places, historical events, "
            "and established concepts using Wikipedia. This is much faster and less prone to "
            "hallucination than a full web search for basic facts."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The specific entity, event, or concept to search for on Wikipedia."
                }
            },
            "required": ["query"]
        }

    async def execute(self, execution_context: dict, **kwargs) -> Any:
        query = kwargs.get("query")
        if not query:
            return "Error: 'query' parameter is required."

        try:
            import asyncio
            headers = {"User-Agent": "AntigravityBot/2.0 (https://github.com/google-deepmind; contact-bot@antigravity.local)"}
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                search_data = None
                for attempt in range(3):
                    # 1. Search to resolve the exact title
                    search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json&srlimit=1"
                    search_resp = await client.get(search_url)
                    
                    if search_resp.status_code == 429:
                        retry_after = int(search_resp.headers.get("Retry-After", 2))
                        await asyncio.sleep(retry_after)
                        continue
                        
                    search_resp.raise_for_status()
                    search_data = search_resp.json()
                    break
                    
                if not search_data:
                    return f"Error executing Wikipedia search: Rate limited after multiple retries."
                
                results = search_data.get("query", {}).get("search", [])
                if not results:
                    return f"No Wikipedia results found for '{query}'."
                
                title = results[0]["title"]
                
                
                # 2. Get the clean summary via REST API
                summary_data = None
                for attempt in range(3):
                    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
                    summary_resp = await client.get(summary_url)
                    
                    if summary_resp.status_code == 429:
                        retry_after = int(summary_resp.headers.get("Retry-After", 2))
                        await asyncio.sleep(retry_after)
                        continue
                        
                    summary_resp.raise_for_status()
                    summary_data = summary_resp.json()
                    break
                    
                if not summary_data:
                    return f"Error executing Wikipedia search: Rate limited while fetching summary."
                
                extract = summary_data.get("extract", "")
                url = summary_data.get("content_urls", {}).get("desktop", {}).get("page", "")
                thumbnail = summary_data.get("thumbnail", {}).get("source", "")
                
                data = {
                    "title": title,
                    "summary": extract,
                    "url": url,
                    "imageUrl": thumbnail
                }
                
                images = []
                if thumbnail:
                    images.append(ImageReference(url=thumbnail, alt_text=title))

                # Fetch supplementary images to enable Bento layouts (which require >= 4 images)
                try:
                    from ddgs import DDGS
                    import asyncio
                    def _fetch_supp():
                        with DDGS() as ddgs:
                            return list(ddgs.images(title, max_results=3))
                    results = await asyncio.to_thread(_fetch_supp)
                    for r in results:
                        img_url = r.get("image")
                        if img_url and isinstance(img_url, str) and "1x1" not in img_url:
                            images.append(ImageReference(url=img_url, alt_text=r.get("title", title)))
                except Exception as e:
                    logger.debug(f"[WikipediaTool] DDGS supplementary images failed for {title}: {e}")

                return NormalizedToolResult(
                    tool_name=self.name,
                    source="Wikipedia",
                    timestamp=datetime.now(),
                    confidence=1.0,
                    rawData=json.dumps(data),
                    normalizedData={"content": json.dumps(data)},
                    images=images
                )

        except Exception as e:
            logger.error(f"[WikipediaTool] Request failed: {str(e)}")
            return f"Error executing Wikipedia search: {str(e)}"
