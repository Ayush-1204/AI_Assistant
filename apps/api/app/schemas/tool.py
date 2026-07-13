from typing import Any

from pydantic import BaseModel, Field


class ToolRequest(BaseModel):
    id: str | None = None
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)

class ToolResponse(BaseModel):
    id: str | None = None
    name: str
    content: str
    is_error: bool = False
    requires_confirmation: bool = False
