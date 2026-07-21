import datetime
import logging

from googleapiclient.discovery import build

from app.integrations.google.auth import GoogleAuthService

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    def __init__(self, auth_service: GoogleAuthService):
        self.auth_service = auth_service
        
    async def _get_client(self, user_id: int):
        creds = await self.auth_service.get_credentials(user_id)
        if not creds:
            raise ValueError(f"No valid Google credentials found for user {user_id}")
        return build('calendar', 'v3', credentials=creds)

    async def get_todays_schedule(self, user_id: int):
        service = await self._get_client(user_id)
        
        now = datetime.datetime.now(datetime.timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat().replace('+00:00', 'Z')
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat().replace('+00:00', 'Z')
        
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])

    async def get_upcoming_events(self, user_id: int, max_results: int = 10):
        service = await self._get_client(user_id)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=now,
            maxResults=max_results, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])

    async def get_monthly_events(self, user_id: int, year: int, month: int):
        service = await self._get_client(user_id)
        start_date = datetime.datetime(year, month, 1, tzinfo=datetime.timezone.utc)
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        end_date = datetime.datetime(next_year, next_month, 1, tzinfo=datetime.timezone.utc)
        
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=start_date.isoformat().replace('+00:00', 'Z'),
            timeMax=end_date.isoformat().replace('+00:00', 'Z'),
            singleEvents=True,
            maxResults=2500,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])

    async def create_event(self, user_id: int, summary: str, description: str, start_time: str, end_time: str):
        service = await self._get_client(user_id)
        event = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_time},
            'end': {'dateTime': end_time},
        }
        event_result = service.events().insert(calendarId='primary', body=event).execute()
        return event_result

    async def update_event(self, user_id: int, event_id: str, updates: dict):
        service = await self._get_client(user_id)
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        for key, value in updates.items():
            if key in ['start', 'end'] and isinstance(value, str):
                event[key] = {'dateTime': value}
            else:
                event[key] = value
        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        return updated_event

    async def delete_event(self, user_id: int, event_id: str):
        service = await self._get_client(user_id)
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return True
        
    async def find_free_time(self, user_id: int, date: str):
        service = await self._get_client(user_id)
        start_time = f"{date}T00:00:00Z"
        end_time = f"{date}T23:59:59Z"
        
        body = {
            "timeMin": start_time,
            "timeMax": end_time,
            "timeZone": 'UTC',
            "items": [{"id": 'primary'}]
        }
        
        freebusy_result = service.freebusy().query(body=body).execute()
        calendars = freebusy_result.get('calendars', {})
        primary = calendars.get('primary', {})
        busy = primary.get('busy', [])
        
        return {"date": date, "busy_slots": busy}
