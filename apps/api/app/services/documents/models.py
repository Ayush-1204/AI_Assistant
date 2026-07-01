from dataclasses import dataclass, field


@dataclass(slots=True)
class Chunk:
    """
    Internal representation of a document chunk.
    """

    chunk_index: int

    content: str

    token_count: int

    source: str

    page: int | None = None

    title: str | None = None

    metadata: dict = field(
        default_factory=dict,
    )

@dataclass(slots=True)
class ExtractedDocument:

    text: str

    page_count: int

    metadata: dict

    title: str | None = None