import hashlib
import json
import uuid
from datetime import datetime, timezone

from app.schemas.tool import ToolRequest, ToolResponse

from .models import AgentExecutionState


class ExecutionStateManager:
    def __init__(self, query: str):
        self.execution_id = str(uuid.uuid4())
        self.state = AgentExecutionState(
            execution_id=self.execution_id,
            original_user_query=query
        )
        self.tool_cache: dict[str, ToolResponse] = {}

    def _hash_tool_call(self, request: ToolRequest) -> str:
        payload = {"name": request.name, "args": request.arguments}
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    def check_duplicate(self, request: ToolRequest) -> ToolResponse | None:
        call_hash = self._hash_tool_call(request)
        return self.tool_cache.get(call_hash)

    def record_tool_result(self, request: ToolRequest, response: ToolResponse):
        self.state.total_tool_calls += 1
        self.state.executed_tools.append(request.name)
        
        if response.is_error:
            self.state.tool_errors.append(f"{request.name} failed: {response.content}")
        else:
            self.state.intermediate_results[request.name] = response.content
            call_hash = self._hash_tool_call(request)
            self.tool_cache[call_hash] = response

    def record_skip(self, request: ToolRequest):
        self.state.total_tool_calls += 1
        self.state.executed_tools.append(request.name)

    def increment_step(self):
        self.state.current_step += 1
        self.state.completed_steps += 1

    def terminate(self, answer: str):
        self.state.end_time = datetime.now(timezone.utc)
        self.state.final_answer = answer
