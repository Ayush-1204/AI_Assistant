import logging
import asyncio
import os
import psutil
from typing import ClassVar, Dict, Any

from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

class AppLauncherTool(BaseTool):
    name = "app_launcher"
    description = "Launch local desktop applications (like notepad, calc, etc) or check running processes."
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "The action to take. Allowed: 'launch_app', 'check_running'.",
                "enum": ["launch_app", "check_running"]
            },
            "app_name": {
                "type": "string",
                "description": "The name of the app to launch (e.g. 'notepad', 'calc', 'explorer') or process to check."
            }
        },
        "required": ["action", "app_name"]
    }

    async def execute(self, execution_context: dict, **kwargs) -> Any:
        action = kwargs.get("action")
        app_name = kwargs.get("app_name")

        try:
            if action == "launch_app":
                # Basic os.startfile for Windows native mapping fallback
                import threading
                def _launch(): os.system(f"start {app_name}")
                threading.Thread(target=_launch).start()
                return {"status": "success", "message": f"Sent launch command for {app_name}"}

            elif action == "check_running":
                if not app_name: return {"status": "error", "message": "app_name required"}
                is_running = False
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'] and app_name.lower() in proc.info['name'].lower():
                        is_running = True
                        break
                return {"status": "success", "is_running": is_running, "app": app_name}
                
            else:
                return {"status": "error", "message": "Invalid action."}

        except Exception as e:
            logger.error(f"AppLauncherTool error: {e}")
            return {"status": "error", "message": str(e)}
