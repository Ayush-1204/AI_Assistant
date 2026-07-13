from dataclasses import dataclass, field
from typing import Callable, Any

@dataclass
class SwarmAgent:
    """
    Core logical representation of a specialized sub-agent within the Swarm loop.
    Contains instructions, tools, and logical capabilities.
    """
    name: str = "Agent"
    instructions: str | Callable[[], str] = "You are a helpful autonomous agent."
    tools: list[Any] = field(default_factory=list)
    model: str | None = None
