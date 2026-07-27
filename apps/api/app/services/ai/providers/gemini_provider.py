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

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        intent: str = "general",
    ):

        prompt_text = PromptBuilder.chat(messages)
        
        print("\n\n=== [DEBUG] EXACT CONTEXT SENT TO GEMINI (CHAT) ===")
        print(prompt_text)
        print("===================================================\n\n")

        import base64

        import google.genai.types as gt
        
        contents: list[Any] = [prompt_text]
        for msg in messages:
            if msg.get("images"):
                for b64_str in msg["images"]:
                    try:
                        contents.append(
                            gt.Part.from_bytes(
                                data=base64.b64decode(b64_str),
                                mime_type="image/jpeg",
                            )
                        )
                    except Exception:
                        pass
        
        gemini_tools: list[Any] = list(tools) if tools else []
            
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
        prompt_text = PromptBuilder.chat(messages)
        
        print("\n\n=== [DEBUG] EXACT CONTEXT SENT TO GEMINI (STREAM_CHAT) ===")
        print(prompt_text)
        print("==========================================================\n\n")

        import base64

        import google.genai.types as gt
        
        contents: list[Any] = [prompt_text]
        for msg in messages:
            if msg.get("images"):
                for b64_str in msg["images"]:
                    try:
                        contents.append(
                            gt.Part.from_bytes(
                                data=base64.b64decode(b64_str),
                                mime_type="image/jpeg",
                            )
                        )
                    except Exception:
                        pass

        gemini_tools: list[Any] = list(tools) if tools else []
        
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
    
    async def extract_memory(
        self,
        message: str,
    ) -> dict | None:

        prompt = f"""
    You are extracting long-term memory.

    Return ONLY valid JSON.

    If the sentence contains nothing worth remembering,
    return:

    null

    Otherwise return:

    {{
        "category":"personal|preference|goal|education|work|relationship",
        "key":"",
        "value":"",
        "confidence":0.95
    }}

    Sentence:

    {message}
    """

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        text = (response.text or "").strip()

        # Remove markdown code fences if present
        if text.startswith("```json"):
            text = text.replace("```json", "", 1)

        if text.startswith("```"):
            text = text.replace("```", "", 1)

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        print("\n" + "=" * 80)
        print("CLEANED RESPONSE:")
        print(text)
        print("=" * 80 + "\n")

        if text.lower() == "null":
            return None

        try:
            return json.loads(text)

        except Exception as e:
            print("JSON ERROR:", e)
            return None