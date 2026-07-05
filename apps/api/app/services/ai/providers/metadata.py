from pydantic import BaseModel

class ProviderMetadata(BaseModel):
    name: str
    supported_models: list[str]
    context_window: int
    supports_streaming: bool
    supports_vision: bool
    supports_native_tools: bool
    supports_parallel_tools: bool
    supports_tool_streaming: bool
    estimated_cost_tier: int
    is_local: bool
