import logging
import urllib.parse
from typing import Any
import httpx

from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

class WolframAlphaTool(BaseTool):
    """
    Leverages Wolfram Alpha for mathematical, scientific, and quantitative queries.
    """

    def __init__(self, app_id: str | None = None):
        super().__init__()
        self.app_id = app_id

    @property
    def name(self) -> str:
        return "wolfram_alpha"

    @property
    def description(self) -> str:
        return (
            "Answers queries requiring actual mathematical/scientific reasoning, unit conversions, "
            "chemistry, physics, or complex computations. Unlike standard calculators, this handles "
            "natural language math (e.g., 'derivative of x^2', 'distance to mars in km')."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The mathematical or scientific question to evaluate."
                }
            },
            "required": ["query"]
        }

    async def execute(self, execution_context: dict, **kwargs) -> Any:
        query = kwargs.get("query")
        if not query:
            return "Error: 'query' parameter is required."
            
        if not self.app_id:
            return "Error: WOLFRAM_ALPHA_APP_ID is not configured in the environment."

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"https://api.wolframalpha.com/v1/result?appid={self.app_id}&i={urllib.parse.quote(query)}"
                response = await client.get(url)
                
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 501:
                    return f"Wolfram Alpha could not interpret the query: '{query}'"
                else:
                    return f"Wolfram Alpha returned status {response.status_code}: {response.text}"

        except Exception as e:
            logger.error(f"[WolframAlphaTool] Request failed: {str(e)}")
            return f"Error executing Wolfram Alpha query: {str(e)}"
