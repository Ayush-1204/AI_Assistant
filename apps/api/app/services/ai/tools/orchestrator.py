import logging
import time
from datetime import datetime

from app.schemas.ai_pipeline import NormalizedToolResult
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

        requires_conf = False # Bypassed based on user request
            
        from app.config import get_settings
        if getattr(get_settings(), "LOCAL_ONLY_MODE", False):
             if getattr(tool, "requires_network", True):
                 msg = f"Security Block: '{request.name}' requires network access, which is blocked in Local-Only Mode."
                 logger.warning(msg)
                 return ToolResponse(id=request.id, name=request.name, content=msg, is_error=True)
            
        try:
            start_time = time.perf_counter()
            result = await tool.execute(execution_context=context, **request.arguments)
            latency = (time.perf_counter() - start_time) * 1000.0
            
            logger.info("Tool executed successfully", extra={"tool": request.name, "latency_ms": latency})
            from app.security.credential_stripper import CredentialStripper
            safe_content = CredentialStripper().strip(str(result))
            
            # Normalization
            if isinstance(result, NormalizedToolResult):
                norm = result
            else:
                norm = NormalizedToolResult(
                    tool_name=request.name,
                    source=request.name,
                    timestamp=datetime.now(),
                    confidence=getattr(tool, "estimated_reliability", 1.0),
                    rawData=result,
                    normalizedData={"content": safe_content}
                )
            return ToolResponse(id=request.id, name=request.name, content=safe_content, is_error=False, normalized_result=norm)
            
        except Exception as e:
            msg = f"Error executing internal tool: {str(e)}"
            logger.error(msg, exc_info=True)
            norm = NormalizedToolResult(
                tool_name=request.name,
                source=request.name,
                timestamp=datetime.now(),
                confidence=0.0,
                rawData=msg
            )
            return ToolResponse(id=request.id, name=request.name, content=msg, is_error=True, normalized_result=norm)
            
    async def execute_all(self, requests: list[ToolRequest], context: dict) -> list[ToolResponse]:
        responses = []
        for req in requests:
            res = await self.execute_tool(req, context)
            responses.append(res)
        return responses
