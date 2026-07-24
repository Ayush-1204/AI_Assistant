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
        
    @property
    def requires_confirmation(self) -> bool:
        """Indicates whether this tool requires explicit user permission to execute."""
        return False
        
    def dynamic_requires_confirmation(self, kwargs: dict) -> bool:
        """Override to dynamically determine confirmation based on arguments."""
        return self.requires_confirmation
        
    @property
    def risk_level(self) -> str:
        """Risk level categorization: 'safe', 'moderate', 'destructive'."""
        return "safe"

    @abstractmethod
    async def execute(self, execution_context: dict, **kwargs) -> Any:
        """Primary handler evaluating payloads properly over mapped bounds."""
        pass
