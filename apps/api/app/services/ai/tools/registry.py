from app.services.ai.tools.base import BaseTool

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        
    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool
        
    def get_tool(self, name: str) -> BaseTool | None:
        return self._tools.get(name)
        
    def get_all_schemas(self) -> list[dict]:
        schemas = []
        for name, tool in self._tools.items():
            schemas.append({
                "name": name,
                "description": tool.description,
                "parameters": tool.parameters_schema
            })
        return schemas
