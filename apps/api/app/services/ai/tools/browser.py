from app.services.ai.tools.base import BaseTool


class BrowserTool(BaseTool):
    @property
    def name(self) -> str:
        return "browser_automation"
        
    @property
    def description(self) -> str:
        return "Executes headless Playwright browser scripts to interact with complex web UI, scrape sites requiring auth, or navigate through workflows."
        
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["extract", "navigate_and_click", "screenshot"],
                    "description": "The type of browser action to perform."
                },
                "url": {
                    "type": "string",
                    "description": "Target URL to open."
                },
                "selectors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional CSS selectors to interact with or extract text from."
                }
            },
            "required": ["action", "url"]
        }

    @property
    def requires_confirmation(self) -> bool:
        return True # Interacting with the web should halt for approval (e.g. buying things)

    @property
    def risk_level(self) -> str:
        return "moderate"

    async def execute(self, execution_context: dict, **kwargs) -> str:
        action = kwargs.get("action")
        url = kwargs.get("url")
        selectors = kwargs.get("selectors", [])
        
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Navigate
                await page.goto(url, wait_until="networkidle")
                
                result = ""
                if action == "extract":
                    if selectors:
                        extracted = []
                        for sel in selectors:
                            elements = await page.locator(sel).all_inner_texts()
                            extracted.extend(elements)
                        result = "\\n".join(extracted)
                    else:
                        result = await page.evaluate("document.body.innerText")
                        
                elif action == "navigate_and_click":
                    for sel in selectors:
                        await page.click(sel)
                    await page.wait_for_load_state("networkidle")
                    result = await page.evaluate("document.body.innerText")
                    
                elif action == "screenshot":
                    import base64
                    screenshot_bytes = await page.screenshot(full_page=True)
                    b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                    result = f"[SCREENSHOT CAPTURED: bytes=len({len(b64)})]"
                
                await browser.close()
                return result[:5000] # truncate massive results
                
        except ImportError:
            return "ERROR: Playwright not installed. Run 'pip install playwright' and 'playwright install chromium'."
        except Exception as e:
            return f"ERROR executing browser logic: {e}"
