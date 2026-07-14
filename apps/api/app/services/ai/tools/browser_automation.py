import logging
import asyncio
import webbrowser
from typing import ClassVar, Dict, Any

from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

class BrowserAutomationTool(BaseTool):
    name = "browser_automation"
    description = "Automate browser interactions for the user, like opening URLs, playing YouTube, or opening Spotify web."
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Action to take. Allowed: 'open_url', 'play_youtube', 'play_spotify'.",
                "enum": ["open_url", "play_youtube", "play_spotify"]
            },
            "query": {
                "type": "string",
                "description": "The URL to open, or the search term for YouTube/Spotify."
            }
        },
        "required": ["action", "query"]
    }

    async def execute(self, execution_context: dict, **kwargs) -> Any:
        action = kwargs.get("action")
        query = kwargs.get("query")
        
        # We use sync webbrowser natively on Windows default browser without blocking thread too much
        try:
            if action == "open_url":
                if not query: return {"status": "error", "message": "query required"}
                if not query.startswith("http"):
                    query = f"https://{query}"
                webbrowser.open(query)
                return {"status": "success", "message": f"Opened {query} in default browser."}

            elif action == "play_youtube":
                if not query: return {"status": "error", "message": "query required"}
                import urllib.parse
                url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                webbrowser.open(url)
                return {"status": "success", "message": f"Playing {query} on YouTube"}
                
            elif action == "play_spotify":
                if not query: return {"status": "error", "message": "query required"}
                import urllib.parse
                url = f"https://open.spotify.com/search/{urllib.parse.quote(query)}"
                webbrowser.open(url)
                return {"status": "success", "message": f"Searching {query} on Spotify"}

            else:
                return {"status": "error", "message": "Invalid browser action."}

        except Exception as e:
            logger.error(f"BrowserAutomationTool error: {e}")
            return {"status": "error", "message": str(e)}
