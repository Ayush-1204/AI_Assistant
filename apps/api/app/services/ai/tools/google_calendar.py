import json
from app.services.ai.tools.base import BaseTool
from app.integrations.google.calendar import GoogleCalendarService

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
            "action": "string (todays_schedule | upcoming_events | create_event | delete_event | find_free_time)",
            "summary": "string (optional): Title of event for create_event",
            "description": "string (optional): Description for create_event",
            "start_time": "string (optional): ISO8601 for create_event (e.g. 2026-07-03T10:00:00Z)",
            "end_time": "string (optional): ISO8601 for create_event",
            "event_id": "string (optional): ID for delete_event",
            "date": "string (optional): YYYY-MM-DD for find_free_time"
        }
        
    async def execute(self, execution_context: dict, **kwargs) -> str:
        action = kwargs.get("action")
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
            elif action == "create_event":
                rv = await self.service.create_event(
                    user_id, 
                    kwargs['summary'], 
                    kwargs.get('description',''), 
                    kwargs['start_time'], 
                    kwargs['end_time']
                )
                return f"Event created. Link: {rv.get('htmlLink')}"
            elif action == "delete_event":
                await self.service.delete_event(user_id, kwargs['event_id'])
                return "Event deleted successfully."
            elif action == "find_free_time":
                rv = await self.service.find_free_time(user_id, kwargs['date'])
                return json.dumps(rv, default=str)
            else:
                return f"Error: Unknown calendar action {action}."
        except Exception as e:
            return f"Calendar execution error: {str(e)}"
