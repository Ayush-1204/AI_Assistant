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
                "description": "The action to take. Allowed: 'launch_app' (or 'open', 'launch'), 'check_running', 'minimize_app', 'close_app'.",
                "enum": ["launch_app", "check_running", "minimize_app", "close_app", "open", "launch", "minimize", "close"]
            },
            "app_name": {
                "type": "string",
                "description": "The name of the app to launch (e.g. 'notepad', 'calc', 'explorer') or process to check."
            }
        },
        "required": ["action", "app_name"]
    }

    @staticmethod
    def _find_windows_app_sync(query: str) -> str | None:
        query_lower = query.lower().replace("yt music", "youtube music")
        import subprocess
        import json
        import os
        
        # 1. Check UWP / Store apps via Get-StartApps
        try:
            res = subprocess.run(["powershell", "-Command", "Get-StartApps | ConvertTo-Json"], capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout:
                apps = json.loads(res.stdout)
                if isinstance(apps, dict):
                    apps = [apps]
                for app in apps:
                    name = app.get("Name", "")
                    if query_lower in name.lower():
                        appid = app.get("AppID")
                        if appid:
                            return f"explorer shell:AppsFolder\\{appid}"
        except Exception as e:
            logger.error(f"Error checking Get-StartApps: {e}")

        # 2. Check Classic Desktop Apps (.lnk)
        appdata = os.environ.get('APPDATA')
        programdata = os.environ.get('ALLUSERSPROFILE')
        
        paths = []
        if appdata:
            paths.append(os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs"))
        if programdata:
            paths.append(os.path.join(programdata, r"Microsoft\Windows\Start Menu\Programs"))
            
        for p in paths:
            if not os.path.exists(p): continue
            for root, _, files in os.walk(p):
                for f in files:
                    if f.endswith('.lnk'):
                        name = f[:-4].lower()
                        if query_lower in name:
                            return os.path.join(root, f)
                            
        return None

    async def execute(self, execution_context: dict, **kwargs) -> Any:
        action = kwargs.get("action", "launch_app")
        app_name = kwargs.get("app_name") or kwargs.get("application_name") or kwargs.get("application") or kwargs.get("query")

        try:
            if action in ("launch_app", "open", "launch"):
                if not app_name:
                    return {"status": "error", "message": "app_name required"}
                app_name = str(app_name)
                app_name_lower = app_name.lower()
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
                else:
                    # Dynamic Search
                    found = await asyncio.to_thread(self._find_windows_app_sync, app_name)
                    if found:
                        target = found
                    else:
                        return {"status": "error", "message": f"Could not find any installed application matching '{app_name}'"}
                
                import threading
                import subprocess
                def _launch(): 
                    # If it's a URI or shell command, use subprocess directly, otherwise use start with empty title
                    if target.startswith("explorer shell:") or target.endswith(":"):
                        cmd = target if target.startswith("explorer") else f"explorer {target}"
                        subprocess.run(cmd, shell=True)
                    else:
                        subprocess.run(f'start "" "{target}"', shell=True)
                        
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
                
            elif action in ("close_app", "close"):
                if not app_name: return {"status": "error", "message": "app_name required"}
                closed = False
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'] and app_name.lower() in proc.info['name'].lower():
                        proc.kill()
                        closed = True
                return {"status": "success", "message": f"Closed {app_name}" if closed else f"Could not find running instance of {app_name}"}

            elif action in ("minimize_app", "minimize"):
                if not app_name: return {"status": "error", "message": "app_name required"}
                import subprocess
                # Use powershell to minimize the window by getting the MainWindowHandle of the matching process
                ps_script = f"""
                $sig = @'
                [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
                '@
                Add-Type -MemberDefinition $sig -name NativeMethods -namespace Win32 -ErrorAction SilentlyContinue
                $procs = Get-Process | Where-Object {{ $_.MainWindowTitle -match "{app_name}" -or $_.Name -match "{app_name}" }}
                $minimized = $false
                foreach ($p in $procs) {{
                    if ($p.MainWindowHandle -ne 0) {{
                        [Win32.NativeMethods]::ShowWindowAsync($p.MainWindowHandle, 2) | Out-Null
                        $minimized = $true
                    }}
                }}
                if ($minimized) {{ Write-Output "Success" }} else {{ Write-Output "Not Found" }}
                """
                res = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
                if "Success" in res.stdout:
                    return {"status": "success", "message": f"Minimized {app_name}"}
                else:
                    return {"status": "error", "message": f"Could not find a visible window for {app_name}"}

            else:
                return {"status": "error", "message": f"Invalid action: {action}"}

        except Exception as e:
            logger.error(f"AppLauncherTool error: {e}")
            return {"status": "error", "message": str(e)}
