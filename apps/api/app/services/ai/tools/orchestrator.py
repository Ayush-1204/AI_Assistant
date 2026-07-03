import json
import re
from app.services.ai.tools.registry import ToolRegistry

class ToolOrchestrator:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def get_system_prompt_extension(self) -> str:
        schemas = self.registry.get_all_schemas()
        if not schemas:
            return ""
            
        prompt = "\n\n=== TOOL USAGE ===\n"
        prompt += "You have access to the following action tools:\n"
        for s in schemas:
            prompt += f"- {s['name']}: {s['description']}\n  Arguments: {json.dumps(s['parameters'])}\n"
            
        prompt += """\nTo execute a tool, YOU MUST output EXACTLY the following XML block containing JSON:
<tool_call>
{"name": "tool_name", "args": {"arg1": "value1"}}
</tool_call>
You will receive the tool output in a <tool_response> block. You can only call ONE tool at a time!"""
        return prompt

    async def extract_and_execute(self, response_text: str, context: dict) -> tuple[bool, str, str]:
        """
        Extracts tool call, executes it, and returns (has_tool_call, raw_tool_call_text, tool_result)
        """
        match = re.search(r'<tool_call>\s*(.*?)\s*</tool_call>', response_text, re.DOTALL)
        if not match:
            return False, "", ""
            
        raw_json = match.group(1)
        try:
            call_data = json.loads(raw_json)
            name = call_data.get("name")
            args = call_data.get("args", {})
            
            tool = self.registry.get_tool(name)
            if not tool:
                return True, match.group(0), f"Error: Tool '{name}' not found natively."
                
            result = await tool.execute(execution_context=context, **args)
            return True, match.group(0), str(result)
            
        except json.JSONDecodeError:
            return True, match.group(0), "Error: Invalid JSON object payload."
        except Exception as e:
            return True, match.group(0), f"Error executing internal tool: {str(e)}"
