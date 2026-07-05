import sys
import os
import asyncio
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Documents", "AI_Assistant", "apps", "api")))

from app.db.session import AsyncSessionLocal
from app.config import settings
from app.dependencies import get_provider_router

logging.basicConfig(level=logging.INFO)

async def main():
    router = get_provider_router()
    
    print("Available providers:", list(router.providers.keys()))
    print("Health check...", await router.check_health())
    
    print("\n--- Test Chat ---")
    res = await router.chat([{"role": "user", "content": "Reply with precisely 'ping'."}])
    print("Chat Response:", res)
    
    print("\n--- Test Stream Chat ---")
    st = router.stream_chat([{"role": "user", "content": "Reply with precisely 'stream'."}])
    async for chunk in st:
        print(chunk, end="", flush=True)
    print("\n--- DONE ---")

if __name__ == "__main__":
    asyncio.run(main())
