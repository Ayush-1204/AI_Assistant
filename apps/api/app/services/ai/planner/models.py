from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class AgentExecutionState(BaseModel):
    execution_id: str
    original_user_query: str
    current_step: int = 0
    completed_steps: int = 0
    pending_steps: int = 0
    executed_tools: List[str] = Field(default_factory=list)
    intermediate_results: Dict[str, Any] = Field(default_factory=dict)
    tool_errors: List[str] = Field(default_factory=list)
    total_tool_calls: int = 0
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    final_answer: Optional[str] = None
