import logging
from typing import Any

from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

class VisionAnalysisTool(BaseTool):
    @property
    def name(self) -> str:
        return "vision_analysis"

    @property
    def description(self) -> str:
        return "Analyzes user-uploaded images and extracts visual information or descriptions."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Specific question or instruction about the image."
                }
            },
            "required": ["query"]
        }
        
    @property
    def supported_intents(self) -> list[str]:
        return ["structured", "general"]

    async def execute(self, execution_context: dict, **kwargs: Any) -> Any:
        query = kwargs.get("query", "Describe what is in this image.")
        images = execution_context.get("images", [])
        
        if not images:
            return "No images were provided in the current context to analyze."
            
        messages = [
            {"role": "system", "content": "You are a helpful computer vision assistant. Describe or answer questions about the provided images."},
            {"role": "user", "content": query, "images": images}
        ]
        
        try:
            from app.dependencies import _router_instance
            import typing
            from app.services.ai.providers.router import ProviderRouter
            
            router_inst = typing.cast(ProviderRouter, _router_instance)
            # The router should natively intercept `images` in the payload and dispatch to vision models
            result = await router_inst.chat(messages, intent="general")
            return result
        except Exception as e:
            logger.error(f"[VisionAnalysisTool] Execution failed: {e}")
            return f"Failed to analyze image: {str(e)}"
