import json
import logging
import urllib.parse
from typing import Any
import httpx

from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

class SemanticScholarTool(BaseTool):
    """
    Searches Semantic Scholar for academic papers and their citation counts.
    """

    def __init__(self):
        super().__init__()

    @property
    def name(self) -> str:
        return "semantic_scholar"

    @property
    def description(self) -> str:
        return (
            "Searches Semantic Scholar for scientific literature across all domains. "
            "Returns papers with their citation counts, publication year, authors, and abstract. "
            "Use this for literature reviews or to find highly cited foundational papers."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query (e.g., 'attention is all you need', 'cancer immunotherapy')."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of papers to retrieve (default is 5, max 10).",
                    "default": 5
                }
            },
            "required": ["query"]
        }

    async def execute(self, execution_context: dict, **kwargs) -> Any:
        query = kwargs.get("query")
        if not query:
            return "Error: 'query' parameter is required."
            
        max_results = min(kwargs.get("max_results", 5), 10)

        try:
            headers = {"User-Agent": "AntigravityPersonalAssistant/1.0 (https://github.com; contact@example.com)"}
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit={max_results}&fields=title,authors,abstract,year,citationCount,url"
                import asyncio
                
                max_retries = 3
                for attempt in range(max_retries):
                    response = await client.get(url)
                    if response.status_code == 429:
                        if attempt < max_retries - 1:
                            logger.warning(f"Semantic Scholar API rate limited. Retrying in 2 seconds... (Attempt {attempt+1}/{max_retries})")
                            await asyncio.sleep(2)
                            continue
                        else:
                            return "Semantic Scholar API rate limit exceeded. Please try again later."
                    
                    response.raise_for_status()
                    data = response.json()
                    break
                
                papers = data.get("data", [])
                if not papers:
                    return f"No Semantic Scholar papers found for '{query}'."
                
                results = []
                for paper in papers:
                    authors = [author.get("name") for author in paper.get("authors", [])]
                    results.append({
                        "title": paper.get("title"),
                        "year": paper.get("year"),
                        "citations": paper.get("citationCount"),
                        "authors": authors,
                        "abstract": paper.get("abstract"),
                        "url": paper.get("url")
                    })
                    
                return json.dumps(results)

        except Exception as e:
            logger.error(f"[SemanticScholarTool] Request failed: {str(e)}")
            return f"Error executing Semantic Scholar search: {str(e)}"
