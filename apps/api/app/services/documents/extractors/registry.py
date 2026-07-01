from pathlib import Path

from .base import BaseExtractor
from .pdf_extractor import PDFExtractor


class ExtractorRegistry:

    def __init__(self):

        self.extractors: dict[str, BaseExtractor] = {

            ".pdf": PDFExtractor(),

        }

    def get(
        self,
        file_path: Path,
    ) -> BaseExtractor:

        extension = file_path.suffix.lower()

        extractor = self.extractors.get(
            extension,
        )

        if extractor is None:

            raise ValueError(
                f"No extractor for {extension}"
            )

        return extractor