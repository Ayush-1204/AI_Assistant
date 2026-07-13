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
                # Fallback to general reasoning intent optimized for flash/pro models
                response_str = await self.router.chat(
                    [system_msg] + history, 
                    tools=current_agent.tools if current_agent.tools else None,
                    intent="reasoning"
                )
                
                # In native integration, the ProviderRouter could return string dumps containing xml tools
                # We dynamically intercept XML function triggers if the provider didn't natively break them down.
                # For Phase 1 of Swarm, we treat textual responses containing 'transfer_to' as literal routing signals.
                
                if "<tool_call>" in response_str:
                    logger.info("[Swarm] Intercepting XML tool call from native provider output.")
                    # Implement quick XML parse specifically for Handoff Tools
                    if "transfer_to_reviewer" in response_str:
                        # Extract context
                        history.append({"role": "assistant", "content": response_str})
                        
                        # Execute handoff
                        for tool in current_agent.tools:
                            if tool.__name__ == "transfer_to_reviewer":
                                next_agent = tool()
                                if isinstance(next_agent, SwarmAgent):
                                    current_agent = next_agent
                                    history.append({"role": "user", "content": f"<tool_result><name>transfer_to_reviewer</name><output>Transferred to {current_agent.name}</output></tool_result>"})
                                break
                    elif "transfer_to_coder" in response_str:
                        history.append({"role": "assistant", "content": response_str})
                        for tool in current_agent.tools:
                            if tool.__name__ == "transfer_to_coder":
                                next_agent = tool()
                                if isinstance(next_agent, SwarmAgent):
                                    current_agent = next_agent
                                    history.append({"role": "user", "content": f"<tool_result><name>transfer_to_coder</name><output>Transferred to {current_agent.name}</output></tool_result>"})
                                break
                    else:
                        return response_str # Unhandled tool logic
                        
                else:
                    return response_str # Standard generation complete
                    
            except Exception as e:
                logger.error(f"[Swarm Orchestrator] Fatal error during agent iteration: {str(e)}")
                return f"Agent Network Failure: {str(e)}"
                
        return "Swarm Network reached maximum recursion limit and forcibly halted."
