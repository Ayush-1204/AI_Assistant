from abc import ABC, abstractmethod
from pathlib import Path

from app.services.documents.models import (
    ExtractedDocument,
)


class BaseExtractor(ABC):

    @abstractmethod
    async def extract(
        self,
        file_path: Path,
    ) -> ExtractedDocument:
        pass