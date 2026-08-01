import asyncio
import json
import logging
import re
from typing import Any

import httpx

from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

# --- Location-Aware Trusted Source Configuration ---
TRUSTED_SOURCES: dict[str, list[str]] = {
    "india": [
        "timesofindia.com",
        "economictimes.indiatimes.com",
        "hindustantimes.com",
        "ndtv.com",
        "thehindu.com",
        "livemint.com",
        "moneycontrol.com",
        "indianexpress.com",
        "businesstoday.in",
    ],
    "us": [
        "reuters.com",
        "apnews.com",
        "bbc.com",
        "nytimes.com",
        "washingtonpost.com",
        "theguardian.com",
        "npr.org",
        "bloomberg.com",
    ],
    "uk": [
        "bbc.co.uk",
        "bbc.com",
        "theguardian.com",
        "reuters.com",
        "independent.co.uk",
        "telegraph.co.uk",
    ],
    "global": [
        "reuters.com",
        "apnews.com",
        "bbc.com",
        "theguardian.com",
        "bloomberg.com",
    ],
}

def _detect_region(location_hint: str | None) -> str:
    """Map a location hint string to a region key."""
    if not location_hint:
        return "global"
    loc = location_hint.lower()
    if any(kw in loc for kw in ["india", "delhi", "mumbai", "bangalore", "hyderabad", "chennai", "kolkata", "faridabad", "noida", "gurgaon"]):
        return "india"
    if any(kw in loc for kw in ["united states", "usa", "us ", "new york", "california", "texas"]):
        return "us"
    if any(kw in loc for kw in ["united kingdom", "uk ", "london", "england", "scotland"]):
        return "uk"
    return "global"


async def _fetch_og_image(url: str, timeout: float = 4.0) -> str | None:
    """
    Attempts to extract the og:image or twitter:image meta tag from a news article URL.
    Returns None if unavailable or on timeout/error.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return None
            # Only parse the <head> portion for speed
            html = resp.text[:20000]
            # og:image
            match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](https?://[^"\']+)["\']', html, re.IGNORECASE)
            if not match:
                match = re.search(r'<meta[^>]+content=["\'](https?://[^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.IGNORECASE)
            if not match:
                # twitter:image fallback
                match = re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\'](https?://[^"\']+)["\']', html, re.IGNORECASE)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None


class NewsSearchTool(BaseTool):
    """
    Searches for news from trusted, location-aware sources.
    Returns structured articles with titles, summaries, source names, URLs, and og:image thumbnails.
    """

    @property
    def name(self) -> str:
        return "news_search"

    @property
    def description(self) -> str:
        return (
            "Search for recent, reliable news articles from trusted regional publishers. "
            "Use this instead of web_search when the user asks about news, current events, or headlines. "
            "Automatically selects high-quality sources based on user location (e.g., Times of India for India, BBC/Reuters globally). "
            "Returns structured articles with title, summary, source, URL, and a relevant thumbnail image."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The news topic or search query (e.g., 'AI regulation latest news', 'India economy 2025')."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of articles to return. Default: 5.",
                    "default": 5
                },
            },
            "required": ["query"]
        }

    async def execute(self, execution_context: dict, **kwargs) -> str:
        query: str = kwargs.get("query", "")
        max_results: int = int(kwargs.get("max_results", 5))

        if not query:
            return json.dumps({"error": "Missing 'query' parameter."})

        # Detect region from execution context
        location_hint: str | None = (
            execution_context.get("location")
            or execution_context.get("user_location")
        )
        region = _detect_region(location_hint)
        trusted_domains = TRUSTED_SOURCES.get(region, TRUSTED_SOURCES["global"])

        logger.info(f"[NewsSearch] Region='{region}', query='{query}', sources={trusted_domains[:3]}...")

        try:
            from app.integrations.search.tavily import TavilySearchProvider
            provider = TavilySearchProvider()

            # Build site: restricted query for Tavily
            site_filter = " OR ".join([f"site:{d}" for d in trusted_domains])
            constrained_query = f"{query} ({site_filter})"

            results, _ = await provider.search(constrained_query, max_results=max(max_results + 2, 8))

            if not results:
                # Fallback: try without site restriction
                logger.warning(f"[NewsSearch] No results with site filter, falling back to plain query.")
                results, _ = await provider.search(query, max_results=max_results)

            # Build article list (cap at max_results)
            articles_raw = []
            for r in results[:max_results]:
                url_str = str(r.url) if hasattr(r, "url") else ""
                # Extract source name from domain
                domain_match = re.search(r"(?:https?://)?(?:www\.)?([^/]+)", url_str)
                source_name = domain_match.group(1) if domain_match else r.source if hasattr(r, "source") else "Unknown"

                articles_raw.append({
                    "title": r.title,
                    "url": url_str,
                    "snippet": r.snippet,
                    "source": source_name,
                    "imageUrl": None,  # will be filled below
                })

            # Fetch og:image thumbnails concurrently (with a timeout guard)
            og_tasks = [_fetch_og_image(a["url"]) for a in articles_raw]
            og_results = await asyncio.gather(*og_tasks, return_exceptions=True)

            articles_out = []
            for article, og_image in zip(articles_raw, og_results):
                if isinstance(og_image, str) and og_image.startswith("http"):
                    article["imageUrl"] = og_image
                else:
                    article["imageUrl"] = None  # frontend will show no image
                articles_out.append(article)

            logger.info(f"[NewsSearch] Returning {len(articles_out)} articles (region={region}).")
            return json.dumps({
                "region": region,
                "sources_used": trusted_domains,
                "articles": articles_out,
            })

        except Exception as e:
            logger.error(f"[NewsSearch] Failed: {str(e)}", exc_info=True)
            return json.dumps({"error": f"News search failed: {str(e)}"})
