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

    async def generate_plan(self, query: str, context_messages: list[dict] | None = None) -> dict[str, Any] | None:
        memory_context = ""
        if context_messages and len(context_messages) > 0 and context_messages[0].get("role") == "system":
            sys_content = context_messages[0].get("content", "")
            if "=== RELEVANT MEMORIES ===" in sys_content:
                memory_parts = sys_content.split("=== RELEVANT MEMORIES ===")
                if len(memory_parts) > 1:
                    memory_context = "=== RELEVANT MEMORIES ===" + memory_parts[1].split("===")[0]

        import datetime
        current_time = datetime.datetime.now().astimezone().isoformat()

        system_prompt = f"""You are an architectural planning agent. Your job is to evaluate the user's request and output a strict JSON plan.
The current local date and time is: {current_time}
IMPORTANT: When outputting timestamps for arguments, you MUST preserve the timezone offset exactly as provided in the local time. DO NOT convert to UTC ('Z') unless requested.

Do NOT attempt to fulfill the user's request. Only output the plan.

{memory_context}

You must decide:
1. `tools_needed`: true/false (Do we need ANY tools to fulfill the user's request, such as web_search, weather, calendar scheduling, email, opening/launching desktop apps, playing music/media, system controls, etc? Almost ALL user commands require tools.)
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
- For calendar event scheduling, you MUST use 'start_time' and 'end_time' with absolute ISO-8601 date-time strings. Do NOT use relative offsets (like time_offset_hours).
- Do NOT schedule 'Knowledge Search' or 'Image Retrieval' for conversational chatter, user names, or self-introductions (e.g., "my name is X").
- When a document is attached, do NOT assume its semantic or visual content from the filename alone. Do NOT schedule 'Image Retrieval' or external knowledge searches based solely on a filename. 
- ONLY schedule 'Image Retrieval' if the user explicitly asks for pictures, or if the core informational intent heavily relies on visual context (e.g. famous landmarks, artwork, or specific products).
- When generating `tool_arguments` for search capabilities, you MUST use exact, concise entity names or keywords in a `query` parameter (e.g. `{{"query": "Narendra Modi"}}`). If the user explicitly excludes a topic, use a minus sign (e.g. `{{"query": "India news -business"}}`). NEVER use conversational questions.

Return EXACTLY and ONLY a valid JSON object matching the above keys.
"""
        if context_messages and len(context_messages) > 1 and context_messages[0].get("role") == "system":
            clean_context = [{"role": m.get("role", ""), "content": m.get("content", "")} for m in context_messages[1:]]
            messages = [{"role": "system", "content": system_prompt}] + clean_context
        else:
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
            end = result.rfind("}")
            if start != -1 and end != -1 and end >= start:
                plan_json = typing.cast(dict[str, Any], json.loads(result[start:end+1]))
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
            end = result.rfind("}")
            if start != -1 and end != -1 and end >= start:
                new_task = typing.cast(dict[str, Any], json.loads(result[start:end+1]))
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
            "   IMPORTANT: For simple actions (like playing music, opening websites, setting timers), provide a short, natural, conversational confirmation (e.g. 'Playing Loser on YouTube Music for you!'). NEVER output robotic status lists, bullet points of 'Command / Status / Service', or raw JSON keys in your final response to the user.\n"
            f"2. TASKS TO EXECUTE:\n{tasks}\n"
            "3. TOOL EXECUTION RULE: You must execute the tools needed for these tasks BEFORE writing your final response. "
            "If tasks are distinct, execute them in parallel tool calls within a single turn.\n"
            "==========================================================\n"
        )
        return instruction
