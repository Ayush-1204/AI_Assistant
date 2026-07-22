import json
import logging
import time
import asyncio
import httpx

from app.config import get_settings
from app.integrations.search.base import SearchProvider
from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

class WebSearchTool(BaseTool):
    def __init__(self, provider: SearchProvider):
        self.provider = provider
        self.settings = get_settings()

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web for up-to-date and reliable information that is not available in memory or local context (e.g., current events, weather, stock prices, latest news etc). IMPORTANT: This tool also returns a list of REAL image URLs matching the query. You MUST use this tool if the user asks for pictures or images of real-world people, places, or entities!"

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up on the web"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of search results to return",
                    "default": self.settings.default_max_results
                }
            },
            "required": ["query"]
        }

    async def _is_url_valid(self, url: str) -> bool:
        """Asynchronously validates if a URL is alive and returns an image."""
        if "wikimedia" in url.lower() or "wikipedia" in url.lower():
            # Explicitly drop wikimedia hotlinks due to strict CORS bounds protecting the proxy
            return False
            
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.head(url, follow_redirects=True)
                if response.status_code == 200:
                    content_type = response.headers.get("Content-Type", "")
                    if content_type.startswith("image/"):
                        return True
                        
                # Head requests may be blocked; fallback to testing GET streams
                if response.status_code in [403, 404, 405, 500]:
                    response_get = await client.get(url, follow_redirects=True)
                    if response_get.status_code == 200 and response_get.headers.get("Content-Type", "").startswith("image/"):
                        return True
        except Exception:
            pass
        return False

    async def execute(self, execution_context: dict, **kwargs) -> str:
        query = kwargs.get("query")
        if not query:
            return json.dumps({"error": "Missing 'query' parameter"})
            
        max_results = kwargs.get("max_results", self.settings.default_max_results)
        
        try:
            start_time = time.perf_counter()
            results, images = await self.provider.search(query, max_results=max_results)
            latency = (time.perf_counter() - start_time) * 1000.0
            
            logger.info(
                "Web search execute success", 
                extra={
                    "provider": self.provider.name,
                    "query": query, 
                    "result_count": len(results),
                    "latency_ms": latency
                }
            )
            
            if not results and not images:
                return json.dumps({"message": "No relevant search results found."})
                
            formatted_results = []
            for r in results:
                formatted_results.append({
                    "title": r.title,
                    "url": str(r.url),
                    "snippet": r.snippet
                })
                
            validation_tasks = [self._is_url_valid(img) for img in images]
            validation_results = await asyncio.gather(*validation_tasks)
            
            valid_images = [
                img for img, is_valid in zip(images, validation_results)
                if is_valid
            ]
            
            return json.dumps({
                "results": formatted_results, 
                "images": valid_images[:10]  # Cap at 10 strictly to preserve LLM token bounds
            })
            
        except Exception as e:
            logger.error(f"Web search failed gracefully: {str(e)}")
            return json.dumps({"error": f"Search failed: {str(e)}"})
