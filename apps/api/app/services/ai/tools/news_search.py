import asyncio
import json
import logging
import re

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
        "firstpost.com",
        "news18.com",
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
        "cnbc.com",
        "techcrunch.com",
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
        "techcrunch.com",
        "cnbc.com",
    ],
}

# Always exclude these — they produce irrelevant or non-article content
EXCLUDED_DOMAINS = [
    "youtube.com",
    "youtu.be",
    "reddit.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "pinterest.com",
    "quora.com",
    "wikipedia.org",
]


def _detect_region(location_hint: str | None) -> str:
    """Map a location hint string to a region key."""
    if not location_hint:
        return "global"
    loc = location_hint.lower()
    if any(kw in loc for kw in ["india", "delhi", "mumbai", "bangalore", "hyderabad",
                                  "chennai", "kolkata", "faridabad", "noida", "gurgaon",
                                  "pune", "ahmedabad", "jaipur"]):
        return "india"
    if any(kw in loc for kw in ["united states", "usa", " us,", "new york",
                                  "california", "texas", "washington dc"]):
        return "us"
    if any(kw in loc for kw in ["united kingdom", "uk,", "london", "england", "scotland"]):
        return "uk"
    return "global"


def _extract_domain(url: str) -> str:
    """Extract clean domain name (e.g. 'reuters.com') from a URL."""
    match = re.search(r"(?:https?://)?(?:www\.)?([^/?#]+)", url)
    return match.group(1) if match else url


async def _fetch_og_image(url: str, timeout: float = 5.0) -> str | None:
    """
    Attempts to extract the og:image / twitter:image from a news article page.
    Returns None on any failure.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html",
        }
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return None
            html = resp.text[:25000]  # only need <head>

            patterns = [
                r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](https?://[^"\'>\s]+)["\']',
                r'<meta[^>]+content=["\'](https?://[^"\'>\s]+)["\'][^>]+property=["\']og:image["\']',
                r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\'](https?://[^"\'>\s]+)["\']',
                r'<meta[^>]+content=["\'](https?://[^"\'>\s]+)["\'][^>]+name=["\']twitter:image["\']',
            ]
            for pattern in patterns:
                m = re.search(pattern, html, re.IGNORECASE)
                if m:
                    img_url = m.group(1)
                    # Skip 1×1 tracking pixels and svg icons
                    if "1x1" not in img_url and not img_url.endswith(".svg"):
                        return img_url
    except Exception:
        pass
    return None


async def _tavily_search(
    query: str,
    include_domains: list[str],
    max_results: int,
) -> tuple[list[dict], list[str]]:
    """
    Direct Tavily API call with include_domains / exclude_domains support.
    Returns (raw_results, images).
    """
    from app.config import get_settings
    settings = get_settings()
    api_key = settings.TAVILY_API_KEY
    if not api_key:
        raise ValueError("Tavily API key not configured")

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": False,
        "include_images": True,
        "include_raw_content": False,
        "max_results": max_results,
        "include_domains": include_domains,
        "exclude_domains": EXCLUDED_DOMAINS,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post("https://api.tavily.com/search", json=payload)
        response.raise_for_status()
        data = response.json()

    return data.get("results", []), data.get("images", [])


class NewsSearchTool(BaseTool):
    """
    Searches for news from trusted, location-aware publishers.
    Returns structured articles with exact title, URL, source domain, and image.
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
                    "description": "The news topic or search query."
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
        max_results: int = min(int(kwargs.get("max_results", 5)), 8)

        if not query:
            return json.dumps({"error": "Missing 'query' parameter."})

        # Detect region from execution context
        location_hint: str | None = (
            execution_context.get("location")
            or execution_context.get("user_location")
        )
        region = _detect_region(location_hint)
        trusted_domains = TRUSTED_SOURCES.get(region, TRUSTED_SOURCES["global"])

        logger.info(f"[NewsSearch] Region='{region}', query='{query}', domains={trusted_domains[:3]}...")

        try:
            # --- Phase 1: Fetch articles with domain filter ---
            raw_results, tavily_images = await _tavily_search(
                query=query,
                include_domains=trusted_domains,
                max_results=max_results + 3,  # fetch a few extra, filter below
            )

            # Fallback: no results with domain filter → try without
            if not raw_results:
                logger.warning("[NewsSearch] No results with trusted domains, falling back to plain query.")
                raw_results, tavily_images = await _tavily_search(
                    query=query,
                    include_domains=[],
                    max_results=max_results,
                )

            # --- Phase 2: Filter out excluded domains just in case ---
            filtered = [
                r for r in raw_results
                if not any(excl in r.get("url", "") for excl in EXCLUDED_DOMAINS)
            ]

            # Cap to requested count
            filtered = filtered[:max_results]

            # --- Phase 3: Build article stubs ---
            articles_raw = []
            for r in filtered:
                url_str = r.get("url", "")
                articles_raw.append({
                    "title": r.get("title", ""),
                    "url": url_str,
                    "snippet": r.get("content", ""),
                    "source": _extract_domain(url_str),
                    "imageUrl": None,
                })

            # --- Phase 4: Fetch og:image concurrently ---
            og_tasks = [_fetch_og_image(a["url"]) for a in articles_raw]
            og_results = await asyncio.gather(*og_tasks, return_exceptions=True)

            # Use Tavily images as ordered fallback pool
            tavily_image_pool = [
                img for img in tavily_images
                if isinstance(img, str) and img.startswith("http")
                and "youtube.com" not in img
                and "ytimg.com" not in img
            ]
            tavily_pool_index = 0

            articles_out = []
            for article, og_image in zip(articles_raw, og_results):
                if isinstance(og_image, str) and og_image.startswith("http"):
                    article["imageUrl"] = og_image
                elif tavily_pool_index < len(tavily_image_pool):
                    # Use next Tavily image as fallback
                    article["imageUrl"] = tavily_image_pool[tavily_pool_index]
                    tavily_pool_index += 1
                else:
                    article["imageUrl"] = None

                articles_out.append(article)

            logger.info(
                f"[NewsSearch] {len(articles_out)} articles returned. "
                f"OG images: {sum(1 for a in articles_out if a['imageUrl'])}/{len(articles_out)}"
            )

            return json.dumps({
                "region": region,
                "sources_used": trusted_domains,
                "articles": articles_out,
            })

        except Exception as e:
            logger.error(f"[NewsSearch] Failed: {str(e)}", exc_info=True)
            return json.dumps({"error": f"News search failed: {str(e)}"})
