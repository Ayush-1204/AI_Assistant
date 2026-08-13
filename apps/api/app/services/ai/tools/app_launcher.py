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
        action = kwargs.get("action", "launch_app")
        app_name = kwargs.get("app_name") or kwargs.get("application_name") or kwargs.get("query")

        try:
            if action == "launch_app":
                app_name_lower = str(app_name).lower()
                target = app_name
                
                # Map common friendly names to executables or URIs
                if "spotify" in app_name_lower: target = "spotify:"
                elif "calc" in app_name_lower: target = "calc.exe"
                elif "notepad" in app_name_lower: target = "notepad.exe"
                elif "word" in app_name_lower and "pass" not in app_name_lower: target = "winword.exe"
                elif "excel" in app_name_lower: target = "excel.exe"
                elif "powerpoint" in app_name_lower: target = "powerpnt.exe"
                elif "browser" in app_name_lower or "chrome" in app_name_lower: target = "chrome.exe"
                elif "edge" in app_name_lower: target = "msedge.exe"
                
                import threading
                def _launch(): 
                    # If it's a URI, use explorer, otherwise use start with empty title
                    if str(target).endswith(":"):
                        os.system(f"explorer {target}")
                    else:
                        os.system(f'start "" "{target}"')
                        
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
