import json
import logging

from app.schemas.ai_pipeline import NormalizedToolResult, ValidationReport
from app.services.ai.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

class ValidatorStage:
    """
    Evaluates the NormalizedToolResult against strict freshness, relevance, and hallucination rules.
    Acts as a firewall to prevent bad tool outputs from reaching the writer.
    """
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def validate(self, query: str, result: NormalizedToolResult) -> ValidationReport:
        if result.confidence < 0.5:
            return ValidationReport(is_trustworthy=False, confidence_score=result.confidence, reason="Tool execution failed or returned very low confidence natively.")

        import datetime
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        prompt = f"""You are a strict data validator. Your job is to evaluate if a piece of retrieved information is trustworthy, relevant, and fresh for the user's query.

Current Date/Time: {current_time}

User Query: {query}
Tool Used: {result.tool_name}
Data to evaluate: {result.normalizedData.get("content", result.rawData)}

Evaluate on:
1. Relevance (Does it answer or help answer the query? NOTE: If the Tool Used is 'image_search', evaluate relevance strictly on whether the images conceptually match the query subject matter. DO NOT fail image tools for lacking text instructions.)
2. Missing Info (Is it empty, filler, or "I don't know"?)
3. Freshness (If the query asks for 'latest' or 'today', is this data recent?)

Return EXACTLY a JSON object:
{{
  "is_trustworthy": true/false,
  "confidence_score": 0.0-1.0,
  "reason": "Short explanation",
  "retry_suggested": true/false
}}
"""
        messages = [
            {"role": "system", "content": "You are a strict data validator outputting ONLY JSON."},
            {"role": "user", "content": prompt}
        ]

        try:
            import typing
            from app.services.ai.providers.router import ProviderRouter
            router_inst = typing.cast(ProviderRouter, self.provider)
            
            # fast validation using general intent
            eval_result = await router_inst.chat(messages, intent="structured")
            start = eval_result.find("{")
            end = eval_result.rfind("}") + 1
            if start != -1 and end != -1:
                eval_json = json.loads(eval_result[start:end])
                report = ValidationReport(
                    is_trustworthy=eval_json.get("is_trustworthy", False),
                    confidence_score=eval_json.get("confidence_score", 0.0),
                    reason=eval_json.get("reason", "Validation parsed"),
                    retry_suggested=eval_json.get("retry_suggested", False)
                )
                logger.info(f"[Validator] Tool {result.tool_name} trustworthy={report.is_trustworthy} ({report.confidence_score})")
                return report
        except Exception as e:
            logger.warning(f"[Validator] Failed to run LLM validation: {str(e)}")
            
        # Fallback if LLM validation fails, trust the native confidence but flag it
        return ValidationReport(
            is_trustworthy=result.confidence > 0.5,
            confidence_score=result.confidence,
            reason="Fallback validation due to LLM parsing failure."
        )
