import asyncio

from app.services.ai.providers import OllamaProvider


async def main():

    provider = OllamaProvider()

    response = await provider.chat(
        [
            {
                "role": "user",
                "content": "Say hello in one sentence.",
            }
        ]
    )

    print(response)


asyncio.run(main())