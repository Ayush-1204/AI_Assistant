import time
import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Any

from app.config import get_settings
from app.services.ai.providers.base import BaseLLMProvider
from app.services.ai.providers.exceptions import (
    ProviderTransientError, AllProvidersFailedError, ProviderError
)
from app.services.ai.providers.strategies import (
    FixedProviderStrategy, PriorityStrategy, RoundRobinStrategy, LeastRecentlyUsedStrategy,
    RoutingStrategy, LoadBalancingStrategy
)
from app.services.ai.providers.metadata import ProviderMetadata

logger = logging.getLogger(__name__)

class ProviderRouter(BaseLLMProvider):
    def __init__(self):
        self.providers: dict[str, BaseLLMProvider] = {}
        self.settings = get_settings()
        
        # Health cache tracking internal up-states independently scaling away from requests payloads
        self._health_cache: dict[str, dict] = {}
        
        self.strategy_type = self.settings.routing_strategy
        self.strategy: RoutingStrategy
        if self.strategy_type == "priority":
            self.strategy = PriorityStrategy(self.settings.fallback_provider_chain)
        else:
            self.strategy = FixedProviderStrategy(self.settings.default_provider)
            
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

    @property
    def name(self) -> str:
        return "provider_router"

    async def get_metadata(self) -> ProviderMetadata:
        # Dummy structural schema since router itself technically supports anything mapped downwards
        return ProviderMetadata(
            name="router", supported_models=[], context_window=0, supports_streaming=True,
            supports_vision=False, supports_native_tools=False, supports_parallel_tools=False,
            supports_tool_streaming=False, estimated_cost_tier=0, is_local=False
        )

    async def check_health(self) -> bool:
        for p_name in self.providers:
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

    async def _get_available_providers(self) -> list[str]:
        available = []
        for name in self.providers:
            if await self._is_provider_healthy(name):
                available.append(name)
        return available

    def _select_provider(self, available: list[str]) -> BaseLLMProvider:
        if not available:
            raise AllProvidersFailedError("No healthy providers available mapping limits.")
            
        if self.lb_strategy:
            selected_name = self.lb_strategy.select_provider(available)
        else:
            selected_name = self.strategy.select_provider(available)
            
        logger.info("Provider selected successfully", extra={"provider": selected_name, "strategy": self.strategy_type})
        return self.providers[selected_name]

    async def _execute_with_router(self, operation: str, *args, **kwargs):
        available_at_start = await self._get_available_providers()
        tried_providers = set()
        
        for _ in range(len(self.providers)):
            current_available = [p for p in available_at_start if p not in tried_providers]
            if not current_available:
                break
                
            provider = self._select_provider(current_available)
            tried_providers.add(provider.name)
            
            for attempt in range(self.settings.retry_count):
                try:
                    start_time = time.perf_counter()
                    
                    if operation == "chat":
                        result = await provider.chat(*args, **kwargs)
                    elif operation == "generate_title":
                        result = await provider.generate_title(*args, **kwargs)
                    elif operation == "extract_memory":
                        result = await provider.extract_memory(*args, **kwargs)
                        
                    latency = (time.perf_counter() - start_time) * 1000.0
                    logger.info(f"Provider {operation} successful", extra={"provider": provider.name, "latency_ms": latency})
                    return result
                    
                except ProviderTransientError as e:
                    logger.warning(f"Transient error spanning {provider.name}", extra={"attempt": attempt + 1, "error": str(e)})
                    if attempt < self.settings.retry_count - 1:
                        await asyncio.sleep(self.settings.retry_backoff * (2 ** attempt))
                    else:
                        logger.warning(f"Provider {provider.name} exhausted retries falling over safely.")
                except ProviderError as e:
                    logger.error(f"Non-transient rejection spanning {provider.name}. Dropping.", extra={"error": str(e)})
                    break
                    
        raise AllProvidersFailedError("All providers fallback chain entirely failed.")

    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> str:
        return await self._execute_with_router("chat", messages, tools=tools)

    async def generate_title(self, first_message: str) -> str:
        return await self._execute_with_router("generate_title", first_message)

    async def extract_memory(self, message: str) -> dict | None:
        return await self._execute_with_router("extract_memory", message)

    async def stream_chat(self, messages: list[dict], tools: list[dict] | None = None) -> AsyncGenerator[Any, None]:
        available_at_start = await self._get_available_providers()
        tried_providers = set()
        
        for _ in range(len(self.providers)):
            current_available = [p for p in available_at_start if p not in tried_providers]
            if not current_available:
                break
                
            provider = self._select_provider(current_available)
            tried_providers.add(provider.name)
            
            for attempt in range(self.settings.retry_count):
                try:
                    start_time = time.perf_counter()
                    stream = provider.stream_chat(messages, tools=tools)
                    
                    found_first_chunk = False
                    async for chunk in stream:
                        found_first_chunk = True
                        yield chunk
                    
                    if found_first_chunk:
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
                except ProviderError as e:
                    logger.error(f"Non-transient streaming rejection skipping {provider.name}.", extra={"error": str(e)})
                    break

        raise AllProvidersFailedError("All providers failed establishing stream pipelines.")