import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from app.services.ai.prompts import PromptBuilder
from app.services.ai.providers.base import BaseLLMProvider
from app.services.ai.providers.exceptions import ProviderError, ProviderTransientError
from app.services.ai.providers.metadata import ProviderMetadata


class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(self, api_key: str, base_url: str, model_name: str, provider_name: str):
        self.api_key = api_key
        self.base_url = base_url if not base_url.endswith("/") else base_url[:-1]
        self.model = model_name
        self.provider_name = provider_name
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ayushverma", 
            "X-Title": "SecondBrain_AI"
        }

    @property
    def name(self) -> str:
        return self.provider_name

    async def get_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            supported_models=[self.model],
            context_window=100000, 
            supports_streaming=True,
            supports_vision=False,
            supports_native_tools=True,
            supports_parallel_tools=True,
            supports_tool_streaming=False,
            estimated_cost_tier=1,
            is_local=False,
        )

    async def check_health(self) -> bool:
        try:
            # We can perform a lightweight list models request
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{self.base_url}/models", headers=self.headers, timeout=5.0)
                return res.status_code == 200
        except Exception:
            return False

    def _convert_tools(self, tools: list[dict] | None) -> list[dict] | None:
        if not tools:
            return None
            
        openai_tools = []
        for t in tools:
            # Assumes Gemini/Standard tool schemas are converted correctly or tools are sent in OpenAI format
            # Normally tool orchestrators output OpenAI compatible json.
            func_dict = t.get("functionDeclarations", [])
            if not func_dict:
                if "type" in t and t["type"] == "function":
                    # Perhaps it's already OpenAI schema
                    openai_tools.append(t)
            else:
                for func in func_dict:
                    openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": func.get("name"),
                            "description": func.get("description", ""),
                            "parameters": func.get("parameters", {})
                        }
                    })
        return openai_tools if openai_tools else None

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        intent: str = "general",
    ):
        def flatten_openai_msg(m):
            if "parts" in m:
                role = "assistant" if m.get("role") == "model" else m.get("role", "user")
                tool_calls = []
                content = ""
                tool_responses = []
                import json
                for p in m["parts"]:
                    if "text" in p:
                        content += p["text"]
                    elif "functionCall" in p:
                        fc = p["functionCall"]
                        tool_calls.append({
                            "id": fc.get("name"), 
                            "type": "function",
                            "function": {
                                "name": fc.get("name"),
                                "arguments": json.dumps(fc.get("args", {}))
                            }
                        })
                    elif "functionResponse" in p:
                         fr = p["functionResponse"]
                         resp_data = fr.get("response", "")
                         if isinstance(resp_data, dict):
                             content_str = json.dumps(resp_data)
                         else:
                             content_str = str(resp_data)
                         tool_responses.append({
                             "role": "tool",
                             "tool_call_id": fr.get("name"),
                             "content": content_str
                         })
                if tool_responses:
                    return tool_responses
                msg_dict = {"role": role, "content": content}
                if tool_calls:
                     msg_dict["tool_calls"] = tool_calls
                return msg_dict
            return m
            
        flat_messages = []
        for msg in messages:
            res = flatten_openai_msg(msg)
            if isinstance(res, list):
                flat_messages.extend(res)
            else:
                flat_messages.append(res)
                
        converted_tools = self._convert_tools(tools)
        payload = {
            "model": self.model,
            "messages": flat_messages,
            "stream": False,
        }
        if converted_tools:
            payload["tools"] = converted_tools
            # For native tool calling we might also need tool_choice

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                
                # We need to construct a response that NativeFunctionStrategy can parse if tooling fires.
                # However we'll return raw data or simple string if no tools.
                msg = data["choices"][0]["message"]
                
                if msg.get("tool_calls"):
                    class MockCall:
                        def __init__(self, name, args):
                            self.name = name
                            self.args = args

                    class MockResponse:
                        def __init__(self, calls, text):
                            self.function_calls = calls
                            self.text = text
                            
                    calls = []
                    for tc in msg.get("tool_calls"):
                        func = tc.get("function", {})
                        args_str = func.get("arguments", "{}")
                        try:
                             args = json.loads(args_str)
                        except Exception:
                             args = {}
                             
                        # Map OpenAI tool logic seamlessly to Gemini's expected execution structural properties
                        calls.append(MockCall(name=func.get("name"), args=args))
                        
                    return MockResponse(calls, msg.get("content") or "")
                
                return msg.get("content") or ""
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 408, 500, 502, 503, 504):
                raise ProviderTransientError(f"{self.provider_name} API transient failure ({e.response.status_code}): {e.response.text}")
            else:
                raise ProviderError(f"{self.provider_name} non-transient API failure ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            raise ProviderTransientError(f"{self.provider_name} API failure: {str(e)}")

    async def generate_title(self, first_message: str) -> str:
        prompt = PromptBuilder.title(first_message)
        msgs = [{"role": "user", "content": prompt}]
        try:
            res = await self.chat(msgs)
            if isinstance(res, str):
                return res.strip()
            return ""
        except Exception:
            return "New Conversation"

    async def extract_memory(self, message: str) -> dict | None:
        return None

    async def stream_chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        intent: str = "general",
    ) -> AsyncGenerator[Any, None]:
        def flatten_openai_msg(m):
            if "parts" in m:
                role = "assistant" if m.get("role") == "model" else m.get("role", "user")
                tool_calls = []
                content = ""
                tool_responses = []
                import json
                for p in m["parts"]:
                    if "text" in p:
                        content += p["text"]
                    elif "functionCall" in p:
                        fc = p["functionCall"]
                        tool_calls.append({
                            "id": fc.get("name"), 
                            "type": "function",
                            "function": {
                                "name": fc.get("name"),
                                "arguments": json.dumps(fc.get("args", {}))
                            }
                        })
                    elif "functionResponse" in p:
                         fr = p["functionResponse"]
                         resp_data = fr.get("response", "")
                         if isinstance(resp_data, dict):
                             content_str = json.dumps(resp_data)
                         else:
                             content_str = str(resp_data)
                         tool_responses.append({
                             "role": "tool",
                             "tool_call_id": fr.get("name"),
                             "content": content_str
                         })
                if tool_responses:
                    return tool_responses
                msg_dict = {"role": role, "content": content}
                if tool_calls:
                     msg_dict["tool_calls"] = tool_calls
                return msg_dict
            return m
            
        flat_messages = []
        for msg in messages:
            res = flatten_openai_msg(msg)
            if isinstance(res, list):
                flat_messages.extend(res)
            else:
                flat_messages.append(res)
                
        converted_tools = self._convert_tools(tools)
        payload = {
            "model": self.model,
            "messages": flat_messages,
            "stream": True,
        }
        if converted_tools:
            payload["tools"] = converted_tools

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk["choices"][0]["delta"]
                                if content := delta.get("content"):
                                    yield content
                            except Exception:
                                pass
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 408, 500, 502, 503, 504):
                raise ProviderTransientError(f"{self.provider_name} API transient streaming failure ({e.response.status_code}): {e.response.text}")
            else:
                raise ProviderError(f"{self.provider_name} non-transient API streaming failure ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            raise ProviderTransientError(f"{self.provider_name} streaming failure: {str(e)}")
