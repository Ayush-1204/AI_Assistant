from abc import ABC, abstractmethod
from pathlib import Path


class BaseExtractor(ABC):
    """
    Base class for all document extractors.
    """

    @abstractmethod
    async def extract(
        self,
        file_path: Path,
    ) -> str:
        """
        Extract plain text from a document.
        """
        raise NotImplementedError