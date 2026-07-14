import json
import logging
from collections.abc import AsyncGenerator

from app.config import settings
from app.schemas.tool import ToolResponse
from app.services.ai.tools.orchestrator import ToolOrchestrator
from app.services.ai.tools.strategies import ToolInvocationStrategy

from .planner import Planner
from .state import ExecutionStateManager

logger = logging.getLogger(__name__)

class AgentExecutor:
    def __init__(
        self,
        planner: Planner,
        orchestrator: ToolOrchestrator,
        strategy: ToolInvocationStrategy,
        intent: str = "general",
    ):
        self.planner = planner
        self.orchestrator = orchestrator
        self.strategy = strategy
        self.intent = intent

    async def run(self, query: str, context: dict, messages: list[dict], tools_payload: list[dict]) -> str:
        state_mgr = ExecutionStateManager(query)
        final_answer = ""
        
        max_steps = settings.MAX_AGENT_STEPS if settings.ENABLE_MULTI_STEP_AGENT else 1
        
        while state_mgr.state.current_step < max_steps:
            state_mgr.increment_step()
            
            raw_response, has_tool, tool_requests, direct_text = await self.planner.plan_step(messages, tools_payload)
            
            if not has_tool:
                final_answer = direct_text
                break
                
            messages.extend(self.strategy.format_assistant_message(raw_response))
            
            tool_responses: list[ToolResponse] = []
            for req in tool_requests:
                if settings.ENABLE_TOOL_RESULT_CACHE:
                    cached_res = state_mgr.check_duplicate(req)
                    if cached_res:
                        logger.info(f"Using cached result for tool {req.name}")
                        tool_responses.append(cached_res)
                        state_mgr.record_skip(req)
                        continue
                
                tool_instance = self.orchestrator.registry.get_tool(req.name)
                if tool_instance and tool_instance.requires_confirmation:
                     # Halt bulk execution in non-streaming mode if it encounters unapproved tasks
                     err_res = ToolResponse(id=req.id, name=req.name, content="ERROR: Requires user confirmation. Use Plan Approval workflow.", is_error=True)
                     tool_responses.append(err_res)
                     continue
                
                try:
                    res = await self.orchestrator.execute_tool(req, context)
                    state_mgr.record_tool_result(req, res)
                    tool_responses.append(res)
                except Exception as e:
                    err_res = ToolResponse(id=req.id, name=req.name, content=str(e), is_error=True)
                    state_mgr.record_tool_result(req, err_res)
                    tool_responses.append(err_res)
            
            messages.extend(self.strategy.format_responses_to_messages(tool_responses, raw_tool_call=raw_response))
            
        state_mgr.terminate(final_answer)
        logger.info(f"Agent finished in {state_mgr.state.completed_steps} steps. State: {state_mgr.execution_id}")
        return final_answer
        
    async def stream_run(self, query: str, context: dict, messages: list[dict], tools_payload: list[dict]) -> AsyncGenerator[str, None]:
        state_mgr = ExecutionStateManager(query)
        final_answer = ""
        
        max_steps = settings.MAX_AGENT_STEPS if settings.ENABLE_MULTI_STEP_AGENT else 1
        
        while state_mgr.state.current_step < max_steps:
            state_mgr.increment_step()
            
            collected_response_obj = None
            full_text = ""
            is_tool_call_predicted = False
            
            async for chunk in self.planner.provider.stream_chat(messages, tools=tools_payload, intent=self.intent):
                if not isinstance(chunk, str):
                    is_tool_call_predicted = True
                    collected_response_obj = chunk
                    continue
                    
                full_text += chunk
                if "<tool_call" in full_text:
                    is_tool_call_predicted = True
                    continue
                    
                yield f"data: {json.dumps({'type': 'content', 'delta': chunk})}\n\n"

            if not is_tool_call_predicted:
                final_answer = full_text
                break
                
            source_payload = collected_response_obj if collected_response_obj else full_text
            has_tool, tool_requests = self.strategy.extract_requests(source_payload)
            
            if not has_tool:
                final_answer = full_text
                break
                
            requires_approval = False
            for req in tool_requests:
                tool_instance = self.orchestrator.registry.get_tool(req.name)
                if tool_instance and tool_instance.requires_confirmation:
                    requires_approval = True
                    break
                    
            if requires_approval:
                plan_payload = [{"id": r.id, "name": r.name, "arguments": r.arguments} for r in tool_requests]
                yield f"data: {json.dumps({'type': 'plan_approval', 'plan': plan_payload})}\n\n"
                state_mgr.terminate("Awaiting plan approval")
                break

            yield f"data: {json.dumps({'type': 'tool', 'name': 'Executing tools...'})}\n\n"
            
            messages.extend(self.strategy.format_assistant_message(source_payload))
            
            tool_responses: list[ToolResponse] = []
            for req in tool_requests:
                if settings.ENABLE_TOOL_RESULT_CACHE:
                    cached_res = state_mgr.check_duplicate(req)
                    if cached_res:
                        logger.info(f"Using cached result for tool {req.name}")
                        tool_responses.append(cached_res)
                        state_mgr.record_skip(req)
                        continue
                
                try:
                    res = await self.orchestrator.execute_tool(req, context)
                    state_mgr.record_tool_result(req, res)
                    tool_responses.append(res)
                except Exception as e:
                    err_res = ToolResponse(id=req.id, name=req.name, content=str(e), is_error=True)
                    state_mgr.record_tool_result(req, err_res)
                    tool_responses.append(err_res)
                    
            messages.extend(self.strategy.format_responses_to_messages(tool_responses, raw_tool_call=source_payload))
            
        state_mgr.terminate(final_answer)
        logger.info(f"Streaming Agent finished in {state_mgr.state.completed_steps} steps. State: {state_mgr.execution_id}")
