from abc import ABC, abstractmethod

class RoutingStrategy(ABC):
    @abstractmethod
    def select_provider(self, available_providers: list[str]) -> str:
        """Select a provider from the list of healthy/available providers."""
        pass

class FixedProviderStrategy(RoutingStrategy):
    def __init__(self, default_provider: str):
        self.default_provider = default_provider
        
    def select_provider(self, available_providers: list[str]) -> str:
        if self.default_provider in available_providers:
            return self.default_provider
        if available_providers:
            return available_providers[0]
        return ""

class PriorityStrategy(RoutingStrategy):
    def __init__(self, fallback_chain: list[str]):
        self.fallback_chain = fallback_chain
        
    def select_provider(self, available_providers: list[str]) -> str:
        for provider in self.fallback_chain:
            if provider in available_providers:
                return provider
        if available_providers:
            return available_providers[0]
        return ""

class LoadBalancingStrategy(ABC):
    @abstractmethod
    def select_provider(self, available_providers: list[str]) -> str:
        pass

class RoundRobinStrategy(LoadBalancingStrategy):
    def __init__(self):
        self.index = 0
        
    def select_provider(self, available_providers: list[str]) -> str:
        if not available_providers: return ""
        selected = available_providers[self.index % len(available_providers)]
        self.index += 1
        return selected

class LeastRecentlyUsedStrategy(LoadBalancingStrategy):
    def __init__(self):
        self.last_used = {}
        
    def select_provider(self, available_providers: list[str]) -> str:
        if not available_providers: return ""
        import time
        best = available_providers[0]
        oldest = self.last_used.get(best, 0)
        for p in available_providers:
            ts = self.last_used.get(p, 0)
            if ts < oldest:
                oldest = ts
                best = p
        self.last_used[best] = time.time()
        return best

class IntentBasedRoutingStrategy(RoutingStrategy):
    def __init__(self, fallback_chains: dict[str, list[str]]):
        """
        fallback_chains = {
            "general": ["gemini-2.5-flash", "groq-llama", "gemini-2.5-flash-lite", "gemini-1.5-flash", "openrouter", "gemini-2.0-flash", "ollama-default"],
            "long_doc": ["gemini-2.5-pro", "gemini-1.5-pro", "gemini-2.5-flash", "openrouter"],
            "vision": ["gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-pro"],
            "coding": ["ollama-coder", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-pro"],
            "reasoning": ["ollama-reasoning", "gemini-2.5-pro", "gemini-1.5-pro"],
            "voice": ["groq-llama", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-1.5-flash", "ollama-default"]
        }
        """
        self.fallback_chains = fallback_chains
        
    def select_provider(self, available_providers: list[str], intent: str = "general") -> str:
        chain = self.fallback_chains.get(intent) or self.fallback_chains.get("general", [])
        for provider in chain:
            if provider in available_providers:
                return provider
        if available_providers:
            return available_providers[0]
        return ""
