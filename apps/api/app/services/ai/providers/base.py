from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
    ) -> str:
        """
        Generate a response from the language model.

        Parameters
        ----------
        messages:
            Conversation history in chat format.

        Returns
        -------
        str
            Assistant response.
        """
        raise NotImplementedError