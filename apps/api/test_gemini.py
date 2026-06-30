import asyncio

from app.services.ai.providers.gemini_provider import GeminiProvider


async def main():
    provider = GeminiProvider()

    response = await provider.generate(
        [
            {
                "role": "user",
                "content": "Say hello in one sentence.",
            }
        ]
    )

    print(response)


asyncio.run(main())