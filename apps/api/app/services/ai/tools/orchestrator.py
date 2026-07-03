import time
import logging

from app.schemas.tool import ToolRequest, ToolResponse
from app.services.ai.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

class ToolOrchestrator:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    async def execute_tool(self, request: ToolRequest, context: dict) -> ToolResponse:
        tool = self.registry.get_tool(request.name)
        if not tool:
            msg = f"Error: Tool '{request.name}' not found natively."
            logger.warning(msg)
            return ToolResponse(id=request.id, name=request.name, content=msg, is_error=True)
            
        try:
            start_time = time.perf_counter()
            result = await tool.execute(execution_context=context, **request.arguments)
            latency = (time.perf_counter() - start_time) * 1000.0
            
            logger.info("Tool executed successfully", extra={"tool": request.name, "latency_ms": latency})
            return ToolResponse(id=request.id, name=request.name, content=str(result), is_error=False)
            
        except Exception as e:
            msg = f"Error executing internal tool: {str(e)}"
            logger.error(msg, exc_info=True)
            return ToolResponse(id=request.id, name=request.name, content=msg, is_error=True)
            
    async def execute_all(self, requests: list[ToolRequest], context: dict) -> list[ToolResponse]:
        responses = []
        for req in requests:
            res = await self.execute_tool(req, context)
            responses.append(res)
        return responses
