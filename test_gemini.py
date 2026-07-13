import asyncio
from app.services.ai.providers.gemini_provider import GeminiProvider
import google.genai.types as gt

async def test():
    tools = []
    print("Initial tools:", tools)

    try:
        tools.append({"google_search": {}})
        config = gt.GenerateContentConfig(tools=tools)
        print("Config created successfully with dict representation.")
    except Exception as e:
        print("Error creating config with dict:", e)

    try:
        # What is the correct way?
        tools2 = [{'google_search': {}}]
        config2 = gt.GenerateContentConfig(tools=tools2)
        print("Config2 created successfully.")
    except Exception as e:
        print("Error creating config2:", e)

    try:
        # Proper class instantiation
        tools3 = [{"google_search": {}}]
        # But wait, search grounding usually is: gt.Tool(google_search=gt.GoogleSearchTool()) 
        tool_obj = gt.Tool(google_search=gt.GoogleSearch())
        config3 = gt.GenerateContentConfig(tools=[tool_obj])
        print("Config3 valid tool object:", config3)
    except Exception as e:
        print("Error creating config3:", e)

if __name__ == "__main__":
    asyncio.run(test())
