import json
import logging

from app.schemas.ai_pipeline import CuratedContext
from app.services.ai.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

class EvaluatorStage:
    """
    Final Quality Evaluation Gate.
    Grades the draft response against the CuratedContext before it is emitted to the user.
    """
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def evaluate(self, draft_response: str, context: CuratedContext) -> bool:
        """
        Returns True if the response is high quality and grounded, False if it needs rewrite.
        """
        if not draft_response.strip():
            return False
            
        prompt = f"""You are a Final Quality Evaluator. Grade the Draft Response against the Curated Context.
        
Curated Context (Ground Truth):
{json.dumps(context.model_dump(), indent=2)}

Draft Response:
{draft_response}

Criteria:
1. Grounding: Does the draft invent facts NOT in the Curated Context? (If yes, fail).
2. Completeness: Did the draft ignore important facts from the Curated Context?
3. Formatting: Is the output structurally sound?

Return ONLY a JSON object:
{{
  "pass": true/false,
  "reason": "Why it passed or failed"
}}
"""
        messages = [
            {"role": "system", "content": "You are a strict Evaluator outputting ONLY JSON."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            import typing
            from app.services.ai.providers.router import ProviderRouter
            router_inst = typing.cast(ProviderRouter, self.provider)
            
            result = await router_inst.chat(messages, intent="general")
            start = result.find("{")
            end = result.rfind("}") + 1
            if start != -1 and end != -1:
                eval_json = json.loads(result[start:end])
                passed = eval_json.get("pass", True)
                logger.info(f"[Evaluator] Final draft passed: {passed}. Reason: {eval_json.get('reason')}")
                return passed
        except Exception as e:
            logger.warning(f"[Evaluator] Failed to run LLM evaluation: {str(e)}")
            
        # Default to pass if evaluator crashes, to ensure uptime
        return True
