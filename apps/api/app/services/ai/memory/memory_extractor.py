import json
import typing
from app.services.ai.providers.base import BaseLLMProvider


class MemoryExtractor:
    """
    Uses the configured LLM provider to extract
    structured memory from user messages.
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
    ):
        self.provider = provider

    def _clean_json(self, text: str) -> str:
        if text.startswith("```json"):
            text = text.replace("```json", "", 1)
        if text.startswith("```"):
            text = text.replace("```", "", 1)
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    async def extract(
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
        "value":"(Must be a full, descriptive sentence)",
        "confidence":0.95
    }}

    Sentence:

    {message}
    """
        try:
            response_text = await self.provider.chat(
                [{"role": "user", "content": prompt}],
                intent="structured"
            )
            cleaned = self._clean_json(response_text)
            
            if cleaned.lower() == "null":
                return None
                
            return typing.cast(dict, json.loads(cleaned))
        except Exception as e:
            print("JSON ERROR:", e)
            return None

    async def extract_from_chunks(
        self,
        text: str,
    ) -> list[dict]:

        prompt = f"""
    You are extracting HIGH-LEVEL metadata about the user based on the documents they upload.
    Only extract broad, stable user-specific themes (e.g., "The user is studying X", "The user works in Y industry", "The user is interested in Z").
    
    CRITICAL RESTRICTION: You MUST NOT extract specific details, facts, numbers, or deep summaries of the document's actual subject matter. We only want to know what the document implies about the USER'S life, work, or education. Do NOT save memories about the document itself.

    Return ONLY valid JSON as a list of objects.

    If nothing is worth remembering, return:
    []

    Otherwise return:
    [
      {{
          "category":"personal|preference|goal|education|work|relationship",
          "key":"Name of fact",
          "value":"Value of fact (Must be a full, descriptive sentence)",
          "confidence":0.95
      }}
    ]

    Document Text:
    {text}
    """
        try:
            response_text = await self.provider.chat(
                [{"role": "user", "content": prompt}],
                intent="structured"
            )
            cleaned = self._clean_json(response_text)
            
            if cleaned == "[]" or not cleaned:
                return []
                
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                return parsed
            return []
        except Exception as e:
            print("JSON ERROR in extract_from_chunks:", e)
            return []