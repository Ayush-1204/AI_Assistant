import json
import logging
import urllib.parse
from typing import Any
import httpx

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
            headers = {"User-Agent": "AntigravityPersonalAssistant/1.0 (https://github.com; contact@example.com)"}
            async with httpx.AsyncClient(timeout=5.0, headers=headers) as client:
                # 1. Search to resolve the exact title
                search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json&srlimit=1"
                search_resp = await client.get(search_url)
                search_resp.raise_for_status()
                search_data = search_resp.json()
                
                results = search_data.get("query", {}).get("search", [])
                if not results:
                    return f"No Wikipedia results found for '{query}'."
                
                title = results[0]["title"]
                
                # 2. Get the clean summary via REST API
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
                summary_resp = await client.get(summary_url)
                summary_resp.raise_for_status()
                summary_data = summary_resp.json()
                
                extract = summary_data.get("extract", "")
                url = summary_data.get("content_urls", {}).get("desktop", {}).get("page", "")
                
                return json.dumps({
                    "title": title,
                    "summary": extract,
                    "url": url
                })

        except Exception as e:
            logger.error(f"[WikipediaTool] Request failed: {str(e)}")
            return f"Error executing Wikipedia search: {str(e)}"
