import asyncio

from app.dependencies import get_llm_provider
from app.services.ai.memory.memory_extractor import MemoryExtractor


async def main():

    provider = get_llm_provider()

    extractor = MemoryExtractor(provider)

    result = await extractor.extract(
        "My favorite editor is VS Code."
    )

    print(result)


asyncio.run(main())