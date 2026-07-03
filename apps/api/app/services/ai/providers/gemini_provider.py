from collections.abc import AsyncGenerator
from email.mime import text

from google import genai
import json

from app.config import get_settings
from app.services.ai.prompts import PromptBuilder
from app.services.ai.providers.base import BaseLLMProvider
from app.services.ai.providers.metadata import ProviderMetadata
from app.services.ai.providers.exceptions import ProviderTransientError

settings = get_settings()


class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

        self.model = settings.GEMINI_MODEL

    @property
    def name(self) -> str:
        return "gemini"

    async def get_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            supported_models=[self.model],
            context_window=1000000,
            supports_streaming=True,
            supports_vision=True,
            supports_function_calling=True,
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
    ) -> str:

        prompt = PromptBuilder.chat(messages)
        
        print("\n\n=== [DEBUG] EXACT CONTEXT SENT TO GEMINI (CHAT) ===")
        print(prompt)
        print("===================================================\n\n")

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text or ""
        except Exception as e:
            raise ProviderTransientError(f"Gemini API failure: {str(e)}")

    async def generate_title(
        self,
        first_message: str,
    ) -> str:

        prompt = PromptBuilder.title(
            first_message,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        return (response.text or "").strip()

    async def stream_chat(
        self,
        messages: list[dict],
    ) -> AsyncGenerator[str, None]:
        prompt = PromptBuilder.chat(messages)
        
        print("\n\n=== [DEBUG] EXACT CONTEXT SENT TO GEMINI (STREAM_CHAT) ===")
        print(prompt)
        print("==========================================================\n\n")

        # Utilize Google SDK's native async client
        try:
            response = await self.client.aio.models.generate_content_stream(
                model=self.model,
                contents=prompt,
            )

            async for chunk in response:
                if chunk.text:
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

        response = self.client.models.generate_content(
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