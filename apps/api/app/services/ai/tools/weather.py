import json
import logging
import datetime
import traceback
import httpx

from app.services.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

class WeatherTool(BaseTool):
    def __init__(self):
        pass

    @property
    def name(self) -> str:
        return "get_weather"

    @property
    def description(self) -> str:
        return "Get the current weather and 7-day forecast for a specific location. Use this tool whenever the user asks for the weather, temperature, or forecast. If the user does not specify a location, you MUST pass 'auto-detect' as the location parameter and the backend will automatically geo-locate them via IP."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city or location name to get the weather for. Examples: 'Delhi', 'New York', 'Paris'. If the user asks for the weather 'here' or doesn't specify a location, pass 'auto'."
                }
            },
            "required": []
        }

    def _wmo_to_condition(self, wmo: int) -> str:
        if wmo in [0, 1]: return "Clear"
        if wmo in [2]: return "Partly Cloudy"
        if wmo in [3]: return "Overcast"
        if wmo in [45, 48]: return "Fog"
        if wmo in [51, 53, 55, 56, 57]: return "Drizzle"
        if wmo in [61, 63, 65, 66, 67, 80, 81, 82]: return "Rain"
        if wmo in [71, 73, 75, 77, 85, 86]: return "Snow"
        if wmo >= 95: return "Storm"
        return "Cloudy"

    async def execute(self, execution_context: dict, **kwargs) -> str:
        location = kwargs.get("location")
        if not location:
            location = "auto"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                if location.lower() in ["auto", "auto-detect", "here", "current_user_city", "current location", "result_from_get_user_location"]:
                    ctx_lat = execution_context.get("lat")
                    ctx_lon = execution_context.get("lon")
                    
                    if ctx_lat is not None and ctx_lon is not None:
                        lat = ctx_lat
                        lon = ctx_lon
                        full_name = "Current Location (GPS)"
                    else:
                        # Fallback to IP-based geolocation
                        ip_resp = await client.get("http://ip-api.com/json/")
                        if ip_resp.status_code != 200:
                            return json.dumps({"error": "Failed to auto-detect location based on IP"})
                        ip_data = ip_resp.json()
                        lat = ip_data.get("lat")
                        lon = ip_data.get("lon")
                        city = ip_data.get("city", "Auto-detected Location")
                        country = ip_data.get("country", "")
                        full_name = f"{city}, {country}" if country else city
                else:
                    # 1. Geocode location to lat/lon
                    geo_resp = await client.get(f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&format=json")
                    if geo_resp.status_code != 200:
                        return json.dumps({"error": "Failed to geocode location"})
                    
                    geo_data = geo_resp.json()
                    if not geo_data.get("results"):
                        return json.dumps({"error": f"Could not find coordinates for location: {location}"})
                        
                    lat = geo_data["results"][0]["latitude"]
                    lon = geo_data["results"][0]["longitude"]
                    city = geo_data["results"][0].get("name", location)
                    country = geo_data["results"][0].get("country", "")
                    full_name = f"{city}, {country}" if country else city
                
                # 2. Get Weather
                for attempt in range(3):
                    try:
                        resp = await client.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&hourly=temperature_2m,precipitation&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=auto")
                        if resp.status_code == 200:
                            break
                        elif attempt == 2:
                            return json.dumps({"error": "Failed to fetch weather data"})
                    except httpx.ConnectError:
                        if attempt == 2:
                            raise
                        import asyncio
                        await asyncio.sleep(1)
                
                data = resp.json()
                
                # Format current weather
                current = data.get("current", {})
                current_wmo = current.get("weather_code", 3)
                
                # Format forecast
                daily = data.get("daily", {})
                daily_times = daily.get("time", [])
                daily_max = daily.get("temperature_2m_max", [])
                daily_min = daily.get("temperature_2m_min", [])
                daily_codes = daily.get("weather_code", [])
                
                hourly = data.get("hourly", {})
                hourly_times = hourly.get("time", [])
                hourly_temps = hourly.get("temperature_2m", [])
                hourly_precip = hourly.get("precipitation", [])

                forecast = []
                for idx in range(min(7, len(daily_times))):
                    dt = datetime.datetime.fromisoformat(daily_times[idx])
                    day_str = dt.strftime("%a")
                    
                    day_hourly = []
                    for i in range(8):
                        h_idx = (idx * 24) + (i * 3)
                        if h_idx < len(hourly_times) and h_idx < len(hourly_temps):
                            dt_h = datetime.datetime.fromisoformat(hourly_times[h_idx])
                            day_hourly.append({
                                "time": dt_h.strftime("%I%p").lstrip("0").lower(),
                                "temp": hourly_temps[h_idx],
                                "precip": hourly_precip[h_idx] if h_idx < len(hourly_precip) else 0.0
                            })
                            
                    forecast.append({
                        "date": daily_times[idx],
                        "day": day_str,
                        "high": daily_max[idx] if daily_max and idx < len(daily_max) else None,
                        "low": daily_min[idx] if daily_min and idx < len(daily_min) else None,
                        "condition": self._wmo_to_condition(daily_codes[idx]) if daily_codes and idx < len(daily_codes) else "Unknown",
                        "hourly": day_hourly
                    })
                
                result = {
                    "location": full_name,
                    "coordinates": {"lat": lat, "lon": lon},
                    "current": {
                        "temperature": f"{current.get('temperature_2m')}°C",
                        "feels_like": f"{current.get('apparent_temperature')}°C",
                        "humidity": f"{current.get('relative_humidity_2m')}%",
                        "wind_speed": f"{current.get('wind_speed_10m')} km/h",
                        "condition": self._wmo_to_condition(current_wmo)
                    },
                    "forecast_7_days": forecast
                }
                
                return json.dumps(result)

        except Exception as e:
            err_msg = traceback.format_exc()
            logger.error(f"[WeatherTool] Error: {err_msg}")
            return json.dumps({"error": f"Failed to execute weather tool: {str(e)}\n{err_msg}"})
