import asyncio
import time

from app.services.ai.providers import OllamaProvider


async def main():

    provider = OllamaProvider()

    start = time.perf_counter()

    response = await provider.chat([
        {
            "role": "user",
            "content": "Hello"
        }
    ])

    end = time.perf_counter()

    print(response)
    print(f"Time: {end-start:.2f}s")


asyncio.run(main())