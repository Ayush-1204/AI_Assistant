import asyncio
import json
import logging
import re
from urllib.parse import urlparse

import httpx

from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

# --- Quality news domains split by region ---
# These MUST be article-level publishers (not aggregators/social media/wikis)

TRUSTED_SOURCES_INDIA = [
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
    "abpnews.com",
    "zeenews.india.com",
]

TRUSTED_SOURCES_GLOBAL = [
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "theguardian.com",
    "bloomberg.com",
    "techcrunch.com",
    "cnbc.com",
    "wsj.com",
    "ft.com",
    "nytimes.com",
    "washingtonpost.com",
    "arstechnica.com",
    "wired.com",
    "theverge.com",
    "economist.com",
    "npr.org",
    "businessinsider.com",
    "forbes.com",
]

TRUSTED_SOURCES: dict[str, list[str]] = {
    "india": TRUSTED_SOURCES_INDIA,
    "us": TRUSTED_SOURCES_GLOBAL,
    "uk": [
        "bbc.co.uk", "bbc.com", "theguardian.com",
        "reuters.com", "independent.co.uk", "telegraph.co.uk",
    ] + TRUSTED_SOURCES_GLOBAL[:8],
    "global": TRUSTED_SOURCES_GLOBAL,
}

# Always exclude these — produce irrelevant or non-article content
EXCLUDED_DOMAINS = [
    "youtube.com", "youtu.be", "reddit.com", "twitter.com", "x.com",
    "tiktok.com", "facebook.com", "instagram.com", "linkedin.com",
    "pinterest.com", "quora.com", "wikipedia.org",
    "undp.org", "worldbank.org", "un.org", "imf.org",  # dev org homepages
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


def _is_article_url(url: str) -> bool:
    """
    Returns True if URL looks like a specific article, not a site homepage.
    Homepages: https://reuters.com  or  https://reuters.com/home
    Articles:  https://reuters.com/technology/ai/openai-cuts-prices-2026-07-30
    """
    try:
        path = urlparse(url).path.strip("/")
        # Must have a meaningful path (at least ~15 chars) with a segment
        return len(path) >= 15 and "/" in path
    except Exception:
        return False


def _fetch_og_image_sync(url: str, timeout: float = 6.0) -> str | None:
    """Synchronous cloudscraper fetch to bypass WAFs and bot protection."""
    try:
        import cloudscraper
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "desktop": True}
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
        }
        resp = scraper.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return None
        html = resp.text[:30000]
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
                if "1x1" not in img_url and not img_url.endswith(".svg"):
                    return img_url
    except Exception as e:
        logger.debug(f"[NewsSearch] og:image scrape failed for {url}: {e}")
    return None


async def _fetch_og_image(url: str, timeout: float = 6.0) -> str | None:
    """Async wrapper — runs cloudscraper in a thread to avoid blocking the event loop."""
    return await asyncio.to_thread(_fetch_og_image_sync, url, timeout)


async def _tavily_search(
    query: str,
    include_domains: list[str],
    max_results: int,
    days: int = 3,
) -> tuple[list[dict], list[str]]:
    """
    Direct Tavily news API call.
    include_domains is REQUIRED to get article-level URLs (without it Tavily returns homepages).
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

    # Retry up to 2 times on transient connection errors
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post("https://api.tavily.com/search", json=payload)
                response.raise_for_status()
                data = response.json()
            return data.get("results", []), data.get("images", [])
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            if attempt == 0:
                logger.warning(f"[NewsSearch] Tavily connection error (attempt {attempt+1}), retrying: {e}")
                await asyncio.sleep(1.5)
            else:
                raise


class NewsSearchTool(BaseTool):
    """
    Searches for news from trusted, location-aware publishers.
    Returns structured articles with exact title, URL, source domain, image, and publish date.
    """

    @property
    def name(self) -> str:
        return "news_search"

    @property
    def description(self) -> str:
        return (
            "Search for RECENT news articles (last 1-7 days) from trusted, reputable publishers. "
            "Use this instead of web_search when the user asks about news, current events, or headlines. "
            "Results come from quality sources only (Reuters, BBC, NDTV, ET, TechCrunch, etc.) based on user location. "
            "IMPORTANT: For comprehensive briefings covering multiple topics (e.g. AI news + business news + world news), "
            "call this tool SEPARATELY for each topic with a specific focused query "
            "(e.g. 'latest AI model releases 2026', 'stock market movements today', 'India geopolitics news'). "
            "Do NOT make one broad call for everything. "
            "Returns structured articles with title, summary, source, exact URL, image, and publish date."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The news topic or search query. Be specific — one topic per call."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of articles to return. Default: 5.",
                    "default": 5
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days back to search. Default: 3 (last 3 days). Max: 7.",
                    "default": 3
                },
            },
            "required": ["query"]
        }

    async def execute(self, execution_context: dict, **kwargs) -> str:
        query: str = kwargs.get("query", "")
        max_results: int = min(int(kwargs.get("max_results", 5)), 8)
        days: int = min(int(kwargs.get("days", 3)), 7)

        if not query:
            return json.dumps({"error": "Missing 'query' parameter."})

        # Detect region and build trusted domain lists
        location_hint: str | None = (
            execution_context.get("location")
            or execution_context.get("user_location")
        )
        region = _detect_region(location_hint)
        regional_trusted = TRUSTED_SOURCES.get(region, [])
        # Always include global quality sources too
        all_trusted = list(dict.fromkeys(regional_trusted + TRUSTED_SOURCES_GLOBAL))

        logger.info(f"[NewsSearch] Region='{region}', query='{query}', days={days}, domains={len(all_trusted)}")

        try:
            # --- Phase 1: Search WITH include_domains (required for article-level URLs) ---
            raw_results, tavily_images = await _tavily_search(
                query=query,
                include_domains=all_trusted,
                max_results=max_results + 5,  # extra buffer
                days=days,
            )

            # --- Phase 2: Filter homepage URLs and excluded domains ---
            article_results = [
                r for r in raw_results
                if _is_article_url(r.get("url", ""))
                and not any(excl in r.get("url", "") for excl in EXCLUDED_DOMAINS)
            ]

            # If we got too few article-level results, try GLOBAL sources only
            if len(article_results) < max_results:
                logger.info(f"[NewsSearch] Only {len(article_results)} article URLs, trying global fallback...")
                fallback_results, fallback_images = await _tavily_search(
                    query=query,
                    include_domains=TRUSTED_SOURCES_GLOBAL,
                    max_results=max_results + 5,
                    days=days + 2,  # slightly wider time window
                )
                fallback_articles = [
                    r for r in fallback_results
                    if _is_article_url(r.get("url", ""))
                    and not any(excl in r.get("url", "") for excl in EXCLUDED_DOMAINS)
                ]
                # Merge, deduplicate by URL
                seen_urls = {r.get("url") for r in article_results}
                for r in fallback_articles:
                    if r.get("url") not in seen_urls:
                        article_results.append(r)
                        seen_urls.add(r.get("url"))
                tavily_images = tavily_images + fallback_images

            filtered = article_results[:max_results]

            if not filtered:
                return json.dumps({"error": "No recent articles found for this query."})

            # --- Phase 3: Build articles using Tavily's per-article 'image' field ---
            # When topic="news", each result has an 'image' field directly from Tavily's crawl.
            # This is WAF-free. Only scrape og:image when Tavily has no image.
            articles_raw = []
            for r in filtered:
                url_str = r.get("url", "")
                tavily_img = r.get("image", "") or ""
                valid_img: str | None = (
                    tavily_img
                    if (isinstance(tavily_img, str)
                        and tavily_img.startswith("http")
                        and "ytimg" not in tavily_img
                        and "1x1" not in tavily_img)
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

            # --- Phase 4: Scrape og:image only for articles still missing images ---
            tavily_pool = [
                img for img in tavily_images
                if isinstance(img, str) and img.startswith("http")
                and "ytimg" not in img and "youtube.com" not in img
            ]
            pool_idx = 0

            missing = [(i, a) for i, a in enumerate(articles_raw) if not a["imageUrl"]]
            if missing:
                og_tasks = [_fetch_og_image(str(a["url"])) for _, a in missing]
                og_results = await asyncio.gather(*og_tasks, return_exceptions=True)

                for (idx, _), og_image in zip(missing, og_results):
                    if isinstance(og_image, str) and og_image.startswith("http"):
                        articles_raw[idx]["imageUrl"] = og_image
                    elif pool_idx < len(tavily_pool):
                        articles_raw[idx]["imageUrl"] = tavily_pool[pool_idx]
                        pool_idx += 1

            img_count = sum(1 for a in articles_raw if a.get("imageUrl"))
            logger.info(
                f"[NewsSearch] Done: {len(articles_raw)} articles, {img_count} with images, region={region}"
            )

            return json.dumps({
                "region": region,
                "articles": articles_raw,
            })

        except Exception as e:
            logger.error(f"[NewsSearch] Failed: {str(e)}", exc_info=True)
            return json.dumps({"error": f"News search failed: {str(e)}"})
