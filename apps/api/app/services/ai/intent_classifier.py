import json

from app.dependencies import _router_instance


class IntentClassifier:
    """
    Acts as the Fast Brain. Resolves user intents immediately before the slow context-assembly pipeline.
    Bypassing Vector DBs and extensive prompt generation for simple atomic tasks saves tokens, compute, and latency.
    """
    def __init__(self):
        self.router = _router_instance

    async def classify(self, prompt: str, images: list[str] | None = None) -> str:
        if images and len(images) > 0:
            return "VISION"
            
        system_prompt = """You are a sub-100ms intent classifier. 
Categorize the user's input into EXACTLY ONE of the following tags:
- [TASK] (e.g. reminders, todo list, setting alarm)
- [MEMORY] (e.g. what is my wife's name, do I like bread, who is my brother)
- [CALENDAR] (e.g. schedule a meeting, what is my next event)
- [SEARCH] (e.g. who won the game, what is the weather, recent news)
- [GENERAL] (e.g. what is the meaning of life, hello)
- [IMAGE_GENERATION] (e.g. generate a picture of a cat, draw a landscape, edit the attached image)
- [ANTIGRAVITY] (e.g. clone this repo and run tests, read hacker news, write python in sandbox)
- [SWARM] (e.g. spawn multi-agent loop, let agents debug this, code and review this)

Return ONLY a valid JSON object in this format, and absolutely nothing else:
{"intent": "TASK"}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # We explicitly route this to the cheapest, fastest model possible
        try:
            import typing

            from app.services.ai.providers.router import ProviderRouter
            router_inst = typing.cast(ProviderRouter, self.router)
            # We enforce `intent="general"` which the ProviderRouter maps to Llama-3/Gemini Flash
            result = await router_inst.chat(messages, intent="general")
            start = result.find("{")
            end = result.rfind("}") + 1
            if start != -1 and end != -1:
                parsed = json.loads(result[start:end])
                intent = parsed.get("intent", "GENERAL").strip().upper()
                if intent in ["TASK", "MEMORY", "CALENDAR", "SEARCH", "GENERAL", "ANTIGRAVITY", "SWARM", "IMAGE_GENERATION"]:
                    return intent
        except Exception:
            pass
            
        # Fallback to regex if LLM route fails/rejects, or deterministic shortcuts
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ["generate an image", "create a picture", "draw", "draw me a", "picture of", "edit the attached image", "edit this image"]): return "IMAGE_GENERATION"
        if any(w in prompt_lower for w in ["swarm", "multi-agent", "agents debug"]): return "SWARM"
        if any(w in prompt_lower for w in ["sandbox", "clone repo", "execute python", "hacker news", "linux command"]): return "ANTIGRAVITY"
        if any(w in prompt_lower for w in ["remind", "todo", "alarm", "add to list"]): return "TASK"
        if any(w in prompt_lower for w in ["schedule", "meeting", "event", "calendar"]): return "CALENDAR"
        if any(w in prompt_lower for w in ["search", "google", "weather", "news", "who won"]): return "SEARCH"
        if "my" in prompt_lower or "remember" in prompt_lower: return "MEMORY"
        
        return "GENERAL"
