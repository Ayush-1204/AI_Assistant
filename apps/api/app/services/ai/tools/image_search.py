import logging
import urllib.parse
from typing import Any
import httpx

from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

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
            "Look up a verified image URL for a specific person, place, or thing. "
            "ALWAYS use this tool when you need to include an image in your response. "
            "Returns a verified image URL that is guaranteed to load properly."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The specific entity, event, or concept to search for an image of."
                }
            },
            "required": ["query"]
        }

    async def execute(self, execution_context: dict, **kwargs) -> Any:
        query = kwargs.get("query")
        if not query:
            return "Error: 'query' parameter is required."

        try:
            # We use Wikipedia's API to fetch the primary page image, which is highly reliable.
            headers = {"User-Agent": "AntigravityPersonalAssistant/1.0 (contact@example.com)"}
            async with httpx.AsyncClient(timeout=10.0, headers=headers, follow_redirects=True) as client:
                
                # 1. Search to resolve the exact title
                search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json&srlimit=1"
                search_resp = await client.get(search_url)
                search_resp.raise_for_status()
                
                search_data = search_resp.json()
                results = search_data.get("query", {}).get("search", [])
                
                if not results:
                    return f"No image found for '{query}'."
                    
                title = results[0]["title"]
                
                # 2. Get the page image
                image_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(title)}&prop=pageimages&format=json&pithumbsize=800"
                image_resp = await client.get(image_url)
                image_resp.raise_for_status()
                
                image_data = image_resp.json()
                pages = image_data.get("query", {}).get("pages", {})
                
                for page_id, page_info in pages.items():
                    if "thumbnail" in page_info:
                        img_source = page_info["thumbnail"]["source"]
                        
                        # 3. Verify the image actually exists and is reachable
                        head_resp = await client.head(img_source)
                        if head_resp.status_code == 200 and head_resp.headers.get("Content-Type", "").startswith("image/"):
                            # Wrap in our local proxy to completely bypass Wikipedia's strict CORS/hotlinking restrictions!
                            proxied_url = f"http://127.0.0.1:8000/media/proxy?url={urllib.parse.quote(img_source, safe='')}"
                            return f"Verified Image URL for {title}: {proxied_url}\nUse Markdown to render this: `![{title}]({proxied_url})`"
                        
                return f"No verified image could be retrieved for '{title}'."

        except Exception as e:
            logger.error(f"Error executing ImageSearchTool: {str(e)}", exc_info=True)
            return f"Error executing image search: {str(e)}"
