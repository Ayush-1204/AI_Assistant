import json
import logging
from typing import Any

from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

class CodeInterpreterTool(BaseTool):
    """
    A tool that executes untrusted Python code in a secure E2B cloud sandbox.
    Useful for data analysis, chart generation, or verifying complex mathematics natively.
    """

    def __init__(self, api_key: str | None = None):
        super().__init__()
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "execute_python_code"

    @property
    def description(self) -> str:
        return (
            "Executes python code in a secure sandboxed cloud environment. "
            "Use this tool for data analysis, parsing CSVs/JSONs, generating charts (matplotlib/seaborn), "
            "or running ANY mathematical computation to avoid hallucination. "
            "You can import standard data science libraries like pandas, numpy, and matplotlib. "
            "IMPORTANT: If you generate charts or files, read them and return their base64 or text contents, or print them. "
            "The standard output (stdout/stderr) of your script is returned."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The raw Python code string to execute in the sandbox."
                }
            },
            "required": ["code"]
        }

    async def execute(self, execution_context: dict, **kwargs) -> Any:
        code = kwargs.get("code")
        if not code:
            return "Error: 'code' parameter is required."

        if not self.api_key:
            return "Error: E2B_API_KEY is not configured in the environment. Ask the user to add it."

        try:
            # We must import inside the function to avoid breaking the app if e2b is not installed
            from e2b_code_interpreter import Sandbox
        except ImportError:
            return "Error: e2b_code_interpreter is not installed. Please install it."

        try:
            logger.info("Executing code in E2B sandbox...")
            # Note: Sandbox() inherently blocks if not using AsyncSandbox, but e2b_code_interpreter provides async APIs
            # The prompt uses `Sandbox` synchronous context manager, which we wrap safely
            # or we can use `AsyncSandbox` if it is supported in this version.
            # Let's use the standard synchronous Sandbox for maximum compatibility with the user's snippet.
            import asyncio
            
            def _run_sandbox():
                import os
                if self.api_key:
                    os.environ["E2B_API_KEY"] = self.api_key
                with Sandbox.create() as sandbox:
                    execution = sandbox.run_code(code)
                    
                    results = []
                    if hasattr(execution, 'logs') and execution.logs.stdout:
                        results.append(f"STDOUT:\n{''.join(execution.logs.stdout)}")
                    if hasattr(execution, 'logs') and execution.logs.stderr:
                        results.append(f"STDERR:\n{''.join(execution.logs.stderr)}")
                    if execution.error:
                        results.append(f"ERROR:\n{execution.error.name}: {execution.error.value}\n{execution.error.traceback}")
                    
                    # Capture chart outputs/images if any were generated natively
                    if execution.results:
                        for idx, res in enumerate(execution.results):
                            if hasattr(res, 'png') and res.png:
                                # We can return images to the multimodality pipeline!
                                results.append(f"[IMAGE GENERATED: Chart {idx}]")
                            if hasattr(res, 'text') and res.text:
                                results.append(f"RESULT TEXT: {res.text}")
                                
                    if not results:
                        return "Execution finished with no output."
                        
                    return "\n\n".join(results)
                    
            return await asyncio.to_thread(_run_sandbox)
            
        except Exception as e:
            logger.error(f"[CodeInterpreterTool] E2B execution failed: {str(e)}")
            return f"Error executing code sandbox: {str(e)}"
