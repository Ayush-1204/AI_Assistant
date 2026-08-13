import json

from app.integrations.google.calendar import GoogleCalendarService
from app.services.ai.tools.base import BaseTool


class CalendarTool(BaseTool):
    def __init__(self, service: GoogleCalendarService):
        self.service = service
        
    @property
    def name(self) -> str:
        return "google_calendar"
        
    @property
    def description(self) -> str:
        return "Manage user's Google Calendar. Allows checking today's schedule, upcoming events, creating, deleting events, and finding free time."
        
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["todays_schedule", "upcoming_events", "create_event", "insert", "delete_event", "find_free_time"],
                    "description": "The calendar action to perform."
                },
                "summary": {
                    "type": "string",
                    "description": "Title of event for create_event"
                },
                "description": {
                    "type": "string",
                    "description": "Description for create_event"
                },
                "start_time": {
                    "type": "string",
                    "description": "ISO8601 for create_event (e.g. 2026-07-03T10:00:00Z)"
                },
                "end_time": {
                    "type": "string",
                    "description": "ISO8601 for create_event"
                },
                "event_id": {
                    "type": "string",
                    "description": "ID for delete_event"
                },
                "reminders": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "method": {"type": "string", "enum": ["email", "popup"]},
                            "minutes": {"type": "integer"}
                        }
                    },
                    "description": "Optional list of reminders. E.g. [{'method': 'popup', 'minutes': 120}]"
                },
                "date": {
                    "type": "string",
                    "description": "YYYY-MM-DD for find_free_time"
                }
            },
            "required": ["action"]
        }
        
    async def execute(self, execution_context: dict, **kwargs) -> str:
        action = kwargs.get("action")
        
        # Handle planner hallucinations
        if "event_title" in kwargs and "summary" not in kwargs:
            kwargs["summary"] = kwargs.pop("event_title")
        elif "title" in kwargs and "summary" not in kwargs:
            kwargs["summary"] = kwargs.pop("title")
            
        if "reminder_minutes" in kwargs and "reminders" not in kwargs:
            kwargs["reminders"] = [{"method": "popup", "minutes": int(kwargs.pop("reminder_minutes"))}]
            
        if not action:
            if "summary" in kwargs or "start_time" in kwargs:
                action = "create_event"
            elif "event_id" in kwargs:
                action = "delete_event"
            elif "date" in kwargs:
                action = "find_free_time"
            else:
                action = "todays_schedule"

        user_id = execution_context.get("user_id")
        if not user_id:
            return "Error: Unauthorized. Cannot determine user."
        
        try:
            if action == "todays_schedule":
                rv = await self.service.get_todays_schedule(user_id)
                return json.dumps(rv, default=str)[:2000]
            elif action == "upcoming_events":
                rv = await self.service.get_upcoming_events(user_id)
                return json.dumps(rv, default=str)[:2000]
            elif action == "create_event" or action == "insert":
                start_time = kwargs.get('start_time')
                if not start_time:
                    if 'time_offset_hours' in kwargs:
                        import datetime
                        dt = datetime.datetime.now() + datetime.timedelta(hours=float(kwargs['time_offset_hours']))
                        start_time = dt.isoformat()
                    else:
                        raise KeyError('start_time is required')
                
                end_time = kwargs.get('end_time')
                if not end_time:
                    import datetime
                    dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    end_time = (dt + datetime.timedelta(hours=1)).isoformat().replace('+00:00', 'Z')
                    
                rv = await self.service.create_event(
                    user_id, 
                    kwargs['summary'], 
                    kwargs.get('description',''), 
                    start_time, 
                    end_time,
                    kwargs.get('reminders')
                )
                
                reminder_text = "with reminders" if kwargs.get('reminders') or "reminder_minutes" in kwargs else "without reminders"
                return f"Event '{kwargs['summary']}' successfully scheduled for {start_time} to {end_time} {reminder_text}. Link: {rv.get('htmlLink')} Event ID: {rv.get('id')}"
            elif action == "delete_event":
                await self.service.delete_event(user_id, kwargs['event_id'])
                return "Event deleted successfully."
            elif action == "find_free_time":
                rv = await self.service.find_free_time(user_id, kwargs['date'])
                return json.dumps(rv, default=str)
            else:
                return f"Error: Unknown calendar action {action}."
        except Exception as e:
            raise e
