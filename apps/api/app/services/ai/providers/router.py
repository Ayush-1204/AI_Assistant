import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any, Literal, TypedDict, overload

from app.config import get_settings
from app.services.ai.providers.base import BaseLLMProvider
from app.services.ai.providers.exceptions import (
    AllProvidersFailedError,
    ProviderError,
    ProviderTransientError,
)
from app.services.ai.providers.metadata import ProviderMetadata
from app.services.ai.providers.strategies import (
    FixedProviderStrategy,
    IntentBasedRoutingStrategy,
    LeastRecentlyUsedStrategy,
    LoadBalancingStrategy,
    PriorityStrategy,
    RoundRobinStrategy,
    RoutingStrategy,
)

logger = logging.getLogger(__name__)

class ProviderHealthCache(TypedDict):
    is_healthy: bool
    last_checked: float

class TokenBucket:
    def __init__(self, capacity: int, refill_period: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_period = refill_period
        self.last_refill = time.time()
        
    def check_capacity(self, amount: int) -> bool:
        now = time.time()
        time_passed = now - self.last_refill
        if time_passed >= self.refill_period:
            self.tokens = self.capacity
            self.last_refill = now
        else:
            refill_amount = int((time_passed / self.refill_period) * self.capacity)
            if refill_amount > 0:
                self.tokens = min(self.capacity, self.tokens + refill_amount)
                self.last_refill = now
        return self.tokens >= amount

    def consume(self, amount: int):
        self.tokens -= amount

class ProviderBudget:
    def __init__(self, rpm: int, tpm: int, cost_per_m_input: float = 0.0, cost_per_m_output: float = 0.0):
        self.rpm_bucket = TokenBucket(rpm, 60.0)
        self.tpm_bucket = TokenBucket(tpm, 60.0)
        self.cost_per_m_input = cost_per_m_input
        self.cost_per_m_output = cost_per_m_output
        self.total_cost = 0.0
        
    def can_call(self, estimated_tokens: int) -> bool:
        return self.rpm_bucket.check_capacity(1) and self.tpm_bucket.check_capacity(estimated_tokens)

    def consume(self, estimated_tokens: int):
        self.rpm_bucket.consume(1)
        self.tpm_bucket.consume(estimated_tokens)

    def track_usage(self, input_tokens: int, output_tokens: int):
        self.total_cost += (input_tokens / 1_000_000.0) * self.cost_per_m_input
        self.total_cost += (output_tokens / 1_000_000.0) * self.cost_per_m_output

class ProviderRouter(BaseLLMProvider):
    def __init__(self):
        self.providers: dict[str, BaseLLMProvider] = {}
        self.settings = get_settings()
        
        # Health cache tracking internal up-states independently scaling away from requests payloads
        self._health_cache: dict[str, ProviderHealthCache] = {}
        self.budgets: dict[str, ProviderBudget] = {}
        
        self.strategy_type = self.settings.routing_strategy
        self.strategy: RoutingStrategy
        if self.strategy_type == "priority":
            self.strategy = PriorityStrategy(self.settings.fallback_provider_chain)
        else:
            self.strategy = FixedProviderStrategy(self.settings.default_provider)
            
        self.intent_strategy = IntentBasedRoutingStrategy({
            "voice": ["groq-llama-3.1-8b-instant", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite", "ollama-default"],
            "dashboard": ["groq-llama-3.1-8b-instant", "groq-qwen3-32b", "gemini-3.1-flash-lite", "gemini-2.5-flash"],
            "long_doc": ["openrouter-gpt-oss-120b", "gemini-3.5-flash", "gemini-2.5-flash"],
            "coding": ["groq-qwen3.6-27b", "groq-qwen3-32b", "ollama-coder", "gemini-3.5-flash"],
            "reasoning": ["groq-compound", "groq-compound-mini", "openrouter-gpt-oss-safeguard-20b", "gemini-3.5-flash"],
            "vision": ["openrouter-orpheus-vl-english", "gemini-3.5-flash"],
            "structured": ["gemini-3.1-flash-lite", "gemini-2.5-flash", "groq-llama-3.3-70b-versatile"],
            "general": ["groq-llama-3.1-8b-instant", "groq-llama-3.3-70b-versatile", "gemini-flash", "groq-qwen3-32b", "ollama-default"]
        })
            
        self.lb_type = self.settings.load_balancing_strategy
        self.lb_strategy: LoadBalancingStrategy | None = None
        if self.lb_type == "round_robin":
            self.lb_strategy = RoundRobinStrategy()
        elif self.lb_type == "lru":
            self.lb_strategy = LeastRecentlyUsedStrategy()

    def register_provider(self, provider: BaseLLMProvider):
        name = provider.name
        self.providers[name] = provider
        self._health_cache[name] = {"is_healthy": True, "last_checked": 0.0}
        
        if "groq-llama" in name.lower():
            # Groq Llama 3.3 70B: $0.59 / $0.79 per 1M tokens
            self.budgets[name] = ProviderBudget(rpm=30, tpm=6000, cost_per_m_input=0.59, cost_per_m_output=0.79)
        elif "gemini-3.1-flash-lite" in name.lower():
            self.budgets[name] = ProviderBudget(rpm=500, tpm=250000, cost_per_m_input=0.075, cost_per_m_output=0.3)
        elif "gemini-3.5-flash" in name.lower():
            self.budgets[name] = ProviderBudget(rpm=20, tpm=250000, cost_per_m_input=0.1, cost_per_m_output=0.4)
        elif "gemini" in name.lower():
            self.budgets[name] = ProviderBudget(rpm=20, tpm=250000, cost_per_m_input=0.075, cost_per_m_output=0.3)
        else:
            self.budgets[name] = ProviderBudget(rpm=1000, tpm=10000000, cost_per_m_input=0.0, cost_per_m_output=0.0)

    @property
    def name(self) -> str:
        return "provider_router"

    async def get_metadata(self) -> ProviderMetadata:
        # Dummy structural schema since router itself technically supports anything mapped downwards
        return ProviderMetadata(
            name="router", supported_models=[], context_window=0, supports_streaming=True,
            supports_vision=False, supports_native_tools=True, supports_parallel_tools=False,
            supports_tool_streaming=False, estimated_cost_tier=0, is_local=False
        )

    async def check_health(self) -> bool:
        for p_name in list(self.providers):
            if await self._is_provider_healthy(p_name):
                return True
        return False

    async def _is_provider_healthy(self, name: str) -> bool:
        cache = self._health_cache.get(name)
        if not cache: return False
        
        now = time.time()
        if now - cache["last_checked"] > self.settings.health_check_interval:
            provider = self.providers[name]
            was_healthy = cache["is_healthy"]
            cache["is_healthy"] = await provider.check_health()
            cache["last_checked"] = now
            
            if was_healthy != cache["is_healthy"]:
                logger.info("Provider health transition mapped", extra={"provider": name, "healthy": cache["is_healthy"]})
                
        return cache["is_healthy"]

    async def _get_available_providers(self, requires_vision: bool = False) -> list[str]:
        local_override = getattr(self.settings, "LOCAL_ONLY_MODE", False)
        
        provider_names = [
            name for name in self.providers 
            if not (local_override and "ollama" not in name.lower())
        ]
        
        # Concurrently check health to avoid sequential 5s blocking timeouts
        health_results = await asyncio.gather(
            *[self._is_provider_healthy(name) for name in provider_names],
            return_exceptions=True
        )
        
        available = []
        vision_available = []
        
        for name, is_healthy in zip(provider_names, health_results):
            if isinstance(is_healthy, bool) and is_healthy:
                available.append(name)
                try:
                    meta = await self.providers[name].get_metadata()
                    if getattr(meta, "supports_vision", False):
                        vision_available.append(name)
                except Exception:
                    pass
                    
        # Give preference to vision models if requested. Fallback linearly if all vision orchestrators are down.
        if requires_vision and vision_available:
            return vision_available
            
        return available

    def _select_provider(self, available: list[str], intent: str = "general") -> BaseLLMProvider:
        if not available:
            raise AllProvidersFailedError("No healthy providers available mapping limits.")
            
        if self.intent_strategy:
            selected_name = self.intent_strategy.select_provider(available, intent=intent)
        elif self.lb_strategy:
            selected_name = self.lb_strategy.select_provider(available)
        else:
            selected_name = self.strategy.select_provider(available)
            
        if intent not in ("dashboard", "dashboard_auto_refresh"):
            logger.info(f"[ProviderRouter] Routed '{intent}' intent successfully to physical model '{selected_name}'")
            
        return self.providers[selected_name]

    def _estimate_tokens(self, operation: str, args: tuple) -> int:
        tokens = 100
        if operation == "chat" or operation == "stream_chat":
            if args and isinstance(args[0], list):
                for msg in args[0]:
                    if isinstance(msg, dict) and "content" in msg and isinstance(msg["content"], str):
                        tokens += len(msg["content"]) // 4
        elif operation == "generate_title":
            if args and isinstance(args[0], str):
                tokens += len(args[0]) // 4
        return tokens

    @overload
    async def _execute_with_router(self, operation: Literal["chat"], *args, intent: str = "general", **kwargs) -> str: ...
    @overload
    async def _execute_with_router(self, operation: Literal["generate_title"], *args, intent: str = "general", **kwargs) -> str: ...

    async def _execute_with_router(self, operation: str, *args, intent: str = "general", **kwargs) -> Any:
        # Determine if payload requires vision capability natively
        requires_vision = False
        if operation in ("chat", "stream_chat") and len(args) > 0 and isinstance(args[0], list):
            for msg in args[0]:
                if isinstance(msg, dict) and "content" in msg and isinstance(msg["content"], str):
                    if len(msg["content"]) > 50000:
                        logger.warning(f"[Router] CRITICAL: Message payload extremely large ({len(msg['content'])} chars). Truncating to prevent provider crash.")
                        msg["content"] = msg["content"][:50000] + "... [TRUNCATED DUE TO SIZE]"
                        
            requires_vision = any("images" in m and bool(m.get("images")) for m in args[0])
            
        available_at_start = await self._get_available_providers(requires_vision)
        tried_providers = set()
        estimated_tokens = self._estimate_tokens(operation, args)
        
        for _ in range(len(self.providers)):
            current_available = [
                p for p in available_at_start 
                if p not in tried_providers and self.budgets[p].can_call(estimated_tokens)
            ]
            if not current_available:
                break
                
            provider = self._select_provider(current_available, intent=intent)
            tried_providers.add(provider.name)
            self.budgets[provider.name].consume(estimated_tokens)
            
            for attempt in range(self.settings.retry_count):
                try:
                    start_time = time.perf_counter()
                    
                    if operation == "chat":
                        result = await provider.chat(*args, intent=intent, **kwargs)
                    elif operation == "generate_title":
                        result = await provider.generate_title(*args, **kwargs)
                        
                    # Calculate live proxy token usage
                    if isinstance(result, str):
                        output_tokens = len(result) // 4
                    elif isinstance(result, dict) and "text" in result:
                        output_tokens = len(result["text"]) // 4
                    else:
                        output_tokens = 50
                        
                    self.budgets[provider.name].track_usage(estimated_tokens, output_tokens)
                        
                    latency = (time.perf_counter() - start_time) * 1000.0
                    
                    if intent not in ("dashboard", "dashboard_auto_refresh"):
                        logger.info(f"Provider {operation} successful", extra={"provider": provider.name, "latency_ms": latency})
                        
                    return result
                    
                except ProviderTransientError as e:
                    logger.warning(f"Transient error spanning {provider.name}", extra={"attempt": attempt + 1, "error": str(e)})
                    if attempt < self.settings.retry_count - 1:
                        await asyncio.sleep(self.settings.retry_backoff * (2 ** attempt))
                    else:
                        logger.warning(f"Provider {provider.name} exhausted retries falling over safely.")
                        if provider.name in self._health_cache:
                            self._health_cache[provider.name]["is_healthy"] = False
                            self._health_cache[provider.name]["last_checked"] = time.time()
                except ProviderError as e:
                    logger.error(f"Non-transient rejection spanning {provider.name}. Dropping.", extra={"error": str(e)})
                    if provider.name in self._health_cache:
                        self._health_cache[provider.name]["is_healthy"] = False
                        self._health_cache[provider.name]["last_checked"] = time.time()
                    break
                    
        raise AllProvidersFailedError("All providers fallback chain entirely failed.")

    async def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, intent: str = "general") -> str:
        return await self._execute_with_router("chat", messages, tools=tools, intent=intent)

    async def generate_title(self, ai_response: str) -> str:
        return await self._execute_with_router("generate_title", ai_response)



    async def stream_chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, intent: str = "general") -> AsyncGenerator[Any, None]:
        requires_vision = any("images" in m and bool(m.get("images", False)) for m in messages)
        available_at_start = await self._get_available_providers(requires_vision)
        tried_providers = set()
        estimated_tokens = self._estimate_tokens("stream_chat", (messages,))
        
        for _ in range(len(self.providers)):
            current_available = [
                p for p in available_at_start 
                if p not in tried_providers and self.budgets[p].can_call(estimated_tokens)
            ]
            if not current_available:
                break
                
            provider = self._select_provider(current_available, intent=intent)
            tried_providers.add(provider.name)
            self.budgets[provider.name].consume(estimated_tokens)
            
            for attempt in range(self.settings.retry_count):
                try:
                    start_time = time.perf_counter()
                    stream = provider.stream_chat(messages, tools=tools, intent=intent)
                    
                    found_first_chunk = False
                    output_tokens = 0
                    async for chunk in stream:
                        found_first_chunk = True
                        if isinstance(chunk, str):
                            output_tokens += len(chunk) // 4
                        yield chunk
                    
                    if found_first_chunk:
                        self.budgets[provider.name].track_usage(estimated_tokens, output_tokens)
                        latency = (time.perf_counter() - start_time) * 1000.0
                        logger.info("Provider stream_chat successfully completed generation", extra={"provider": provider.name, "latency_ms": latency})
                        return
                    else:
                        break
                        
                except ProviderTransientError as e:
                    logger.warning(f"Transient streaming error overriding {provider.name}", extra={"attempt": attempt + 1, "error": str(e)})
                    if attempt < self.settings.retry_count - 1:
                        await asyncio.sleep(self.settings.retry_backoff * (2 ** attempt))
                    else:
                        logger.warning(f"Provider {provider.name} exhausted streaming retries falling over.")
                        if provider.name in self._health_cache:
                            self._health_cache[provider.name]["is_healthy"] = False
                            self._health_cache[provider.name]["last_checked"] = time.time()
                except ProviderError as e:
                    logger.error(f"Non-transient streaming rejection skipping {provider.name}.", extra={"error": str(e)})
                    if provider.name in self._health_cache:
                        self._health_cache[provider.name]["is_healthy"] = False
                        self._health_cache[provider.name]["last_checked"] = time.time()
                    break

        raise AllProvidersFailedError("All providers failed establishing stream pipelines.")