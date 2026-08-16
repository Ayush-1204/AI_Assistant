import asyncio
import datetime
import json
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, get_provider_router, decode_access_token
from fastapi import Query
from app.config import settings

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

calendar_ws_manager = ConnectionManager()

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/budgets")
async def get_budgets():
    provider_router = get_provider_router()
    budgets_info = []
    
    for name, budget in provider_router.budgets.items():
        budget.rpm_bucket.check_capacity(0)
        budget.tpm_bucket.check_capacity(0)
        
        budgets_info.append({
            "provider": name,
            "rpm_capacity": budget.rpm_bucket.capacity,
            "rpm_remaining": budget.rpm_bucket.tokens,
            "tpm_capacity": budget.tpm_bucket.capacity,
            "tpm_remaining": budget.tpm_bucket.tokens,
            "total_cost": budget.total_cost
        })
    return budgets_info

def _wmo_to_condition(wmo: int) -> str:
    if wmo == 0: return "Clear"
    if wmo in [1]: return "Mostly Clear"
    if wmo in [2]: return "Partly Cloudy"
    if wmo in [3]: return "Overcast"
    if wmo in [45, 48]: return "Fog"
    if wmo in [51, 53, 55, 56, 57]: return "Drizzle"
    if wmo in [61, 63, 65, 66, 67, 80, 81, 82]: return "Rain"
    if wmo in [71, 73, 75, 77, 85, 86]: return "Snow"
    if wmo >= 95: return "Storm"
    return "Cloudy"

async def fetch_weather(lat: str = "28.6139", lon: str = "77.2090") -> dict[str, Any]:
    try:
        from app.services.ai.tools.weather import WeatherTool
        import json
        tool = WeatherTool()
        res = await tool.execute(execution_context={"lat": lat, "lon": lon}, location="auto")
        data = json.loads(res)
        if "error" in data:
            raise Exception(data["error"])
            
        current = data.get("current", {})
        forecast_7 = data.get("forecast_7_days", [])
        
        forecast = []
        for day in forecast_7[:5]:
            forecast.append({
                "day": day.get("day"),
                "high": int(day.get("high")) if day.get("high") is not None else "--",
                "low": int(day.get("low")) if day.get("low") is not None else "--",
                "condition": day.get("condition")
            })
            
        return {
            "title": current.get("temperature", "--"),
            "subtitle": f"Feels like {current.get('feels_like', '--')}",
            "condition": current.get("condition", "--"),
            "location": data.get("location", "Unknown Location"),
            "is_day": 1,
            "wind_speed": current.get("wind_speed", "0 km/h"),
            "humidity": current.get("humidity", "0%"),
            "forecast": forecast
        }
    except Exception as e:
        logger.warning(f"Failed to fetch weather via tool: {e}")
        return {"title": "31.8°C", "subtitle": "Partly Cloudy", "condition": "Partly Cloudy", "location": "Unknown", "is_day": 1, "forecast": []}

@router.get("/calendar/events")
async def get_calendar_events(
    year: int | None = None,
    month: int | None = None,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    events_payload = []
    try:
        from app.integrations.google.auth import GoogleAuthService
        from app.integrations.google.calendar import GoogleCalendarService
        from app.repositories.oauth_repository import OAuthRepository
        repo = OAuthRepository(db)
        auth = GoogleAuthService(repo)
        cal = GoogleCalendarService(auth)
        
        now = datetime.datetime.now()
        target_year = year or now.year
        target_month = month or now.month
        events = await cal.get_monthly_events(user.id, target_year, target_month)
        
        for evt in events:
            start_dt = evt.get('start', {}).get('dateTime') or evt.get('start', {}).get('date')
            end_dt = evt.get('end', {}).get('dateTime') or evt.get('end', {}).get('date')
            events_payload.append({
                "id": evt.get("id"),
                "summary": evt.get("summary", "Busy"),
                "location": evt.get("location", ""),
                "start": start_dt,
                "end": end_dt,
            })
    except Exception as e:
        logger.warning(f"Failed to fetch calendar events: {e}")
        pass
        
    return {"events": events_payload}

from pydantic import BaseModel
class CreateEventRequest(BaseModel):
    summary: str
    description: str
    start_time: str
    end_time: str

@router.post("/calendar/events")
async def create_calendar_event(
    req: CreateEventRequest,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        from app.integrations.google.auth import GoogleAuthService
        from app.integrations.google.calendar import GoogleCalendarService
        from app.repositories.oauth_repository import OAuthRepository
        cal = GoogleCalendarService(GoogleAuthService(OAuthRepository(db)))
        evt = await cal.create_event(user.id, req.summary, req.description, req.start_time, req.end_time)
        return {"id": evt.get("id")}
    except Exception as e:
        logger.warning(f"Failed to create event: {e}")
        return {"error": str(e)}

@router.delete("/calendar/events/{event_id}")
async def delete_calendar_event(
    event_id: str,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        from app.integrations.google.auth import GoogleAuthService
        from app.integrations.google.calendar import GoogleCalendarService
        from app.repositories.oauth_repository import OAuthRepository
        cal = GoogleCalendarService(GoogleAuthService(OAuthRepository(db)))
        await cal.delete_event(user.id, event_id)
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}

async def fetch_news() -> dict[str, str]:
    return {"title": "Tech Innovations Surge", "subtitle": "Major technological breakthroughs in the region"}

async def _generate_calendar_grid(user_id: int, db: AsyncSession):
    today = datetime.datetime.now().day
    grid = []
    events_set = set()
    today_events_titles = []
    
    try:
        from app.integrations.google.auth import GoogleAuthService
        from app.integrations.google.calendar import GoogleCalendarService
        from app.repositories.oauth_repository import OAuthRepository
        repo = OAuthRepository(db)
        auth = GoogleAuthService(repo)
        cal = GoogleCalendarService(auth)
        
        events = await cal.get_upcoming_events(user_id, max_results=30)
        for evt in events:
            start_dt = evt.get('start', {}).get('dateTime') or evt.get('start', {}).get('date')
            if start_dt:
                dt = datetime.datetime.fromisoformat(start_dt.replace("Z", "+00:00"))
                if dt.month == datetime.datetime.now().month:
                    events_set.add(dt.day)
                    if dt.day == today:
                        today_events_titles.append(f"{evt.get('summary')} at {dt.strftime('%H:%M')}")
    except Exception:
        pass # Silently fallback to an empty grid if user has no Google Account OAuth explicitly granted
        
    for i in range(-2, 33):
        day = i if 1 <= i <= 31 else 0
        grid.append({"day": day, "hasEvent": day in events_set})
    return grid, today, today_events_titles

from app.routers.dashboard_rules import (
    _generate_rule_based_weather_summary,
    _generate_rule_based_calendar_summary,
    _fetch_curated_news_domains
)

@router.get("/widgets/weather")
async def get_weather_widget(
    request: Request,
    user = Depends(get_current_user)
) -> dict[str, Any]:
    lat = request.headers.get("X-User-Lat")
    lon = request.headers.get("X-User-Lon")

    if not lat or not lon:
        if user.last_known_lat and user.last_known_lon:
            lat, lon = str(user.last_known_lat), str(user.last_known_lon)
        else:
            lat, lon = "28.6139", "77.2090"

    weather = await fetch_weather(lat, lon)
    weather_summary = _generate_rule_based_weather_summary(weather)
    
    return {
        "id": "weather",
        "title": weather.get("title", ""),
        "subtitle": weather.get("subtitle", ""),
        "condition": weather.get("condition", ""),
        "location": weather.get("location", "Unknown Location"),
        "ai_summary": weather_summary,
        "is_day": weather.get("is_day", 1),
        "forecast": weather.get("forecast", [])
    }

@router.get("/widgets/calendar")
async def get_calendar_widget(
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    calendar_grid, today, today_events = await _generate_calendar_grid(user.id, db)
    calendar_summary = _generate_rule_based_calendar_summary(today_events)
    
    today_dt = datetime.datetime.now()
    calendar_title = today_dt.strftime("%A, %b %d")
    next_up_str = today_events[0].split(" at ")[0] if today_events else "No immediate events • Schedule Clear"
    
    return {
        "id": "calendar",
        "badge": "Next Up",
        "title": calendar_title,
        "subtitle": next_up_str,
        "ai_summary": calendar_summary,
        "current_day": today,
        "month_grid": calendar_grid
    }

@router.get("/widgets/news")
async def get_news_widget(
    request: Request,
    user = Depends(get_current_user)
) -> dict[str, Any]:
    lat = request.headers.get("X-User-Lat")
    lon = request.headers.get("X-User-Lon")

    if not lat or not lon:
        if user.last_known_lat and user.last_known_lon:
            lat, lon = str(user.last_known_lat), str(user.last_known_lon)
        else:
            lat, lon = "28.6139", "77.2090"

    # Quick fetch just to resolve city name for news domain queries
    weather = await fetch_weather(lat, lon)
    location_name = weather.get("location", "Unknown Location")
    
    news_articles = await _fetch_curated_news_domains(location_name)
    
    return {
        "id": "news",
        "articles": news_articles
    }



@router.websocket("/calendar/ws")
async def calendar_websocket(websocket: WebSocket, token: str = Query(default=None)):
    if not token:
        await websocket.close(code=1008)
        return
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if sub is None:
            await websocket.close(code=1008)
            return
        user_id = int(sub)
    except Exception:
        await websocket.close(code=1008)
        return
        
    await calendar_ws_manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        calendar_ws_manager.disconnect(websocket, user_id)


@router.post("/calendar/watch")
async def register_calendar_watch(
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.integrations.google.auth import GoogleAuthService
    from app.integrations.google.calendar import GoogleCalendarService
    from app.repositories.oauth_repository import OAuthRepository
    
    cal = GoogleCalendarService(GoogleAuthService(OAuthRepository(db)))
    
    # Needs a public URL. Fallback to localhost if not set (which will fail for Google, but good for testing logic)
    public_url = settings.WEBHOOK_PUBLIC_URL
    if not public_url:
        return {"error": "WEBHOOK_PUBLIC_URL not configured. Cannot register watch."}
        
    webhook_url = f"{public_url.rstrip('/')}/webhooks/calendar"
    
    watch = await cal.register_watch(user.id, db, webhook_url)
    if not watch:
        return {"error": "Failed to register watch channel"}
        
    return {"status": "Watch registered", "channel_id": watch.channel_id, "expiration": watch.expiration.isoformat()}
