import asyncio
import sys
import os

sys.path.append(os.path.dirname(__file__))

from app.services.ai.providers.gemini_provider import GeminiProvider

async def main():
    provider = GeminiProvider()
    prompt = """system: You are a backend daemon tracking autonomous execution for Ayush Verma. Task Directive: You need to tell the weather details of my location including the wind conditions, AQI, flow of weather, UV index etc. and recommend me.    
CRITICAL: Do NOT invent, hallucinate, or mock telemetry data! Use your tools (e.g. web search) to fetch real, live data to satisfy the directive.
user: Commence daemon routine."""

    messages = [{"role": "system", "content": prompt}]
    tools = [{
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}
        }
    }]
    print("Testing chat with tools...")
    res = await provider.chat(messages, tools=tools)
    try:
        print("Response text:", repr(res.text))
    except Exception as e:
        print("Exception:", str(e))
        
    print("Function calls:", res.function_calls)

if __name__ == "__main__":
    asyncio.run(main())
