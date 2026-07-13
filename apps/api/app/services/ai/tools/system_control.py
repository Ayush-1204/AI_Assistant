import logging
import asyncio
from typing import ClassVar, Dict, Any
import psutil
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

class SystemControlTool(BaseTool):
    name = "system_control"
    description = "Control local desktop system hardware like volume, brightness, and check battery levels."
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "The system action to take. Allowed: 'set_volume', 'get_volume', 'set_brightness', 'get_brightness', 'get_battery'.",
                "enum": ["set_volume", "get_volume", "set_brightness", "get_brightness", "get_battery"]
            },
            "value": {
                "type": "integer",
                "description": "The percentage (0-100) to set volume or brightness to. Not required for 'get' actions."
            }
        },
        "required": ["action"]
    }

    async def execute(self, execution_context: dict, **kwargs) -> Any:
        action = kwargs.get("action")
        value = kwargs.get("value")

        try:
            if action == "get_battery":
                batt = psutil.sensors_battery()
                if not batt:
                    return {"status": "error", "message": "No battery sensor found."}
                return {
                    "status": "success", 
                    "battery_percent": batt.percent, 
                    "power_plugged": batt.power_plugged
                }

            elif action == "set_brightness":
                if value is None: return {"status": "error", "message": "value required for set_brightness"}
                sbc.set_brightness(value)
                return {"status": "success", "message": f"Brightness set to {value}%"}

            elif action == "get_brightness":
                current_brightness = sbc.get_brightness()
                return {"status": "success", "brightness": current_brightness[0] if isinstance(current_brightness, list) else current_brightness}

            elif action == "set_volume":
                if value is None: return {"status": "error", "message": "value required for set_volume"}
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                # scalar volume is float 0.0 to 1.0
                volume.SetMasterVolumeLevelScalar(max(0.0, min(1.0, value / 100.0)), None)
                return {"status": "success", "message": f"Volume set to {value}%"}

            elif action == "get_volume":
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                current_vol = round(volume.GetMasterVolumeLevelScalar() * 100)
                return {"status": "success", "volume": current_vol}

            else:
                return {"status": "error", "message": "Invalid action."}

        except Exception as e:
            logger.error(f"SystemControlTool error: {e}")
            return {"status": "error", "message": str(e)}
