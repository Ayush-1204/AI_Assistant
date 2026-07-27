import json
import logging

from app.schemas.ai_pipeline import CuratedContext, ImageReference, NormalizedToolResult
from app.services.ai.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

class EditorStage:
    """
    Curates a list of Validated Tool Results into a clean CuratedContext.
    Merges duplicate facts, formats cleanly, but NEVER adds hallucinated data.
    """
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def curate(self, query: str, results: list[NormalizedToolResult]) -> CuratedContext:
        if not results:
            return CuratedContext(summary="No valid information retrieved.", missing_information=[query])

        # Extract all content
        raw_facts = []
        all_images = []
        for r in results:
            raw_facts.append(f"[{r.tool_name}] {r.normalizedData.get('content', r.rawData)}")
            all_images.extend(r.images)
            
        combined_facts_str = "\n\n".join(raw_facts)

        prompt = f"""You are an Editor. Merge and summarize the following retrieved facts into a clean, structured object answering the query: "{query}".
DO NOT invent any facts. If information is missing, explicitly list it in `missing_information`.

Retrieved Data:
{combined_facts_str}

Return EXACTLY a JSON object matching this schema:
{{
  "summary": "A clean, concise 2-3 sentence overview.",
  "merged_facts": ["fact 1", "fact 2", "fact 3"],
  "missing_information": ["missing query part 1"]
}}
"""
        messages = [
            {"role": "system", "content": "You are a strict data editor outputting ONLY JSON."},
            {"role": "user", "content": prompt}
        ]

        try:
            import typing
            from app.services.ai.providers.router import ProviderRouter
            router_inst = typing.cast(ProviderRouter, self.provider)
            
            edit_result = await router_inst.chat(messages, intent="structured")
            start = edit_result.find("{")
            end = edit_result.rfind("}") + 1
            if start != -1 and end != -1:
                edit_json = json.loads(edit_result[start:end])
                
                # Curate images (e.g. sort by relevance or dedup)
                unique_urls = set()
                curated_images = []
                for img in all_images:
                    if img.url not in unique_urls:
                        unique_urls.add(img.url)
                        curated_images.append(img)
                        
                return CuratedContext(
                    summary=edit_json.get("summary", ""),
                    merged_facts=edit_json.get("merged_facts", []),
                    missing_information=edit_json.get("missing_information", []),
                    curated_images=curated_images
                )
        except Exception as e:
            logger.warning(f"[Editor] Failed to run LLM edit: {str(e)}")

        return CuratedContext(
            summary="Raw concatenated results due to Editor failure.",
            merged_facts=[combined_facts_str]
        )
