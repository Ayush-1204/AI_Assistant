from pydantic import BaseModel

class ProviderMetadata(BaseModel):
    name: str
    supported_models: list[str]
    context_window: int
    supports_streaming: bool
    supports_vision: bool
    supports_function_calling: bool
    estimated_cost_tier: int
    is_local: bool
