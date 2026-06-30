from app.services.llm.gemini_provider import GeminiProvider

import asyncio


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