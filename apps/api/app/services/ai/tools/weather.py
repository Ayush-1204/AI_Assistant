import json
import logging
import httpx
import datetime

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
        return "Get the current weather and 5-day forecast for a specific location. Use this tool whenever the user asks for the weather, temperature, or forecast."

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
            "required": ["location"]
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
            return json.dumps({"error": "Missing 'location' parameter"})

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                if location.lower() == "auto":
                    # Use IP-based geolocation
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
                resp = await client.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=auto")
                if resp.status_code != 200:
                    return json.dumps({"error": "Failed to fetch weather data"})
                    
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
                
                forecast = []
                for idx in range(min(5, len(daily_times))):
                    forecast.append({
                        "date": daily_times[idx],
                        "high": daily_max[idx] if daily_max and idx < len(daily_max) else None,
                        "low": daily_min[idx] if daily_min and idx < len(daily_min) else None,
                        "condition": self._wmo_to_condition(daily_codes[idx]) if daily_codes and idx < len(daily_codes) else "Unknown"
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
                    "forecast_5_days": forecast
                }
                
                return json.dumps(result)

        except Exception as e:
            logger.error(f"[WeatherTool] Error: {e}")
            return json.dumps({"error": f"Failed to execute weather tool: {str(e)}"})
