import math

from app.services.ai.tools.base import BaseTool


class CalculatorTool(BaseTool):
    @property
    def name(self) -> str:
        return "calculator"
        
    @property
    def description(self) -> str:
        return "Evaluates a mathematical expression accurately."
        
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression, e.g. '2 + 2'"
                }
            },
            "required": ["expression"]
        }
        
    async def execute(self, execution_context: dict, expression: str = "", **kwargs) -> str:
        try:
            allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
            allowed_names["abs"] = abs
            allowed_names["round"] = round
            allowed_names["pow"] = pow
            
            res = eval(expression, {"__builtins__": {}}, allowed_names)
            return str(res)
        except Exception as e:
            return f"Math error: {str(e)}"
