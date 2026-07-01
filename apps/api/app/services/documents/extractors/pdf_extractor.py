from pathlib import Path

import fitz

from .base import BaseExtractor


class PDFExtractor(BaseExtractor):

    async def extract(
        self,
        file_path: Path,
    ) -> str:

        document = fitz.open(file_path)

        pages: list[str] = []

        try:

            for page in document:

                text = page.get_text(
                    "text",
                )

                if text.strip():
                    pages.append(text)

        finally:
            document.close()

        return "\n\n".join(pages)