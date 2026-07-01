from enum import Enum, auto

from app.services.ai.providers.base import BaseLLMProvider


class TaskType(Enum):

    CHAT = auto()

    MEMORY = auto()

    RAG = auto()

    EMBEDDING = auto()

    CODING = auto()

    OFFLINE = auto()


class ProviderRouter:

    def __init__(
        self,
        gemini: BaseLLMProvider,
        ollama: BaseLLMProvider,
    ):
        self.gemini = gemini
        self.ollama = ollama

    async def get_provider(
        self,
        task: TaskType,
    ) -> BaseLLMProvider:

        if task in (
            TaskType.OFFLINE,
            TaskType.CODING,
        ):
            return self.ollama

        return self.gemini