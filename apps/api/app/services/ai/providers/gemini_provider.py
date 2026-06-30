from collections.abc import AsyncGenerator
from email.mime import text

from google import genai
import json

from app.config import get_settings
from app.services.ai.prompts import PromptBuilder
from app.services.ai.providers.base import BaseLLMProvider

settings = get_settings()


class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

        self.model = settings.GEMINI_MODEL

    async def chat(
        self,
        messages: list[dict],
    ) -> str:

        prompt = PromptBuilder.chat(messages)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        return response.text

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

        return response.text.strip()

    async def stream_chat(
        self,
        messages: list[dict],
    ) -> AsyncGenerator[str, None]:
        raise NotImplementedError
    
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

        text = response.text.strip()

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