from abc import ABC, abstractmethod
from typing import Any

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier representing this tool."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Natural description for the LLM context."""
        pass
        
    @property
    @abstractmethod
    def parameters_schema(self) -> dict:
        """JSON mapping dictating execution properties correctly."""
        pass
        
    @abstractmethod
    async def execute(self, execution_context: dict, **kwargs) -> Any:
        """Primary handler evaluating payloads properly over mapped bounds."""
        pass
