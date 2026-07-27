import json
import logging
from typing import Any

from app.services.ai.providers.base import BaseLLMProvider
from app.services.ai.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

class ToolRouter:
    """
    Dynamically routes an abstract capability to a concrete Tool in the Registry.
    """
    def __init__(self, provider: BaseLLMProvider, registry: ToolRegistry):
        self.provider = provider
        self.registry = registry

    async def resolve_capability(self, capability: str) -> str | None:
        """
        Returns the name of the best matching tool for the given capability.
        """
        available_tools = []
        for name, tool in self.registry._tools.items():
            meta = {
                "name": name,
                "description": getattr(tool, "description", ""),
                "reliability": getattr(tool, "estimated_reliability", 1.0)
            }
            available_tools.append(meta)

        prompt = f"""You are a Tool Router. Match the requested Capability to the best available Tool.

Requested Capability: {capability}

Available Tools:
{json.dumps(available_tools, indent=2)}

Return ONLY a JSON object:
{{
  "selected_tool": "tool_name",
  "reason": "Why this tool is best"
}}
"""
        messages = [
            {"role": "system", "content": "You are a fast router. Output ONLY valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            import typing
            from app.services.ai.providers.router import ProviderRouter
            router_inst = typing.cast(ProviderRouter, self.provider)
            
            result = await router_inst.chat(messages, intent="structured")
            start = result.find("{")
            end = result.rfind("}") + 1
            if start != -1 and end != -1:
                route_json = json.loads(result[start:end])
                selected = route_json.get("selected_tool")
                if selected in self.registry._tools:
                    logger.info(f"[ToolRouter] Routed capability '{capability}' to '{selected}'")
                    return selected
        except Exception as e:
            logger.warning(f"[ToolRouter] Failed to route capability: {str(e)}")
            
        # Fallback heuristic: just return the first tool that kinda matches
        cap_lower = capability.lower()
        for name, tool in self.registry._tools.items():
            if name.lower() in cap_lower or cap_lower in name.lower() or cap_lower in tool.description.lower():
                return name
                
        return None
