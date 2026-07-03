from pydantic import BaseModel, Field
from typing import Any

class ToolRequest(BaseModel):
    id: str | None = None
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)

class ToolResponse(BaseModel):
    id: str | None = None
    name: str
    content: str
    is_error: bool = False
