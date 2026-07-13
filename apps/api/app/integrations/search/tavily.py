import logging

import httpx

from app.config import get_settings
from app.integrations.search.base import SearchProvider
from app.schemas.search import SearchResult

logger = logging.getLogger(__name__)

class TavilySearchProvider(SearchProvider):
    def __init__(self, api_key: str | None = None):
        self.settings = get_settings()
        self.api_key = api_key or self.settings.TAVILY_API_KEY
        if not self.api_key:
            logger.warning("Tavily API key is missing. Web search will fail.")
        else:
            logger.debug("Tavily API key configured (key present).")
            
        self.base_url = "https://api.tavily.com/search"
        self.timeout = self.settings.search_timeout

    @property
    def name(self) -> str:
        return "tavily"

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self.api_key:
            raise ValueError("Tavily API key not configured")
            
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "include_images": False,
            "include_raw_content": False,
            "max_results": max_results,
            "include_domains": [],
            "exclude_domains": []
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(self.base_url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("results", []):
                    results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            snippet=item.get("content", "")
                        )
                    )
                return results
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Tavily search API error [{e.response.status_code}]: {e.response.text}")
                raise RuntimeError(f"Search provider error: {e.response.status_code}") from e
            except httpx.RequestError as e:
                logger.error(f"Tavily search request failed: {repr(e)}")
                raise RuntimeError(f"Search provider connection error: {repr(e)}") from e
            except Exception as e:
                logger.error(f"Unexpected error in Tavily search: {repr(e)}")
                raise RuntimeError("Search execution failed dynamically") from e

