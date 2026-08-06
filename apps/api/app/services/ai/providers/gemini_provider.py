import json
from collections.abc import AsyncGenerator
from typing import Any

from google import genai

from app.config import get_settings
from app.services.ai.prompts import PromptBuilder
from app.services.ai.providers.base import BaseLLMProvider
from app.services.ai.providers.exceptions import ProviderTransientError
from app.services.ai.providers.metadata import ProviderMetadata

settings = get_settings()


class GeminiProvider(BaseLLMProvider):
    def __init__(self, model_name: str | None = None, provider_name: str = "gemini"):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

        self.model = model_name or settings.GEMINI_MODEL
        self.provider_name = provider_name

    @property
    def name(self) -> str:
        return self.provider_name

    async def get_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            supported_models=[self.model],
            context_window=1000000,
            supports_streaming=True,
            supports_vision=True,
            supports_native_tools=True,
            supports_parallel_tools=True,
            supports_tool_streaming=False,
            estimated_cost_tier=3,
            is_local=False,
        )

    async def check_health(self) -> bool:
        try:
            self.client.models.generate_content(
                model=self.model,
                contents="ping",
            )
            return True
        except Exception:
            return False

    def _build_contents(self, messages: list[dict]) -> list[Any]:
        import base64
        import json
        import google.genai.types as gt
        
        raw_contents = []
        for msg in messages:
            role = "model" if msg.get("role") == "assistant" else "user"
            parts = []
            
            # 1. Text Content
            if msg.get("content"):
                # Tool responses have role="tool". In Gemini, they are part of the user's turn
                if msg.get("role") == "tool":
                    name = msg.get("tool_call_id", "unknown_tool")
                    content_str = msg.get("content", "{}")
                    try:
                        resp_dict = json.loads(content_str)
                    except Exception:
                        resp_dict = {"result": content_str}
                    parts.append(gt.Part.from_function_response(name=name, response=resp_dict))
                else:
                    parts.append(gt.Part.from_text(text=msg["content"]))
                    
            # 2. Image Content
            if msg.get("images"):
                for b64 in msg["images"]:
                    try:
                        parts.append(gt.Part.from_bytes(data=base64.b64decode(b64), mime_type="image/jpeg"))
                    except Exception:
                        pass
                        
            # 3. Tool Calls (Assistant requesting a tool)
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    func = tc.get("function", {})
                    name = func.get("name")
                    args_str = func.get("arguments", "{}")
                    try:
                        args = json.loads(args_str)
                    except Exception:
                        args = {}
                    if name:
                        parts.append(gt.Part.from_function_call(name=name, args=args))
                        
            if parts:
                raw_contents.append(gt.Content(role=role, parts=parts))
                
        # Group consecutive same-role messages
        contents: list[gt.Content] = []
        for c in raw_contents:
            if contents and contents[-1].role == c.role:
                if contents[-1].parts is None:
                    contents[-1].parts = []
                if c.parts:
                    contents[-1].parts.extend(c.parts)
            else:
                contents.append(c)
                
        return contents

    def _convert_tools(self, tools: list[dict] | None) -> list[Any] | None:
        if not tools:
            return None
            
        import google.genai.types as gt
        
        func_decls = []
        for t in tools:
            if t.get("type") == "function" and "function" in t:
                func = t["function"]
                name = func.get("name")
                desc = func.get("description", "")
                params = func.get("parameters", {"type": "OBJECT", "properties": {}})
                if name:
                    func_decls.append(gt.FunctionDeclaration(
                        name=name,
                        description=desc,
                        parameters=params
                    ))
                    
        gemini_tools = []
        if func_decls:
            gemini_tools.append(gt.Tool(function_declarations=func_decls))
            
        return gemini_tools if gemini_tools else None

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        intent: str = "general",
    ):

        contents = self._build_contents(messages)
        
        gemini_tools = self._convert_tools(tools) or []
            
        if "lite" not in self.model.lower():
            import google.genai.types as gt
            try:
                # Add native search grounding properly formatted using the SDK schema
                gemini_tools.append(gt.Tool(google_search=gt.GoogleSearch()))
            except Exception:
                pass

        config = None
        if gemini_tools:
            import google.genai.types as gt
            config = gt.GenerateContentConfig(tools=gemini_tools)

        try:
            if config:
                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config,
                )
            else:
                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=contents,
                )
            # Return the raw object if it contains function calls, otherwise return text
            if response.function_calls:
                return response
            return response.text or ""
        except Exception as e:
            raise ProviderTransientError(f"Gemini API failure: {str(e)}")

    async def generate_title(
        self,
        ai_response: str,
    ) -> str:

        prompt = PromptBuilder.title(
            ai_response,
        )

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        return (response.text or "").strip()

    async def stream_chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        intent: str = "general",
    ) -> AsyncGenerator[Any, None]:
        contents = self._build_contents(messages)

        gemini_tools = self._convert_tools(tools) or []
        
        if "lite" not in self.model.lower():
            import google.genai.types as gt
            try:
                gemini_tools.append(gt.Tool(google_search=gt.GoogleSearch()))
            except Exception:
                pass

        config = None
        if gemini_tools:
            import google.genai.types as gt
            config = gt.GenerateContentConfig(tools=gemini_tools)
            
        # Utilize Google SDK's native async client
        try:
            if config:
                response = await self.client.aio.models.generate_content_stream(
                    model=self.model,
                    contents=contents,
                    config=config,
                )
            else:
                response = await self.client.aio.models.generate_content_stream(
                    model=self.model,
                    contents=contents,
                )

            async for chunk in response:
                if chunk.function_calls:
                    yield chunk
                elif chunk.text:
                    yield chunk.text
        except Exception as e:
            raise ProviderTransientError(f"Gemini stream failure: {str(e)}")