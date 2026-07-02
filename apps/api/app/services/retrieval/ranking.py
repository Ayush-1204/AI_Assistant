from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RetrievedChunk:
    document_id: int
    document_title: str
    chunk_id: int
    chunk_index: int
    token_count: int
    distance: float
    content: str


def document_title(document) -> str:
    return (
        getattr(document, "title", None)
        or getattr(document, "original_filename", None)
        or getattr(document, "filename", None)
        or "Untitled Document"
    )


def is_expected_result(
    result: RetrievedChunk,
    expected_document: str,
    expected_chunk: int | None = None,
) -> bool:
    document_matches = (
        result.document_title.casefold()
        == expected_document.casefold()
    )

    if not document_matches:
        return False

    if expected_chunk is None:
        return True

    return result.chunk_index == expected_chunk


def find_expected_rank(
    results: list[RetrievedChunk],
    expected_document: str,
    expected_chunk: int | None = None,
) -> int | None:
    for index, result in enumerate(results, start=1):
        if is_expected_result(result, expected_document, expected_chunk):
            return index

    return None
