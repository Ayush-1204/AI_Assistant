import json
import logging
from typing import Any

from app.services.ai.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class UpfrontPlanner:
    """
    Evaluates the user's request BEFORE the main executor loop begins,
    outputting a strict JSON plan detailing tasks, output structure, and tools needed.
    """
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def generate_plan(self, query: str) -> dict[str, Any] | None:
        system_prompt = """You are an architectural planning agent. Your job is to evaluate the user's request and output a strict JSON plan.
Do NOT attempt to fulfill the user's request. Only output the plan.

You must decide:
1. `tools_needed`: true/false (Do we need external tools like web_search, image_search, weather, etc?)
2. `output_structure`: One of [direct_answer, step_by_step_guide, news_briefing, checklist, comparison, report, snippet]
3. `is_parallelizable`: true/false (Can the required tasks run concurrently?)
4. `tasks`: A list of detailed objects representing the execution graph. Each task MUST have:
   - `id`: unique string ID
   - `name`: Human readable task name
   - `capability`: The abstract capability required (e.g. 'Current News Search', 'Local Weather', 'Image Retrieval'). DO NOT specify concrete tool names.
   - `tool_arguments`: JSON object of arguments for the tool
   - `dependencies`: list of task IDs that must complete before this runs (empty if independent)
   - `expectedOutput`: What you expect this capability to return
5. `reasoning`: A short explanation of why this plan was chosen.

CRITICAL INSTRUCTION: If the request requires multiple independent facts or news topics, you MUST break them down into separate, independent tasks in the `tasks` array. Do NOT group them into a single broad task.
- For weather requests, the 'Local Weather' capability automatically handles user geolocation internally. Do NOT create separate geolocation tasks for weather.

Return EXACTLY and ONLY a valid JSON object matching the above keys.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        try:
            # We explicitly route this to a fast model (intent='general')
            import typing
            from app.services.ai.providers.router import ProviderRouter
            router_inst = typing.cast(ProviderRouter, self.provider)
            
            result = await router_inst.chat(messages, intent="structured")
            start = result.find("{")
            end = result.rfind("}") + 1
            if start != -1 and end != -1:
                plan_json = json.loads(result[start:end])
                logger.info(f"[UpfrontPlanner] Generated plan: {plan_json}")
                return plan_json
        except Exception as e:
            logger.warning(f"[UpfrontPlanner] Failed to generate plan: {str(e)}")
            
        return None

    async def replan_branch(self, query: str, failed_task: dict, failure_reason: str) -> dict[str, Any] | None:
        """
        Dynamically generate an alternate task to fulfill a capability that failed.
        """
        prompt = f"""You are a replanning agent. A task in the execution graph has failed.
User Query: {query}
Failed Task ID: {failed_task.get("id")}
Failed Capability: {failed_task.get("capability")}
Reason for failure: {failure_reason}

You must generate an alternate ExecutionTask (in JSON format) to recover this branch.
Maybe try a different capability, or change the tool arguments.

Return ONLY the JSON object for the single new ExecutionTask:
{{
   "id": "new_task_id",
   "name": "Human readable name",
   "capability": "New Capability (e.g. 'Wikipedia Search' instead of 'News Search')",
   "tool_arguments": {{...}},
   "dependencies": [],
   "expectedOutput": "..."
}}
"""
        messages = [
            {"role": "system", "content": "You are a strict replanning agent outputting ONLY JSON."},
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
                new_task = json.loads(result[start:end])
                logger.info(f"[UpfrontPlanner] Generated replan task: {new_task}")
                return new_task
        except Exception as e:
            logger.warning(f"[UpfrontPlanner] Failed to replan: {str(e)}")
            
        return None

    def format_plan_as_system_instruction(self, plan: dict[str, Any]) -> str:
        """
        Converts the JSON plan into a strict system prompt instruction for the main executor.
        """
        tasks = ""
        for t in plan.get("tasks", []):
            deps = f" (Depends on: {t.get('dependencies')})" if t.get('dependencies') else ""
            tasks += f"- [{t.get('id')}] {t.get('name')} -> capability: {t.get('capability')}{deps}\n"
        
        structure = plan.get("output_structure", "direct_answer")
        
        instruction = (
            "\n\n==========================================================\n"
            "UPFRONT EXECUTION PLAN (MANDATORY):\n"
            "You are strictly bound to the following execution plan. You must not deviate.\n"
            f"1. OUTPUT STRUCTURE REQUIRED: '{structure}'. You must format your final response to perfectly match this layout.\n"
            f"2. TASKS TO EXECUTE:\n{tasks}\n"
            "3. TOOL EXECUTION RULE: You must execute the tools needed for these tasks BEFORE writing your final response. "
            "If tasks are distinct, execute them in parallel tool calls within a single turn.\n"
            "==========================================================\n"
        )
        return instruction
