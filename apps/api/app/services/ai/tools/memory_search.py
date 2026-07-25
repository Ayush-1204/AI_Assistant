from app.services.ai.memory.memory_service import MemoryService
from app.services.ai.tools.base import BaseTool


class MemorySearchTool(BaseTool):
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
        
    @property
    def name(self) -> str:
        return "search_memory"
        
    @property
    def description(self) -> str:
        return "Search the user's explicit facts/preferences memory."
        
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {}
        }
        
    async def execute(self, execution_context: dict, **kwargs) -> str:
        user_id = execution_context.get("user_id")
        if not user_id:
            return "Execution Error: Unknown user."
            
        memories = await self.memory_service.retrieve_memories(user_id=user_id)
        if not memories:
            return "No memories recorded or found natively."
            
        output = ""
        for m in memories:
            output += f"- {m.value}\n"
            
        return output
