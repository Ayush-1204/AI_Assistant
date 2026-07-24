import json
import logging
from typing import Any

from app.services.ai.planner.agents.swarm.base import SwarmAgent
from app.services.ai.providers.router import ProviderRouter

logger = logging.getLogger(__name__)

class SwarmOrchestrator:
    """
    A lightweight, multi-agent framework inspired by conversational handoffs.
    The primary agent routes execution to sub-agents (e.g., Coder, Reviewer) dynamically 
    by resolving tool execution callbacks that return SwarmAgent instances.
    """
    def __init__(self, router: ProviderRouter):
        self.router = router
        
    async def run(self, starting_agent: SwarmAgent, messages: list[dict], max_turns: int = 15) -> str:
        current_agent = starting_agent
        history = messages.copy()
        
        for turn in range(max_turns):
            instructions = current_agent.instructions() if callable(current_agent.instructions) else current_agent.instructions
            system_msg = {"role": "system", "content": instructions}
            
            logger.info(f"[Swarm {turn+1}/{max_turns}] Active Agent: {current_agent.name}")
            
            try:
                # Convert python functions to OpenAI tool schemas for native provider support
                api_tools = []
                from app.services.ai.tools.base import BaseTool
                if current_agent.tools:
                    for t in current_agent.tools:
                        if callable(t):
                            api_tools.append({
                                "type": "function",
                                "function": {
                                    "name": t.__name__,
                                    "description": t.__doc__ or f"Execute {t.__name__}",
                                    "parameters": {"type": "object", "properties": {}}
                                }
                            })
                        elif isinstance(t, BaseTool):
                            api_tools.append({
                                "type": "function",
                                "function": {
                                    "name": t.name,
                                    "description": t.description,
                                    "parameters": t.parameters_schema
                                }
                            })
                        else:
                            api_tools.append(t)
                
                # Fallback to general reasoning intent optimized for flash/pro models
                response = await self.router.chat(
                    [system_msg] + history, 
                    tools=api_tools if api_tools else None,
                    intent="reasoning"
                )
                
                response_str = ""
                native_handoff = None
                native_tool_calls = []
                
                if isinstance(response, str):
                    response_str = response
                else:
                    # MockResponse (OpenRouter) or GenerateContentResponse (Gemini)
                    try:
                        if hasattr(response, "text") and response.text:
                            response_str = response.text
                    except Exception:
                        pass
                        
                    if hasattr(response, "function_calls") and response.function_calls:
                        for call in response.function_calls:
                            name = getattr(call, "name", "")
                            if name in ("transfer_to_reviewer", "transfer_to_coder"):
                                native_handoff = name
                            else:
                                native_tool_calls.append(call)
                    elif hasattr(response, "candidates") and response.candidates:
                        for part in response.candidates[0].content.parts:
                            if hasattr(part, "function_call") and part.function_call:
                                name = part.function_call.name
                                if name in ("transfer_to_reviewer", "transfer_to_coder"):
                                    native_handoff = name
                                else:
                                    native_tool_calls.append(part.function_call)

                if native_tool_calls and not native_handoff:
                    if response_str:
                        history.append({"role": "assistant", "content": response_str})
                    
                    for call in native_tool_calls:
                        name = getattr(call, "name", None) or getattr(call, "id", None) or "unknown"
                        args = getattr(call, "args", {})
                        if hasattr(args, "to_dict"):
                            args = args.to_dict()
                            
                        # Find and execute the internal BaseTool
                        for t in current_agent.tools:
                            if isinstance(t, BaseTool) and t.name == name:
                                try:
                                    result = await t.execute(execution_context={"agent": current_agent.name}, **args)
                                    from app.security.credential_stripper import CredentialStripper
                                    safe = CredentialStripper().strip(str(result))
                                    history.append({"role": "user", "content": f"<tool_result><name>{name}</name><output>{safe}</output></tool_result>"})
                                except Exception as e:
                                    history.append({"role": "user", "content": f"<tool_result><name>{name}</name><output>Error: {str(e)}</output></tool_result>"})
                                break
                    continue # Cycle swarm iteration to read tool output

                # Check for XML text routing signals
                xml_handoff = None
                if "<tool_call>" in response_str:
                    logger.info("[Swarm] Intercepting XML tool call from native provider output.")
                    if "transfer_to_reviewer" in response_str:
                        xml_handoff = "transfer_to_reviewer"
                    elif "transfer_to_coder" in response_str:
                        xml_handoff = "transfer_to_coder"
                
                handoff_target = native_handoff or xml_handoff
                
                if handoff_target:
                    if response_str:
                        history.append({"role": "assistant", "content": response_str})
                        
                    for tool in current_agent.tools:
                        if callable(tool) and tool.__name__ == handoff_target:
                            next_agent = tool()
                            if isinstance(next_agent, SwarmAgent):
                                current_agent = next_agent
                                history.append({"role": "user", "content": f"<tool_result><name>{handoff_target}</name><output>Transferred to {current_agent.name}</output></tool_result>"})
                            break
                    else:
                        if not native_handoff:
                            return response_str # Unhandled XML tool logic
                else:
                    return response_str # Standard generation complete
                    
            except Exception as e:
                logger.error(f"[Swarm Orchestrator] Fatal error during agent iteration: {str(e)}")
                return f"Agent Network Failure: {str(e)}"
                
        return "Swarm Network reached maximum recursion limit and forcibly halted."
