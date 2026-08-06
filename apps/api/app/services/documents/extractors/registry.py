from pathlib import Path

from .base import BaseExtractor
from .pdf_extractor import PDFExtractor
from .text_extractor import TextExtractor
from .docx_extractor import DocxExtractor


class ExtractorRegistry:

    def __init__(self):

        self.extractors: dict[str, BaseExtractor] = {

            ".pdf": PDFExtractor(),
            ".txt": TextExtractor(),
            ".md": TextExtractor(),
            ".json": TextExtractor(),
            ".docx": DocxExtractor(),

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