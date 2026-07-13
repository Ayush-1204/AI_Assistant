from datetime import datetime

from app.services.ai.tools.base import BaseTool


class CurrentTimeTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_current_time"
        
    @property
    def description(self) -> str:
        return "Returns the current local date and time."
        
    @property
    def parameters_schema(self) -> dict:
        return {}
        
    async def execute(self, execution_context: dict, **kwargs) -> str:
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")
