import asyncio
from pathlib import Path

from app.services.documents.extractors.registry import (
    ExtractorRegistry,
)


async def main():

    pdf = Path(
        r"C:\Users\AYUSH VERMA\Documents\AI_Assistant\apps\api\sample.pdf"
    )

    extractor = ExtractorRegistry().get(pdf)

    doc = await extractor.extract(pdf)

    print("=" * 80)

    print(doc.page_count)

    print(doc.metadata)

    print(doc.text[:1000])


asyncio.run(main())