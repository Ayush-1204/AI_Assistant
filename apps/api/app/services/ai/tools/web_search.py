import json
import logging
import time

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
        return "Search the web for up-to-date and reliable information that is not available in memory or local context (e.g., current events, weather, stock prices, latest news etc)."

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

    async def execute(self, execution_context: dict, **kwargs) -> str:
        query = kwargs.get("query")
        if not query:
            return json.dumps({"error": "Missing 'query' parameter"})
            
        max_results = kwargs.get("max_results", self.settings.default_max_results)
        
        try:
            start_time = time.perf_counter()
            results = await self.provider.search(query, max_results=max_results)
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
            
            if not results:
                return json.dumps({"message": "No relevant search results found."})
                
            formatted_results = []
            for r in results:
                formatted_results.append({
                    "title": r.title,
                    "url": str(r.url),
                    "snippet": r.snippet
                })
                
            return json.dumps({"results": formatted_results})
            
        except Exception as e:
            logger.error(f"Web search failed gracefully: {str(e)}")
            return json.dumps({"error": f"Search failed: {str(e)}"})
