import asyncio
import datetime
import json
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, get_provider_router

logger = logging.getLogger(__name__)

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

async def fetch_real_time_news() -> str:
    try:
        from app.services.ai.tools.news_search import NewsSearchTool
        import json
        tool = NewsSearchTool()
        res = await tool.execute(
            execution_context={},
            query="top breaking news headlines today tech business sports",
            max_results=6,
            days=2,
            skip_images=True
        )
        data = json.loads(res)
        if "error" in data:
            raise Exception(data["error"])
        return json.dumps(data.get("articles", []))
    except Exception as e:
        logger.warning(f"[Dashboard] News tool fetch failed: {repr(e)}")
        return "Tavily search unavailable. Generate broadly plausible breaking news based on implicit parametric knowledge."

async def _generate_ai_dashboard_payload(weather_data: dict, today_events_titles: list, lat: str, lon: str, news_context: str):
    router = get_provider_router()
    today_dt = datetime.datetime.now().strftime("%A, %b %d")
    
    prompt = f"""
    You are an expert AI dashboard curator. Based on this live context, generate exactly one JSON object.
    
    Current Date: {today_dt}
    User Coordinates (Lat, Lon): {lat}, {lon}
    Weather: {weather_data.get('title')} {weather_data.get('condition', '')} in {weather_data.get('location', 'Unknown Location')}
    Calendar Events Today: {today_events_titles if today_events_titles else 'None explicitly defined'}
    Raw News Search Context: {news_context}
    
    The JSON MUST have:
    1. "weather_summary": A professional summary (roughly 2-3 lines, max 25 words).
    2. "calendar_summary": An insight about the schedule today (roughly 2-3 lines, max 25 words).
    3. "news_articles": An array of objects matching EXACTLY this structure:
       [ {{"domain": "tech", "title": "Headline", "summary": " • First bullet roughly 2 lines max 25 words\\n• Second bullet roughly 2 lines max 25 words"}}, ... ]
       MUST include EXACTLY these domains: "top", "tech", "local", "foreign", "business", "sports". EXACTLY 2 bullet points for the summary string.
       Format the news based on the search context provided or real-time insights/plausible generation for India/Global if context is missing or vague.
       
    Output strictly raw JSON starting with {{ and ending with }}. Do not wrap in markdown ``` codeblocks.
    """
    
    try:
        import asyncio
        response = await asyncio.wait_for(router._execute_with_router("chat", [{"role": "user", "content": prompt}], intent="dashboard"), timeout=20.0)
        
        # Accommodate object response from Gemini native providers lacking a raw strip()
        if hasattr(response, "text"):
            content = response.text or ""
        else:
            content = response
            
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        return json.loads(content)
    except (Exception, asyncio.CancelledError) as e:
        print(f"Fallback generation activated due to error: {e}")
        return {
            "weather_summary": f"Sensors offline. {weather_data.get('title', 'Local climate')} stabilized.",
            "calendar_summary": f"Your internal scheduler indicates minimal critical events for {today_dt.split(',')[0]}.",
            "news_articles": [
                {"domain": "top", "title": "System Operating in Autonomous Mode", "summary": "• Cloud synchronicity severed natively.\n• Re-establishing fallback handshakes locally."},
                {"domain": "tech", "title": "DNS Telemetry Subsystem Failure", "summary": "• Local host disconnected from resolving global LLM edge nodes.\n• Retrying quantum endpoints."},
                {"domain": "local", "title": "Local Network Intact", "summary": "• Internal data bus operating at 100% capacity.\n• No physical disruption detected."},
                {"domain": "business", "title": "Resource Allocation Offline", "summary": "• Live ticker streams paused.\n• Preserving local battery and compute reserves."},
                {"domain": "foreign", "title": "International Nodes Unreachable", "summary": "• Global ping requests timing out.\n• Awaiting packet restoration."},
                {"domain": "sports", "title": "Local Runtimes Operational", "summary": "• While cloud inferences fail, the core UI remains highly performant.\n• No critical runtime loss detected."}
            ]
        }

@router.get("/widgets")
async def get_dashboard_widgets(
    request: Request,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    lat = request.headers.get("X-User-Lat")
    lon = request.headers.get("X-User-Lon")

    if not lat or not lon:
        if user.last_known_lat and user.last_known_lon:
            lat, lon = str(user.last_known_lat), str(user.last_known_lon)
        else:
            lat, lon = "28.6139", "77.2090"

    weather_task = asyncio.create_task(fetch_weather(lat, lon))
    news_task = asyncio.create_task(fetch_real_time_news())
    calendar_task = asyncio.create_task(_generate_calendar_grid(user.id, db))
    
    weather, news_context, (calendar_grid, today, today_events) = await asyncio.gather(
        weather_task, news_task, calendar_task
    )
    
    today_dt = datetime.datetime.now()
    calendar_title = today_dt.strftime("%A, %b %d")
    
    # Fully AI Generated structure mapping!
    ai_data = await _generate_ai_dashboard_payload(weather, today_events, lat, lon, news_context)
    
    # Build dynamic next_up string
    next_up_str = today_events[0] if today_events else "No immediate events • Schedule Clear"
    
    return {
        "widgets": [
            {
                "id": "weather",
                "title": weather.get("title", ""),
                "subtitle": weather.get("subtitle", ""),
                "condition": weather.get("condition", ""),
                "location": weather.get("location", ""),
                "ai_summary": ai_data.get("weather_summary", "Stable weather optimal."),
                "is_day": weather.get("is_day", 1),
                "forecast": weather.get("forecast", [])
            },
            {
                "id": "calendar",
                "badge": "Next Up",
                "title": calendar_title,
                "subtitle": next_up_str,
                "ai_summary": ai_data.get("calendar_summary", "Routine schedule loaded."),
                "current_day": today,
                "month_grid": calendar_grid
            },
            {
                "id": "news",
                "articles": ai_data.get("news_articles", [])
            }
        ]
    }

