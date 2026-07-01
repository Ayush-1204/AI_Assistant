from __future__ import annotations

import tiktoken

from app.services.documents.models import (
    Chunk,
    ExtractedDocument,
)


class TextChunker:
    """
    Token-aware chunker.
    """

    def __init__(
        self,
        model: str = "cl100k_base",
        chunk_size: int = 800,
        overlap: int = 100,
    ):
        self.encoding = tiktoken.get_encoding(model)
        self.chunk_size = chunk_size
        self.overlap = overlap

    def token_count(
        self,
        text: str,
    ) -> int:
        return len(
            self.encoding.encode(text)
        )

    def chunk(
        self,
        document: ExtractedDocument,
    ) -> list[Chunk]:

        paragraphs = [
            p.strip()
            for p in document.text.split("\n\n")
            if p.strip()
        ]

        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:

            merged = (
                current + "\n\n" + paragraph
                if current
                else paragraph
            )

            if self.token_count(merged) <= self.chunk_size:
                current = merged
                continue

            if current:
                chunks.append(current)

            current = paragraph

        if current:
            chunks.append(current)

        return self._apply_overlap(
            chunks=chunks,
            document=document,
        )

    def _apply_overlap(
        self,
        *,
        chunks: list[str],
        document: ExtractedDocument,
    ) -> list[Chunk]:

        results: list[Chunk] = []

        previous = ""

        for index, chunk in enumerate(chunks):

            if previous:

                words = previous.split()

                overlap_text = " ".join(
                    words[-self.overlap:]
                )

                chunk = overlap_text + "\n\n" + chunk

            results.append(
                Chunk(
                    chunk_index=index,
                    content=chunk,
                    token_count=self.token_count(chunk),
                    source=document.title or "",
                    metadata=document.metadata,
                )
            )

            previous = chunk

        return results