import datetime
import logging
from typing import Any

from googleapiclient.discovery import build

from app.integrations.google.auth import GoogleAuthService

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    def __init__(self, auth_service: GoogleAuthService):
        self.auth_service = auth_service
        
    async def _execute_call(self, user_id: int, fn):
        creds = await self.auth_service.get_credentials(user_id)
        if not creds:
            raise ValueError(f"No valid Google credentials found for user {user_id}")
            
        old_token = creds.token
        service = build('calendar', 'v3', credentials=creds)
        
        import asyncio
        result = await asyncio.to_thread(fn, service)
        
        if creds.token != old_token:
            await self.auth_service.update_credentials(user_id, creds)
            
        return result

    def _get_target_calendars(self, service):
        try:
            calendars_result = service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])
            
            target_calendars = ['primary']
            for c in calendars:
                if 'holiday' in c.get('id', '').lower():
                    if c['id'] not in target_calendars:
                        target_calendars.append(c['id'])
            return target_calendars
        except Exception:
            return ['primary']

    async def get_todays_schedule(self, user_id: int):
                
        now = datetime.datetime.now(datetime.timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat().replace('+00:00', 'Z')
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat().replace('+00:00', 'Z')
        
        def _call(service):
            cals = self._get_target_calendars(service)
            all_events = []
            for cal_id in cals:
                try:
                    res = service.events().list(
                        calendarId=cal_id, 
                        timeMin=start_of_day,
                        timeMax=end_of_day,
                        singleEvents=True,
                        maxResults=2500,
                        orderBy='startTime'
                    ).execute()
                    events = res.get('items', [])
                    for e in events:
                        if cal_id != 'primary':
                            e['is_holiday'] = True
                    all_events.extend(events)
                except Exception:
                    pass
            all_events.sort(key=lambda x: x.get('start', {}).get('dateTime', x.get('start', {}).get('date', '')))
            return all_events
            
        all_events = await self._execute_call(user_id, _call)
        return all_events

    async def get_upcoming_events(self, user_id: int, max_results: int = 10):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
        def _call(service):
            cals = self._get_target_calendars(service)
            all_events = []
            for cal_id in cals:
                try:
                    res = service.events().list(
                        calendarId=cal_id, 
                        timeMin=now,
                        singleEvents=True,
                        maxResults=2500,
                        orderBy='startTime'
                    ).execute()
                    events = res.get('items', [])
                    for e in events:
                        if cal_id != 'primary':
                            e['is_holiday'] = True
                    all_events.extend(events)
                except Exception:
                    pass
            all_events.sort(key=lambda x: x.get('start', {}).get('dateTime', x.get('start', {}).get('date', '')))
            return all_events
            
        all_events = await self._execute_call(user_id, _call)
        return all_events

    async def get_monthly_events(self, user_id: int, year: int, month: int):
        start_date = datetime.datetime(year, month, 1, tzinfo=datetime.timezone.utc)
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        end_date = datetime.datetime(next_year, next_month, 1, tzinfo=datetime.timezone.utc)
        
        def _call(service):
            cals = self._get_target_calendars(service)
            all_events = []
            for cal_id in cals:
                try:
                    res = service.events().list(
                        calendarId=cal_id, 
                        timeMin=start_date.isoformat().replace('+00:00', 'Z'),
                        timeMax=end_date.isoformat().replace('+00:00', 'Z'),
                        singleEvents=True,
                        maxResults=2500,
                        orderBy='startTime'
                    ).execute()
                    events = res.get('items', [])
                    for e in events:
                        if cal_id != 'primary':
                            e['is_holiday'] = True
                    all_events.extend(events)
                except Exception:
                    pass
            all_events.sort(key=lambda x: x.get('start', {}).get('dateTime', x.get('start', {}).get('date', '')))
            return all_events
            
        all_events = await self._execute_call(user_id, _call)
        return all_events

    async def create_event(self, user_id: int, summary: str, description: str, start_time: str, end_time: str, reminders: list | dict | None = None, time_zone: str = 'Asia/Kolkata'):
        event: dict[str, Any] = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': time_zone},
            'end': {'dateTime': end_time, 'timeZone': time_zone},
        }
        if reminders is not None:
            if isinstance(reminders, dict) and 'overrides' in reminders:
                # LLM generated the full object instead of a list
                event['reminders'] = reminders
            elif isinstance(reminders, list):
                # LLM correctly generated a list of overrides
                event['reminders'] = {
                    'useDefault': False,
                    'overrides': reminders
                }
        def _call(service):
            return service.events().insert(calendarId='primary', body=event).execute()
            
        return await self._execute_call(user_id, _call)

    async def update_event(self, user_id: int, event_id: str, updates: dict):
        def _call(service):
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            for key, value in updates.items():
                if key in ['start', 'end'] and isinstance(value, str):
                    event[key] = {'dateTime': value}
                else:
                    event[key] = value
            return service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
            
        return await self._execute_call(user_id, _call)

    async def delete_event(self, user_id: int, event_id: str):
        def _call(service):
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            return True
            
        return await self._execute_call(user_id, _call)
        
    async def find_free_time(self, user_id: int, date: str):
        start_time = f"{date}T00:00:00Z"
        end_time = f"{date}T23:59:59Z"
        
        body = {
            "timeMin": start_time,
            "timeMax": end_time,
            "timeZone": 'UTC',
            "items": [{"id": 'primary'}]
        }
        
        def _call(service):
            return service.freebusy().query(body=body).execute()
            
        freebusy_result = await self._execute_call(user_id, _call)
        calendars = freebusy_result.get('calendars', {})
        primary = calendars.get('primary', {})
        busy = primary.get('busy', [])
        
        return {"date": date, "busy_slots": busy}
