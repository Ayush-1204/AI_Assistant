from dataclasses import dataclass


@dataclass(slots=True)
class ExtractedDocument:
    """
    Output of any document extractor.
    """

    text: str

    page_count: int

    metadata: dict