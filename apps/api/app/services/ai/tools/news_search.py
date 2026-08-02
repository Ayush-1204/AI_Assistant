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
        "abpnews.com",
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


def _fetch_og_image_sync(url: str, timeout: float = 6.0) -> str | None:
    """Synchronous cloudscraper fetch to bypass WAFs and bot protection."""
    try:
        import cloudscraper
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
        }
        
        resp = scraper.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return None
            
        html = resp.text[:30000]  # only need <head>

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
    except Exception as e:
        logger.debug(f"[NewsSearch] Failed to fetch image for {url}: {e}")
    return None


async def _fetch_og_image(url: str, timeout: float = 6.0) -> str | None:
    """
    Attempts to extract the og:image / twitter:image from a news article page.
    Uses cloudscraper in a background thread to bypass Cloudflare/WAFs.
    """
    return await asyncio.to_thread(_fetch_og_image_sync, url, timeout)


async def _tavily_search(
    query: str,
    include_domains: list[str],
    max_results: int,
    days: int = 3,
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
        "topic": "news",
        "days": days,
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
            "Search for RECENT news articles (last 1-7 days) from trusted, reputable publishers. "
            "Use this instead of web_search when the user asks about news, current events, or headlines. "
            "Results are automatically ranked to prefer high-quality sources (Reuters, BBC, NDTV, ET, etc.) based on user location. "
            "IMPORTANT: For comprehensive briefings covering multiple topics (e.g. AI news + business news + world news), "
            "call this tool SEPARATELY for each topic with a specific focused query (e.g. 'latest AI model releases 2026', "
            "'stock market movements today', 'India geopolitics news'). Do NOT make one broad call for everything. "
            "Returns structured articles with title, summary, source, exact URL, image, and publish date."
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
                "days": {
                    "type": "integer",
                    "description": "Number of days back to search for news. Default: 3.",
                    "default": 3
                },
            },
            "required": ["query"]
        }

    async def execute(self, execution_context: dict, **kwargs) -> str:
        query: str = kwargs.get("query", "")
        max_results: int = min(int(kwargs.get("max_results", 5)), 8)
        days: int = int(kwargs.get("days", 3))

        if not query:
            return json.dumps({"error": "Missing 'query' parameter."})

        # Detect region from execution context
        location_hint: str | None = (
            execution_context.get("location")
            or execution_context.get("user_location")
        )
        region = _detect_region(location_hint)
        regional_trusted = TRUSTED_SOURCES.get(region, [])
        global_trusted = TRUSTED_SOURCES["global"]
        # Combined set: regional + global quality sources
        all_trusted = list(dict.fromkeys(regional_trusted + global_trusted))  # preserve order, no dupes

        logger.info(f"[NewsSearch] Region='{region}', query='{query}', days={days}")

        try:
            # --- Phase 1: Broad news search WITHOUT include_domains ---
            # include_domains + topic:news is too restrictive and triggers fallback to junk.
            # Instead: exclude junk, then post-rank by trusted domain preference.
            raw_results, tavily_images = await _tavily_search(
                query=query,
                include_domains=[],
                max_results=max_results + 6,  # fetch extra buffer for post-ranking
                days=days,
            )

            if not raw_results:
                return json.dumps({"error": "No news found for this query."})

            # --- Phase 2: Post-rank: trusted domains first, then others ---
            # Excluded domains are already filtered in _tavily_search, but double-check
            clean = [
                r for r in raw_results
                if not any(excl in r.get("url", "") for excl in EXCLUDED_DOMAINS)
            ]

            def _trust_score(r: dict) -> int:
                url = r.get("url", "")
                for domain in all_trusted:
                    if domain in url:
                        return 1  # trusted
                return 0  # untrusted

            # Stable sort: trusted first, maintain Tavily relevance order within each group
            clean.sort(key=_trust_score, reverse=True)
            filtered = clean[:max_results]

            if not filtered:
                return json.dumps({"error": "No usable news found for this query."})

            # --- Phase 3: Build articles, using Tavily's per-article 'image' field ---
            # Tavily news topic returns 'image' per result — this is WAF-free and correct.
            articles_raw = []
            for r in filtered:
                url_str = r.get("url", "")
                # Tavily news topic returns per-result image — use it directly
                tavily_img = r.get("image", "") or r.get("imageUrl", "")
                valid_img = (
                    tavily_img
                    if (isinstance(tavily_img, str) and tavily_img.startswith("http")
                        and "ytimg" not in tavily_img and "1x1" not in tavily_img)
                    else None
                )
                articles_raw.append({
                    "title": r.get("title", ""),
                    "url": url_str,
                    "snippet": r.get("content", ""),
                    "source": _extract_domain(url_str),
                    "imageUrl": valid_img,
                    "publishedAt": r.get("published_date", ""),
                })

            # --- Phase 4: Only scrape og:image for articles missing an image ---
            # Build a clean fallback pool from Tavily's top-level images list
            tavily_pool = [
                img for img in tavily_images
                if isinstance(img, str) and img.startswith("http")
                and "ytimg" not in img and "youtube.com" not in img
            ]
            pool_idx = 0

            articles_needing_images = [(i, a) for i, a in enumerate(articles_raw) if not a["imageUrl"]]
            if articles_needing_images:
                og_tasks = [_fetch_og_image(str(a["url"])) for _, a in articles_needing_images]
                og_results = await asyncio.gather(*og_tasks, return_exceptions=True)

                for (idx, article), og_image in zip(articles_needing_images, og_results):
                    if isinstance(og_image, str) and og_image.startswith("http"):
                        articles_raw[idx]["imageUrl"] = og_image
                    elif pool_idx < len(tavily_pool):
                        articles_raw[idx]["imageUrl"] = tavily_pool[pool_idx]
                        pool_idx += 1

            img_count = sum(1 for a in articles_raw if a.get("imageUrl"))
            logger.info(
                f"[NewsSearch] Done: {len(articles_raw)} articles, "
                f"{img_count} with images, region={region}"
            )

            return json.dumps({
                "region": region,
                "sources_used": all_trusted,
                "articles": articles_raw,
            })

        except Exception as e:
            logger.error(f"[NewsSearch] Failed: {str(e)}", exc_info=True)
            return json.dumps({"error": f"News search failed: {str(e)}"})
