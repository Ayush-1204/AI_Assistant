import logging
from app.services.ai.tools.base import BaseTool

def _run_in_new_loop(coro):
    import sys
    import asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    try:
        return new_loop.run_until_complete(coro)
    finally:
        new_loop.close()


logger = logging.getLogger(__name__)


class PlaywrightBrowserTool(BaseTool):
    """Full Playwright-powered headless browser tool for complex web automation."""

    @property
    def name(self) -> str:
        return "browser"

    @property
    def description(self) -> str:
        return (
            "Drive a real headless Chromium browser. Use for: scraping pages that require JavaScript, "
            "extracting content from login-protected sites, filling and submitting forms, executing JS, "
            "or waiting for dynamic content to load. For simple URL-opening use open_browser instead."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["extract", "fill_form", "execute_js", "wait_and_extract", "screenshot"],
                    "description": (
                        "The browser action: "
                        "'extract' - load page and return visible text or selector content; "
                        "'fill_form' - fill fields and optionally submit; "
                        "'execute_js' - run arbitrary JavaScript and return result; "
                        "'wait_and_extract' - wait for a CSS selector to appear then extract; "
                        "'screenshot' - return base64 PNG of the page."
                    ),
                },
                "url": {
                    "type": "string",
                    "description": "Target URL to navigate to.",
                },
                "selectors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "CSS selectors to interact with or extract text from.",
                },
                "form_fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string"},
                            "value": {"type": "string"},
                        },
                        "required": ["selector", "value"],
                    },
                    "description": "For fill_form: list of {selector, value} pairs to fill in.",
                },
                "submit_selector": {
                    "type": "string",
                    "description": "For fill_form: CSS selector for the submit button. Optional.",
                },
                "js_code": {
                    "type": "string",
                    "description": "For execute_js: the JavaScript expression to evaluate in the page context.",
                },
                "wait_selector": {
                    "type": "string",
                    "description": "For wait_and_extract: wait for this CSS selector to appear before extracting.",
                },
                "wait_timeout": {
                    "type": "integer",
                    "description": "Milliseconds to wait for wait_selector before timing out. Default 10000.",
                },
            },
            "required": ["action", "url"],
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    def dynamic_requires_confirmation(self, kwargs: dict) -> bool:
        action = kwargs.get("action", "extract")
        return action in ["fill_form", "execute_js"]

    @property
    def risk_level(self) -> str:
        return "moderate"

    async def execute(self, execution_context: dict, **kwargs) -> str:
        import asyncio
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(_run_in_new_loop, self._execute_async(execution_context, **kwargs)),
                timeout=45.0
            )
        except asyncio.TimeoutError:
            return f"ERROR: Browser execution timed out after 45 seconds while processing action '{kwargs.get('action')}' on {kwargs.get('url')}."

    async def _execute_async(self, execution_context: dict, **kwargs) -> str:
        action = kwargs.get("action", "extract")
        url = kwargs.get("url", "")
        selectors = kwargs.get("selectors", [])
        form_fields = kwargs.get("form_fields", [])
        submit_selector = kwargs.get("submit_selector")
        js_code = kwargs.get("js_code", "")
        wait_selector = kwargs.get("wait_selector")
        wait_timeout = kwargs.get("wait_timeout", 10000)

        if not url:
            return "ERROR: url is required."

        try:
            from playwright.async_api import async_playwright, TimeoutError as PWTimeout
        except ImportError:
            return "ERROR: Playwright not installed. Run 'pip install playwright && playwright install chromium'."

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0.0.0 Safari/537.36"
                    )
                )
                page = await context.new_page()

                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                except PWTimeout:
                    logger.warning(f"[Browser] Page load timed out for {url}, continuing anyway")

                result = ""

                if action == "extract":
                    if selectors:
                        parts = []
                        for sel in selectors:
                            try:
                                texts = await page.locator(sel).all_inner_texts()
                                parts.extend(texts)
                            except Exception:
                                pass
                        result = "\n".join(parts) if parts else await page.evaluate("document.body.innerText")
                    else:
                        result = await page.evaluate("document.body.innerText")

                elif action == "fill_form":
                    for field in form_fields:
                        sel = field.get("selector", "")
                        val = field.get("value", "")
                        try:
                            await page.locator(sel).fill(val)
                            logger.info(f"[Browser] Filled '{sel}' with value")
                        except Exception as e:
                            logger.warning(f"[Browser] fill failed for {sel}: {e}")

                    if submit_selector:
                        try:
                            await page.locator(submit_selector).click()
                            await page.wait_for_load_state("domcontentloaded", timeout=10000)
                        except PWTimeout:
                            logger.warning("[Browser] Submit click timed out")
                        except Exception as e:
                            logger.warning(f"[Browser] Submit click error: {e}")

                    result = await page.evaluate("document.body.innerText")

                elif action == "execute_js":
                    if not js_code:
                        result = "ERROR: js_code is required for execute_js action."
                    else:
                        js_result = await page.evaluate(js_code)
                        result = str(js_result)

                elif action == "wait_and_extract":
                    if wait_selector:
                        try:
                            await page.wait_for_selector(wait_selector, timeout=wait_timeout)
                        except PWTimeout:
                            result = f"ERROR: Timed out waiting for selector '{wait_selector}' after {wait_timeout}ms."
                            await browser.close()
                            return result

                    if selectors:
                        parts = []
                        for sel in selectors:
                            try:
                                texts = await page.locator(sel).all_inner_texts()
                                parts.extend(texts)
                            except Exception:
                                pass
                        result = "\n".join(parts) if parts else await page.evaluate("document.body.innerText")
                    else:
                        result = await page.evaluate("document.body.innerText")

                elif action == "screenshot":
                    import base64
                    screenshot_bytes = await page.screenshot(full_page=True, type="png")
                    b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                    result = f"[SCREENSHOT: {len(b64)} base64 chars captured from {url}]"

                else:
                    result = f"ERROR: Unknown action '{action}'."

                await browser.close()
                return result[:8000]  # truncate massive results

        except Exception as e:
            logger.error(f"[Browser] Unexpected error: {e}")
            return f"ERROR executing browser action '{action}': {e}"
