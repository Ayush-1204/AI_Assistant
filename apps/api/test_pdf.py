import asyncio
from pathlib import Path

from app.services.documents.extractors.registry import (
    ExtractorRegistry,
)


async def main():

    registry = ExtractorRegistry()

    extractor = registry.get(
        Path("sample.pdf"),
    )

    text = await extractor.extract(
        Path("sample.pdf"),
    )

    print(text[:1000])


asyncio.run(main())