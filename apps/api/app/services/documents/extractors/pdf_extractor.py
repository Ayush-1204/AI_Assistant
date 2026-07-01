from pathlib import Path

import pymupdf # pyright: ignore[reportMissingImports]

from app.services.documents.models import (
    ExtractedDocument,
)

from .base import BaseExtractor


class PDFExtractor(BaseExtractor):

    async def extract(
        self,
        file_path: Path,
    ) -> ExtractedDocument:

        document = pymupdf.open(file_path)

        pages = []

        try:

            for page in document:

                text = page.get_text()

                if text.strip():
                    pages.append(text)

            metadata = document.metadata or {}

            page_count = len(document)

        finally:
            document.close()

        return ExtractedDocument(
            text="\n\n".join(pages),
            page_count=page_count,
            metadata=metadata,
        )