import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any

from app.schemas.tool import ToolRequest, ToolResponse
from app.services.ai.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

class ToolInvocationStrategy(ABC):
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    @abstractmethod
    def get_system_prompt_extension(self) -> str:
        pass
        
    @abstractmethod
    def get_tools_for_provider(self) -> Any:
        pass

    @abstractmethod
    def extract_requests(self, response_text_or_obj: Any) -> tuple[bool, list[ToolRequest]]:
        pass
        
    @abstractmethod
    def format_assistant_message(self, response_text_or_obj: Any) -> list[dict]:
        pass

    @abstractmethod
    def format_responses_to_messages(self, responses: list[ToolResponse], raw_tool_call: Any = None) -> list[dict]:
        pass
        
    @abstractmethod
    def get_text_from_response(self, response_text_or_obj: Any) -> str:
        """Helper to extract pure displayable text from a provider response payload."""
        pass


class XmlFunctionStrategy(ToolInvocationStrategy):
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
You will receive the tool output in a <tool_response> block. You can only call ONE tool at a time!

CRITICAL INSTRUCTION: If the user queries a basic pleasantry, casual greeting, or conversational filler (e.g., 'hello', 'hey', 'how are you', 'who are you'), YOU MUST NOT INVOKE ANY TOOLS. Respond immediately with a friendly conversational greeting. Do not over-complicate chit-chat."""
        return prompt
        
    def get_tools_for_provider(self) -> Any:
        return None

    def extract_requests(self, response_text_or_obj: Any) -> tuple[bool, list[ToolRequest]]:
        if not isinstance(response_text_or_obj, str):
            # Might be streaming chunks accumulating, or an unexpected structure. We act safe.
            if hasattr(response_text_or_obj, "text"):
                response_text_or_obj = response_text_or_obj.text
            elif isinstance(response_text_or_obj, dict) and "message" in response_text_or_obj:
                response_text_or_obj = response_text_or_obj["message"].get("content", "")
            else:
                return False, []
            
        if not isinstance(response_text_or_obj, str): return False, []
            
        match = re.search(r'<tool_call>\s*(.*?)\s*</tool_call>', response_text_or_obj, re.DOTALL)
        if not match:
            return False, []
            
        raw_json = match.group(1)
        try:
            call_data = json.loads(raw_json)
            req = ToolRequest(
                id=match.group(0),
                name=call_data.get("name", "unknown"),
                arguments=call_data.get("args", {})
            )
            return True, [req]
            
        except json.JSONDecodeError:
            req = ToolRequest(id=match.group(0), name="PARSE_ERROR", arguments={})
            return True, [req]
            
    def format_assistant_message(self, response_text_or_obj: Any) -> list[dict]:
        text = self.get_text_from_response(response_text_or_obj)
        return [{"role": "assistant", "content": text}]
            
    def format_responses_to_messages(self, responses: list[ToolResponse], raw_tool_call: Any = None) -> list[dict]:
        if not responses:
            return []
            
        res = responses[0]
        original_xml = res.id if res.id else getattr(raw_tool_call, "id", "unknown_xml")
        
        tool_msg_content = f"Tool execution result for:\n{original_xml}\n\n<tool_response>\n{res.content}\n</tool_response>"
        return [{"role": "user", "content": tool_msg_content}]
        
    def get_text_from_response(self, response_text_or_obj: Any) -> str:
        if isinstance(response_text_or_obj, str):
            return response_text_or_obj
        if hasattr(response_text_or_obj, "text"):
            return response_text_or_obj.text or ""
        return str(response_text_or_obj)


class NativeFunctionStrategy(ToolInvocationStrategy):
    def get_system_prompt_extension(self) -> str:
        return "CRITICAL INSTRUCTION: If the user queries a basic pleasantry, casual greeting, or conversational filler (e.g., 'hello', 'hey', 'how are you', 'who are you'), YOU MUST NOT INVOKE ANY TOOLS. Respond immediately with a friendly conversational greeting. Do not over-complicate chit-chat."
        
    def get_tools_for_provider(self) -> Any:
        schemas = self.registry.get_all_schemas()
        if not schemas:
            return None
            
        tools = []
        for s in schemas:
            # We map JSON schema to Python types natively accepted by genai list of dictionaries
            parameters = s.get("parameters", {"type": "object", "properties": {}})
            tools.append({
                "function_declarations": [{
                    "name": s["name"],
                    "description": s["description"],
                    "parameters": parameters,
                }]
            })
        return tools

    def extract_requests(self, response_text_or_obj: Any) -> tuple[bool, list[ToolRequest]]:
        if not hasattr(response_text_or_obj, "function_calls") or not response_text_or_obj.function_calls:
             return False, []
             
        requests = []
        for call in response_text_or_obj.function_calls:
             req = ToolRequest(
                 id=call.name,  # ID tracing by name
                 name=call.name,
                 arguments=dict(call.args) if call.args else {}
             )
             requests.append(req)
             
        return True, requests
        
    def format_assistant_message(self, response_text_or_obj: Any) -> list[dict]:
        # Google expects native history appending to encompass function calls explicitly via Parts list
        parts = []
        if hasattr(response_text_or_obj, "text") and response_text_or_obj.text:
             parts.append({"text": response_text_or_obj.text})
             
        if hasattr(response_text_or_obj, "function_calls") and response_text_or_obj.function_calls:
             for call in response_text_or_obj.function_calls:
                 parts.append({
                     "functionCall": {
                         "name": call.name,
                         "args": dict(call.args) if call.args else {}
                     }
                 })
                 
        if not parts:
            parts.append({"text": ""})
            
        return [{"role": "model", "parts": parts}]

    def format_responses_to_messages(self, responses: list[ToolResponse], raw_tool_call: Any = None) -> list[dict]:
        parts = []
        for res in responses:
             parts.append({
                 "functionResponse": {
                     "name": res.name,
                     "response": {"content": res.content, "status": "ERROR" if res.is_error else "OK"}
                 }
             })
        return [{"role": "user", "parts": parts}]
        
    def get_text_from_response(self, response_text_or_obj: Any) -> str:
        if isinstance(response_text_or_obj, str):
            return response_text_or_obj
        if hasattr(response_text_or_obj, "text"):
            return response_text_or_obj.text or ""
        return ""

