import importlib.util
import inspect
import logging
import os

from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

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

    def scan_and_register_directory(self, target_directory: str):
        """Dynamically scans a directory for external Python skills and registers them."""
        if not os.path.exists(target_directory):
            logger.warning(f"[Registry] Skipped dynamic scan: {target_directory} does not exist.")
            return

        for filename in os.listdir(target_directory):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                file_path = os.path.join(target_directory, filename)
                
                try:
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if issubclass(obj, BaseTool) and obj is not BaseTool:
                                instance = obj()
                                self.register(instance)
                                logger.info(f"[Registry] Dynamically registered skill: {instance.name}")
                except Exception as e:
                    logger.error(f"[Registry] Failed to load skill from {filename}: {str(e)}")
