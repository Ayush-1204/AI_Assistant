import json
from typing import Any, Tuple, List

def parse_json_objects_from_stream(buffer: str) -> Tuple[List[dict[str, Any]], str]:
    """
    Yields fully formed JSON objects from a string buffer containing a JSON array or objects.
    Returns the parsed objects and the remaining unparsed buffer string.
    """
    objects = []
    depth = 0
    in_string = False
    escape = False
    start = -1
    last_end = 0
    
    for i, char in enumerate(buffer):
        if escape:
            escape = False
            continue
        if char == '\\':
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
            
        if not in_string:
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and start != -1:
                    obj_str = buffer[start:i+1]
                    try:
                        obj = json.loads(obj_str)
                        objects.append(obj)
                        last_end = i + 1
                    except Exception:
                        # Malformed object or incomplete, ignore for now
                        pass
                        
    remaining_buffer = buffer[last_end:]
    return objects, remaining_buffer
