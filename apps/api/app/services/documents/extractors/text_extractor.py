from pathlib import Path

from app.services.documents.models import ExtractedDocument
from .base import BaseExtractor


class TextExtractor(BaseExtractor):
    """
    Extracts text content natively from plaintext, markdown, and JSON files securely.
    """

    async def extract(
        self,
        file_path: Path,
    ) -> ExtractedDocument:
        
        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception as e:
            text = file_path.read_text(encoding="latin-1", errors="replace")

        return ExtractedDocument(
            text=text,
            page_count=1,
            metadata={
                "source_type": "text/plain",
                "filename": file_path.name,
                "file_size": file_path.stat().st_size if file_path.exists() else 0,
            },
            title=file_path.stem
        )
