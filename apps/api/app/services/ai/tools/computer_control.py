import base64
import io
import time
from typing import Any

from app.services.ai.tools.base import BaseTool

try:
    import pyautogui
    from PIL import ImageGrab
    # Implicit safety rails for autonomous agents
    pyautogui.PAUSE = 0.5 
    pyautogui.FAILSAFE = True
except ImportError:
    pyautogui = None
    ImageGrab = None


class ComputerControlTool(BaseTool):
    """
    A foundational tool for Agentic Desktop Automation.
    Allows the AI to take screenshots, map semantic elements to physical coordinates, and manipulate the OS directly.
    """

    def __init__(self):
        super().__init__()
        self.last_screenshot: dict | None = None

    @property
    def name(self) -> str:
        return "computer_control"

    @property
    def description(self) -> str:
        return (
            "Execute native OS actions like mouse clicks, keyboard typing, and desktop visual parsing using absolute coordinates. "
            "ONLY use this if web_search or app_launcher is insufficient. "
            "CRITICAL INSTRUCTION FOR VISION: If you identify bounding boxes in a [ymin, xmin, ymax, xmax] format scaled from 0-1000, "
            "you MUST convert them to physical X,Y pixels before interacting. "
            "E.g., x = (xmin + xmax)/2 * (width / 1000). y = (ymin + ymax)/2 * (height / 1000)."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The action to perform. Allowed: 'screenshot', 'click', 'double_click', 'type', 'press_key', 'drag'.",
                    "enum": ["screenshot", "click", "double_click", "type", "press_key", "drag"]
                },
                "x": {
                    "type": "integer",
                    "description": "The absolute X pixel coordinate on the screen. Required for click/drag actions."
                },
                "y": {
                    "type": "integer",
                    "description": "The absolute Y pixel coordinate on the screen. Required for click/drag actions."
                },
                "text": {
                    "type": "string",
                    "description": "Text to type. Required if action='type'."
                },
                "key": {
                    "type": "string",
                    "description": "Key to press. Required if action='press_key'. E.g., 'enter', 'win', 'esc'."
                },
                "end_x": {
                    "type": "integer",
                    "description": "Ending X coordinate for 'drag' action."
                },
                "end_y": {
                    "type": "integer",
                    "description": "Ending Y coordinate for 'drag' action."
                }
            },
            "required": ["action"]
        }

    async def execute(self, execution_context: dict, **kwargs) -> Any:
        if pyautogui is None or ImageGrab is None:
            return "Fatal: 'pyautogui' or 'Pillow' is not installed. Native computer control is unavailable. Run `pip install pyautogui Pillow`."

        action = kwargs.get("action")
        
        try:
            if action == "screenshot":
                # Capture primary monitor bounding box
                img = ImageGrab.grab()
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=85)
                byte_im = buf.getvalue()
                
                b64_str = base64.b64encode(byte_im).decode('utf-8')
                width, height = img.size
                
                # To feed back to Gemini multimodality!
                return {
                    "mime_type": "image/jpeg",
                    "data": b64_str,
                    "resolution": f"{width}x{height}",
                    "message": "Desktop image captured successfully. Next, extract bounding boxes or relative locations to generate literal pixel coordinate parameters (x, y) for further actions."
                }
                
            elif action in ("click", "double_click"):
                x = kwargs.get("x")
                y = kwargs.get("y")
                if x is None or y is None:
                    return "Error: Both 'x' and 'y' coordinates are required for clicking."
                
                # Smoothly move to coordinates simulating human curve and execute 
                pyautogui.moveTo(x, y, duration=0.4)
                
                if action == "click":
                    pyautogui.click()
                    return f"Clicked precisely at coordinates ({x}, {y})."
                else:
                    pyautogui.doubleClick()
                    return f"Double-clicked precisely at coordinates ({x}, {y})."

            elif action == "type":
                text = kwargs.get("text")
                if not text:
                    return "Error: 'text' parameter is required for typing."
                # Type characters realistically
                pyautogui.write(text, interval=0.04)
                return f"Typed textual payload safely: '{text}'"

            elif action == "press_key":
                key = kwargs.get("key")
                if not key:
                    return "Error: 'key' parameter is required."
                if "+" in key:
                    keys = [k.strip() for k in key.split("+")]
                    pyautogui.hotkey(*keys)
                else:
                    pyautogui.press(key)
                return f"Successfully pressed the physical key: '{key}'"
                
            elif action == "drag":
                x = kwargs.get("x")
                y = kwargs.get("y")
                e_x = kwargs.get("end_x")
                e_y = kwargs.get("end_y")
                
                if None in (x, y, e_x, e_y):
                    return "Error: 'x', 'y', 'end_x', and 'end_y' are universally required for a dragging sweep."
                    
                pyautogui.moveTo(x, y, duration=0.2)
                pyautogui.dragTo(e_x, e_y, duration=0.6, button='left')
                return f"Dragged cursor from ({x}, {y}) ending at ({e_x}, {e_y})."
                
            else:
                return f"Error: Unknown structural computer_control action '{action}'."
                
        except pyautogui.FailSafeException:
            return "CRITICAL INTERRUPT: The human user triggered the fail-safe by ripping the mouse to a screen corner! The automation loop has been forcefully aborted."
        except Exception as e:
            return f"Execution error in Desktop Subroutine: {e}"
