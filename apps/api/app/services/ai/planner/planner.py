import logging
from typing import Any

from app.schemas.tool import ToolRequest
from app.services.ai.providers.base import BaseLLMProvider
from app.services.ai.tools.strategies import ToolInvocationStrategy

logger = logging.getLogger(__name__)

class Planner:
    def __init__(self, provider: BaseLLMProvider, strategy: ToolInvocationStrategy, intent: str = "general"):
        self.provider = provider
        self.strategy = strategy
        self.intent = intent

    async def plan_step(self, messages: list[dict], tools_payload: list[dict]) -> tuple[Any, bool, list[ToolRequest], str]:
        """
        Determines the next action iteratively based on context.
        Returns: (raw_response_obj, has_tools, tool_requests, direct_text)
        """
        response_obj = await self.provider.chat(messages, tools=tools_payload, intent=self.intent)
        has_tool, tool_requests = self.strategy.extract_requests(response_obj)
        direct_text = self.strategy.get_text_from_response(response_obj)
        
        return response_obj, has_tool, tool_requests, direct_text
