from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class AgentExecutionState(BaseModel):
    execution_id: str
    original_user_query: str
    current_step: int = 0
    completed_steps: int = 0
    pending_steps: int = 0
    executed_tools: list[str] = Field(default_factory=list)
    intermediate_results: dict[str, Any] = Field(default_factory=dict)
    tool_errors: list[str] = Field(default_factory=list)
    total_tool_calls: int = 0
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime | None = None
    final_answer: str | None = None
