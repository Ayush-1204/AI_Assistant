from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Citation(BaseModel):
    url: str
    title: str
    snippet: str

class ImageReference(BaseModel):
    url: str
    alt_text: str
    relevance_score: float = 1.0

class NormalizedToolResult(BaseModel):
    tool_name: str
    source: str
    timestamp: datetime = Field(default_factory=datetime.now)
    confidence: float = 1.0
    rawData: Any | None = None
    normalizedData: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    images: list[ImageReference] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)

class ExecutionTask(BaseModel):
    id: str
    name: str
    capability: str
    tool_arguments: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    canRunInParallel: bool = True
    expectedOutput: str = ""
    timeout: int = 30
    retryPolicy: int = 2
    
class ExecutionTrace(BaseModel):
    id: str
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: datetime | None = None
    tasks_executed: int = 0
    tasks_failed: int = 0
    replans_triggered: int = 0
    final_quality_score: float = 0.0

class ResponsePlan(BaseModel):
    tools_needed: bool = False
    output_structure: str = "direct_answer"
    is_parallelizable: bool = True
    tasks: list[ExecutionTask] = Field(default_factory=list)
    reasoning: str = ""

class ValidationReport(BaseModel):
    is_trustworthy: bool
    confidence_score: float
    reason: str = ""
    retry_suggested: bool = False

class CuratedContext(BaseModel):
    summary: str
    merged_facts: list[str] = Field(default_factory=list)
    curated_images: list[ImageReference] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    raw_data: Any | None = None
