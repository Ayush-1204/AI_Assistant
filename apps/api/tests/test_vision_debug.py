import asyncio
import os
import sys

# Add the app dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.ai.ai_service import AIService
from app.services.ai.providers.router import ProviderRouter
from app.services.ai.context.context_builder import ContextBuilder
from app.services.message_service import MessageService
from app.services.conversation_service import ConversationService
from app.services.ai.memory.memory_service import MemoryService
from app.services.ai.tools.orchestrator import ToolOrchestrator

from unittest.mock import AsyncMock, MagicMock

async def main():
    provider = ProviderRouter()
    provider.stream_chat = AsyncMock()
    
    msg_svc = AsyncMock()
    msg_svc.list_by_conversation.return_value = [
        MagicMock(role="user", content="Here is an image [Attached Image]", images=None)
    ]
    
    ctx_builder = ContextBuilder(msg_svc, AsyncMock(), AsyncMock())
    
    ai = AIService(
        provider=provider,
        message_service=msg_svc,
        conversation_service=AsyncMock(),
        context_builder=ctx_builder,
        memory_service=AsyncMock(),
        tool_orchestrator=AsyncMock()
    )
    
    # Test stream_chat
    gen = ai.stream_chat(
        user_id=1,
        conversation_id=1,
        prompt="what's in this image",
        images=["base64string1", "base64string2"],
        intent="VISION"
    )
    
    async for chunk in gen:
        pass
        
    print("Messages passed to provider.stream_chat:")
    messages = provider.stream_chat.call_args[0][0]
    last_msg = messages[-1]
    print(f"Role: {last_msg.get('role')}")
    print(f"Images present: {'images' in last_msg}")
    print(f"Images content: {last_msg.get('images')}")

if __name__ == "__main__":
    asyncio.run(main())
