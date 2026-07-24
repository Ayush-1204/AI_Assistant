import asyncio
import sys
import os
import json

sys.path.append(os.path.dirname(__file__))

from app.services.ai.providers.gemini_provider import GeminiProvider

async def main():
    provider = GeminiProvider()
    messages = [{"role": "user", "content": "Hello!"}]
    tools = [{
        "type": "function",
        "function": {
            "name": "test_tool",
            "description": "A test tool",
            "parameters": {"type": "object", "properties": {}}
        }
    }]
    print("Testing chat...")
    res = await provider.chat(messages, tools=tools)
    try:
        print("Response text:", res.text)
    except Exception as e:
        print("Exception accessing text:", type(e), str(e))
    print("Candidates:", res.candidates)

if __name__ == "__main__":
    asyncio.run(main())