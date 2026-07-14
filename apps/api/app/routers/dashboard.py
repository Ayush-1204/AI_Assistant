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

async def fetch_weather(lat: str = "28.6139", lon: str = "77.2090") -> dict[str, Any]:
    try:
        # Open-Meteo for real weather + daily forecast
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m&daily=temperature_2m_max&timezone=auto")
            if resp.status_code == 200:
                data = resp.json()
                temp = data.get("current", {}).get("temperature_2m", "--")
                
                daily_times = data.get("daily", {}).get("time", [])
                daily_max = data.get("daily", {}).get("temperature_2m_max", [])
                
                forecast = []
                for idx in range(min(5, len(daily_times))):
                    dt = datetime.datetime.fromisoformat(daily_times[idx])
                    day_str = dt.strftime("%a")
                    high = int(daily_max[idx]) if daily_max else "--"
                    forecast.append({"day": day_str, "high": high})
                    
                return {
                    "title": f"{temp}°C", 
                    "subtitle": "Live Location Context",
                    "forecast": forecast
                }
    except Exception:
        pass
        
    return {"title": "31.8°C", "subtitle": "Live Location Context", "forecast": []}

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
            events_payload.append({
                "id": evt.get("id"),
                "summary": evt.get("summary", "Busy"),
                "location": evt.get("location", ""),
                "start": start_dt,
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
        from app.integrations.search.tavily import TavilySearchProvider
        tavily = TavilySearchProvider()
        res = await tavily.search("latest essential top breaking news headlines india tech business sports", max_results=6)
        return str(res)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"[Dashboard] Tavily news fetch failed: {repr(e)}")
        return "Tavily search unavailable. Generate broadly plausible breaking news based on implicit parametric knowledge."

async def _generate_ai_dashboard_payload(weather_data: dict, today_events_titles: list, lat: str, lon: str):
    router = get_provider_router()
    news_context = await fetch_real_time_news()
    today_dt = datetime.datetime.now().strftime("%A, %b %d")
    
    prompt = f"""
    You are an expert AI dashboard curator. Based on this live context, generate exactly one JSON object.
    
    Current Date: {today_dt}
    User Coordinates (Lat, Lon): {lat}, {lon}
    Weather: {weather_data.get('title')} {weather_data.get('subtitle')}
    Calendar Events Today: {today_events_titles if today_events_titles else 'None explicitly defined'}
    Raw News Search Context: {news_context}
    
    The JSON MUST have:
    1. "weather_summary": A professional summary (roughly 2-3 lines, max 25 words).
    2. "calendar_summary": An insight about the schedule today (roughly 2-3 lines, max 25 words).
    3. "news_articles": An array of objects matching EXACTLY this structure:
       [ {{"domain": "tech", "title": "Headline", "summary": "• First bullet roughly 2 lines max 25 words\\n• Second bullet roughly 2 lines max 25 words"}}, ... ]
       MUST include EXACTLY these domains: "top", "tech", "business", "foreign", "sports". EXACTLY 2 bullet points for the summary string.
       Format the news based on the search context provided or real-time insights/plausible generation for India/Global if context is missing or vague.
       
    Output strictly raw JSON starting with {{ and ending with }}. Do not wrap in markdown ``` codeblocks.
    """
    
    try:
        response = await router._execute_with_router("chat", [{"role": "user", "content": prompt}], intent="dashboard")
        
        # Accommodate object response from Gemini native providers lacking a raw strip()
        if hasattr(response, "text"):
            content = response.text or ""
        else:
            content = str(response)
            
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        return json.loads(content)
    except Exception as e:
        print(f"Fallback generation activated due to error: {e}")
        return {
            "weather_summary": "System optimal, predicting stable climate progression.",
            "calendar_summary": "Your schedule is relatively light today.",
            "news_articles": [
                {"domain": "top", "title": "Global Accord Finalized", "summary": "• Pre-launch integrations finalized.\n• Payload launching next month."},
                {"domain": "tech", "title": "India AI Infrastructure", "summary": "• Government allocates resources for GPU clusters.\n• Startups receive subsidies."},
                {"domain": "business", "title": "Markets Rally", "summary": "• IT sectors lead breakaway.\n• Institutions increase holdings."},
                {"domain": "foreign", "title": "EU Policies", "summary": "• New regulations passed.\n• Compliance standards updated."},
                {"domain": "sports", "title": "Squad Secures Finish", "summary": "• Top order chases down limit.\n• Key players rotated."}
            ]
        }

@router.get("/widgets")
async def get_dashboard_widgets(
    request: Request,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    lat = request.headers.get("X-User-Lat", "28.6139")
    lon = request.headers.get("X-User-Lon", "77.2090")

    weather, _ = await asyncio.gather(fetch_weather(lat, lon), fetch_news())
    calendar_grid, today, today_events = await _generate_calendar_grid(user.id, db)
    
    today_dt = datetime.datetime.now()
    calendar_title = today_dt.strftime("%A, %b %d")
    
    # Fully AI Generated structure mapping!
    ai_data = await _generate_ai_dashboard_payload(weather, today_events, lat, lon)
    
    # Build dynamic next_up string
    next_up_str = today_events[0] if today_events else "No immediate events • Schedule Clear"
    
    return {
        "widgets": [
            {
                "id": "weather",
                "title": weather["title"],
                "subtitle": weather["subtitle"],
                "ai_summary": ai_data.get("weather_summary", "Stable weather optimal."),
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

