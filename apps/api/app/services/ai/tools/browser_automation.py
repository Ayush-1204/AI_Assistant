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
                "description": "Action to take. Allowed: 'open_url', 'play_youtube', 'play_ytmusic', 'play_spotify'.",
                "enum": ["open_url", "play_youtube", "play_ytmusic", "play_spotify"]
            },
            "query": {
                "type": "string",
                "description": "The URL to open, or the search term for YouTube/Spotify."
            }
        },
        "required": ["action", "query"]
    }

    def _get_youtube_video_id(self, query: str) -> str:
        import urllib.request
        import urllib.parse
        import re
        
        try:
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8')
            video_ids = re.findall(r'watch\?v=(\S{11})', html)
            if video_ids:
                return str(video_ids[0])
        except Exception:
            pass
        return ""

    async def execute(self, execution_context: dict, **kwargs) -> Any:
        action = kwargs.get("action")
        query = kwargs.get("query")
        
        service_str = str(kwargs.get("service") or "").lower()
        query_str = str(query or "").lower()
        
        if not action:
            if "youtube music" in service_str or "yt music" in service_str or "yt music" in query_str:
                action = "play_ytmusic"
            elif "youtube" in service_str or "yt" in query_str:
                action = "play_youtube"
            elif "spotify" in service_str or "spotify" in query_str:
                action = "play_spotify"
            else:
                action = "open_url"
        
        # We use sync webbrowser natively on Windows default browser without blocking thread too much
        try:
            if action == "open_url":
                if not query: return {"status": "error", "message": "query required"}
                if not query.startswith("http"):
                    # Check if it looks like a domain name
                    if "." in query and " " not in query:
                        query = f"https://{query}"
                    else:
                        # Fallback to a google search if they just sent a phrase
                        import urllib.parse
                        query = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                webbrowser.open(query)
                return {"status": "success", "message": f"Opened {query} in default browser."}

            elif action == "play_youtube":
                if not query: return {"status": "error", "message": "query required"}
                vid = self._get_youtube_video_id(query)
                if vid:
                    url = f"https://www.youtube.com/watch?v={vid}"
                else:
                    import urllib.parse
                    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                webbrowser.open(url)
                return {"status": "success", "message": f"Playing {query} on YouTube"}
                
            elif action == "play_ytmusic":
                if not query: return {"status": "error", "message": "query required"}
                vid = self._get_youtube_video_id(query)
                if vid:
                    url = f"https://music.youtube.com/watch?v={vid}"
                else:
                    import urllib.parse
                    url = f"https://music.youtube.com/search?q={urllib.parse.quote(query)}"
                webbrowser.open(url)
                return {"status": "success", "message": f"Playing {query} on YouTube Music"}
                
            elif action == "play_spotify":
                if not query: return {"status": "error", "message": "query required"}
                import urllib.parse
                url = f"spotify:search:{urllib.parse.quote(query)}"
                webbrowser.open(url)
                return {"status": "success", "message": f"Searching {query} on Spotify (Desktop App)"}

            else:
                return {"status": "error", "message": "Invalid browser action."}

        except Exception as e:
            logger.error(f"BrowserAutomationTool error: {e}")
            return {"status": "error", "message": str(e)}
