import random
import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

def _generate_rule_based_weather_summary(weather_data: dict) -> str:
    condition = weather_data.get('condition', '').lower()
    title = weather_data.get('title', '') # temperature like "32°C"
    subtitle = weather_data.get('subtitle', '').lower() # e.g. "feels like 36°C"
    forecast = weather_data.get('forecast', [])
    wind_str = weather_data.get('wind_speed', '')
    humidity_str = weather_data.get('humidity', '')
    
    temp_val = 25
    feels_like_val = None
    wind_val = 0
    humidity_val = 50
    
    try:
        if "°C" in title:
            temp_val = int(title.replace("°C", "").strip())
        if "feels like" in subtitle and "°c" in subtitle:
            feels_like_val = int(subtitle.replace("feels like", "").replace("°c", "").strip())
        if "km/h" in wind_str:
            wind_val = float(wind_str.replace("km/h", "").strip())
        if "%" in humidity_str:
            humidity_val = int(humidity_str.replace("%", "").strip())
    except:
        pass

    if feels_like_val is not None and (feels_like_val - temp_val) >= 4 and feels_like_val >= 35:
        opts = [
            f"It's {temp_val}°C but high humidity makes it feel like {feels_like_val}°C. Stay cool!",
            f"Oppressive heat out there. It feels significantly hotter than {temp_val}°C.",
            "High humidity alert. Avoid strenuous outdoor activities.",
            f"The air is thick today. True temp is {temp_val}°C but it feels like {feels_like_val}°C.",
            "Sticky and humid conditions outside. Hydration is critical today.",
            f"Don't let the {temp_val}°C fool you—it feels like a sweltering {feels_like_val}°C.",
            "Muggy conditions detected. Try to stay in air-conditioned environments.",
            "Tropical-level humidity today. Take it easy if you're stepping out.",
            "The heat index is soaring. Protect yourself from the harsh conditions.",
            "Sweat won't evaporate easily today. Keep a cool beverage close by!"
        ]
        return random.choice(opts)
        
    if feels_like_val is not None and (temp_val - feels_like_val) >= 4 and feels_like_val <= 5:
        opts = [
            f"Wind chill warning! It's {temp_val}°C but feels like a freezing {feels_like_val}°C.",
            f"Dress in heavy layers. The wind makes it feel like {feels_like_val}°C outside.",
            "Biting cold wind today. Keep exposed skin covered!",
            f"The thermometer says {temp_val}°C, but the wind bites like {feels_like_val}°C.",
            "Harsh wind chill factor. A thick coat and scarf are highly recommended.",
            "Bracing cold outside due to the wind. Stay indoors if possible.",
            f"Don't trust the raw temperature. It feels bone-chillingly cold at {feels_like_val}°C.",
            "Gusty winds are stripping away the heat. Bundle up tight!",
            "Icy breeze detected. Make sure to wear gloves and a warm hat.",
            "The ambient temperature drops significantly in the wind. Stay warm."
        ]
        return random.choice(opts)

    # Condition-based rules
    if wind_val >= 50 or "storm" in condition or "thunder" in condition or "lightning" in condition:
        opts = [
            "Storm advisory: Please stay indoors and stay safe.",
            "Severe stormy conditions detected. Avoid unnecessary travel.",
            "Thunderstorms in the area. Unplug sensitive electronics.",
            "Squally weather ahead. Secure outdoor items!",
            "Lightning strikes expected. Seek shelter immediately.",
            "Heavy storm cells passing through. Keep away from windows.",
            "Tempestuous weather outside. A good day to stay cozied up indoors.",
            "Dark skies and thunder overhead. Travel with extreme caution.",
            "Potential for severe weather. Keep emergency supplies handy.",
            "Mother Nature is putting on a show. Watch the storm safely from inside.",
            f"Dangerous {wind_val}km/h winds out there! Take immediate shelter."
        ]
    elif humidity_val >= 90 and temp_val >= 25:
        opts = [
            f"It's incredibly humid ({humidity_val}%). The air feels like soup today.",
            f"Intense tropical humidity outside at {humidity_val}%.",
            f"Extremely muggy today with {humidity_val}% humidity. Stay hydrated."
        ]
    elif "rain" in condition or "drizzle" in condition or "shower" in condition:
        opts = [
            "It's raining outside. Don't forget to carry an umbrella!",
            "Rainy day ahead. Perfect weather for a hot cup of tea.",
            "Showers expected. Drive safely if you're heading out.",
            "Wet conditions today. Waterproof footwear is recommended.",
            "Drizzly and damp. A raincoat will be your best friend today.",
            "Steady rainfall detected. Allow extra time for your commute.",
            "Puddles are forming. Watch your step when walking outside.",
            "A gloomy, rainy day. Perfect ambiance for reading a book.",
            "Light showers rolling through. Keep your umbrella close.",
            "Rain gear is essential today. Don't get caught in the downpour!"
        ]
    elif "snow" in condition or "blizzard" in condition:
        opts = [
            "Snowy conditions today. Bundle up and stay warm!",
            "It's snowing! Keep your winter gear ready if stepping out.",
            "Freezing temperatures with snow. Stay cozy indoors.",
            "Watch out for icy sidewalks and roads today.",
            "Winter wonderland outside! But roads may be treacherous.",
            "Heavy snowfall expected. Consider working from home if possible.",
            "Flakes are falling. Time for hot cocoa and warm blankets.",
            "Blizzard conditions possible. Do not travel unless absolutely necessary.",
            "Snow accumulation likely. Keep your shovel and salt handy.",
            "Beautiful but freezing snowy weather. Dress in multiple warm layers."
        ]
    elif "fog" in condition or "mist" in condition or "haze" in condition:
        opts = [
            "Foggy conditions today. Drive carefully with headlights on.",
            "Low visibility due to fog. Take your time if commuting.",
            "Hazy skies. Visibility might be reduced on the roads.",
            "Thick mist rolling in. Be extra vigilant while driving.",
            "Pea-soup fog outside. Slow down and maintain a safe distance.",
            "Misty morning ahead. The air feels heavy and damp.",
            "Atmospheric haze detected. Keep your low-beam headlights on.",
            "Fog banks could obscure your vision. Travel safely.",
            "A mysterious foggy day. Visibility is significantly impaired.",
            "Heavy fog warning. Allow plenty of extra travel time."
        ]
    elif wind_val >= 30 or "wind" in condition or "breezy" in condition:
        opts = [
            "It's quite windy today. Hold onto your hats!",
            "Strong gusts expected. Be careful if cycling or riding a bike.",
            "Blustery conditions outside. Watch out for flying debris.",
            "High winds in the forecast. Secure any loose outdoor furniture.",
            "A brisk and breezy day. Windbreakers are highly recommended.",
            "Gusty weather. It might be harder to walk against the wind today.",
            "Gale-force winds possible. Stay clear of large trees.",
            "The wind is howling today. Keep your windows shut tight.",
            "Very breezy out there. A great day to fly a kite, perhaps?",
            f"Turbulent air currents at {wind_val}km/h. Be mindful of sudden strong gusts."
        ]
    # Temperature-based rules
    elif temp_val >= 40:
        opts = [
            "Dangerous heatwave! Do not go outside unless strictly necessary.",
            "Severe heat alert! Drink lots of water and stay in the AC.",
            "Life-threatening temperatures today. Seek cooling centers if needed.",
            "Extreme thermal warning. Physical exertion outside is dangerous.",
            "Record-breaking heat. Protect yourself from heat exhaustion.",
            "Scorching 40+ degree weather. Keep pets indoors and hydrated.",
            "Blistering heatwave. Blackout curtains and fans are your allies.",
            "The sun is merciless today. Hydration is an absolute priority.",
            "Unbearable heat levels. Check on elderly neighbors if possible.",
            "Thermal crisis conditions. Avoid all sun exposure during peak hours."
        ]
    elif temp_val >= 35:
        opts = [
            "Extreme heat alert! Stay hydrated and avoid direct sunlight.",
            "Scorching temperatures today. Keep cool and drink plenty of water.",
            "Very hot outside. Best to stay in air-conditioned spaces.",
            "Summer is peaking. Wear light, breathable clothing today.",
            "Sweltering conditions. Don't forget your sunscreen and sunglasses.",
            "The heat is intense. Take frequent breaks if working outdoors.",
            "High temperature warning. Seek shade whenever possible.",
            "A truly hot day. Ice-cold beverages are highly recommended.",
            "Baking hot outside. Limit your time in the direct sun.",
            "Heat advisory in effect. Keep your cool and stay hydrated."
        ]
    elif temp_val <= 0:
        opts = [
            "Freezing temperatures! Ice may form on roads and walkways.",
            "It's below zero outside. Frostbite can happen quickly, bundle up.",
            "Sub-zero weather. Ensure your pipes are insulated and stay warm.",
            "Bitterly cold conditions. Heavy winter coats are mandatory.",
            "Below freezing point. Watch your step for black ice.",
            "Deep freeze in effect. Keep your home heating running steadily.",
            "Bone-chilling cold. Limit exposure to the outdoors.",
            "Frigid temperatures. Don't forget your thermal undergarments.",
            "A truly freezing day. Perfect for staying under a heavy duvet.",
            "Extreme cold warning. Protect your extremities with gloves and thick socks."
        ]
    elif temp_val <= 10:
        opts = [
            "It's quite cold outside. Make sure to wear warm layers.",
            "Chilly weather today. A hot beverage would be perfect.",
            "Brisk and cold. Keep yourself bundled up.",
            "A crisp, cold day. A jacket and sweater are required.",
            "Nippy weather. Don't leave the house without a warm coat.",
            "Cool temperatures today. Great weather for a brisk walk if bundled.",
            "Sweater weather is here. Stay cozy and comfortable.",
            "A cold snap is present. Keep your hands warm.",
            "Chilly air detected. Thermal wear might be a good idea.",
            "It's pretty cold out. Keep the thermostat at a comfortable level."
        ]
    elif temp_val >= 20 and temp_val <= 28 and "clear" in condition:
        opts = [
            "Absolutely perfect weather today! Get outside if you can.",
            "Ideal temperatures and clear skies. A beautiful day!",
            "Gorgeous weather right now. Don't waste it indoors!",
            "Picture-perfect conditions. Great day for a picnic or hike.",
            "Flawless weather. Enjoy the sunshine and comfortable breeze.",
            "A spectacular day outside. The climate couldn't be better.",
            "Sublime weather conditions. It's a great day to be alive.",
            "Optimal temperatures and bright skies. Go enjoy the day!",
            "Stunning weather today. Open the windows and let the fresh air in.",
            "A 10/10 weather day. Perfect for literally any outdoor activity."
        ]
    else:
        if "cloud" in condition or "overcast" in condition:
            opts = [
                "Pleasant cloudy weather today. Great day for a walk.",
                "Overcast skies. Comfortable temperatures for outdoor activities.",
                "Sun is hiding today. Expect cool, shaded conditions.",
                "A grey day outside, but the temperature is agreeable.",
                "Cloud cover is providing nice shade today.",
                "Soft, diffused light from the overcast skies. A calm day.",
                "Mostly cloudy. A quiet and subdued atmospheric vibe.",
                "The clouds are rolling in. Enjoy the mild weather.",
                "Overcast and peaceful. A good day for focused work.",
                "Cloudy skies overhead. It's cool and very comfortable."
            ]
        else:
            opts = [
                "Clear skies and beautiful weather today. Make the most of it!",
                "Perfect conditions outside. Have a wonderful day ahead.",
                "Stable and pleasant weather optimal for your plans.",
                "A fine day with good weather. Enjoy your activities.",
                "Nothing unusual in the forecast. Standard pleasant weather.",
                "A standard, comfortable day outside. No severe conditions.",
                "Nice and calm weather today. Proceed with your usual schedule.",
                "The climate is cooperating beautifully today.",
                "Fair weather conditions detected. All looks good outside.",
                "A lovely, unremarkable day weather-wise. Enjoy the stability."
            ]
            
    # Add forecast insight if available
    base_msg = random.choice(opts)
    if forecast and len(forecast) > 0:
        tomorrow = forecast[0]
        if tomorrow.get('high') != "--" and isinstance(tomorrow.get('high'), int):
            if tomorrow['high'] > temp_val + 5:
                base_msg += " Heads up: It will be significantly hotter tomorrow."
            elif tomorrow['high'] < temp_val - 5:
                base_msg += " Brace yourself: A cold front is moving in tomorrow."
                
    # Time of day awareness
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        greetings = ["Good morning!", "Rise and shine!", "Morning!"]
    elif 12 <= hour < 17:
        greetings = ["Good afternoon!", "Afternoon!", "Hope your day is going well."]
    elif 17 <= hour < 21:
        greetings = ["Good evening!", "Evening!", "Winding down the day?"]
    else:
        greetings = ["Good night!", "Late night?", "It's getting late!"]
        
    prefix = random.choice(greetings)
    return f"{prefix} {base_msg}"

def _generate_rule_based_calendar_summary(today_events_titles: list) -> str:
    # Use the events directly fetched from Google Calendar for all holiday context
    count = len(today_events_titles)
    
    # Identify if one of the events is likely a holiday/festival or birthday
    special_event = None
    for title in today_events_titles:
        lower_title = title.lower()
        if "holiday" in lower_title or "day" in lower_title or "eve" in lower_title or "diwali" in lower_title or "christmas" in lower_title:
            special_event = title.split(" at ")[0] # Clean up time suffix if present
            break
        if "birthday" in lower_title or "bday" in lower_title:
            special_event = title.split(" at ")[0]
            break
            
    if count == 0:
        opts = [
            "Your schedule is completely clear. Enjoy the quiet day!",
            "No scheduled events today. Take some time to relax or plan ahead.",
            "A free day awaits you. Perfect time to focus on personal tasks.",
            "Your calendar is a blank slate today. Make it a great one!",
            "Zero meetings on the agenda today. Deep work time!",
            "Nothing pressing on the calendar. A perfect day to catch up.",
            "You have the whole day to yourself. No events scheduled.",
            "A rare empty schedule! Enjoy the uninterrupted freedom.",
            "Your day is wide open. Do whatever brings you joy today.",
            "No alerts will bother you today. Your calendar is blissfully clear."
        ]
        base = random.choice(opts)
    else:
        next_event = today_events_titles[0].split(" at ")[0]
        
        # If the special event is the only event, format nicely
        if count == 1 and special_event == next_event:
            opts = [
                f"Just one highlight today: {next_event}. Have a wonderful time!",
                f"Today is {next_event}! Enjoy the celebration.",
                f"Your only event today is {next_event}.",
                f"It's {next_event} today! Make it a memorable one.",
                f"All focus is on {next_event} today. Have fun!",
                f"You're celebrating {next_event} today. Enjoy your special day.",
                f"Only {next_event} on the radar today. Have a blast!",
                f"Today marks {next_event}. Take time to enjoy it.",
                f"Your schedule is dedicated solely to {next_event} today.",
                f"Happy {next_event} day! Wishing you the very best."
            ]
            return random.choice(opts)
            
        opts = [
            f"You have {count} events scheduled today. Next up: {next_event}.",
            f"Busy day! {count} things on the agenda, starting with {next_event}.",
            f"Your calendar shows {count} events. Don't forget about {next_event}.",
            f"First up on your {count}-event schedule is {next_event}.",
            f"It's a full day with {count} events. Next is {next_event}.",
            f"Stay focused! You have {count} events, beginning with {next_event}.",
            f"Your itinerary has {count} items today. Up next: {next_event}.",
            f"{count} tasks await you today. {next_event} is your next priority.",
            f"Pace yourself today. You have {count} events, starting with {next_event}.",
            f"A packed schedule of {count} events today. Next up: {next_event}."
        ]
        base = random.choice(opts)
        
    if special_event:
        return f"Happy {special_event}! 🎉 {base}"
    return base

import difflib
import re

def _extract_headline(title: str, content: str) -> str:
    # First, clean the title
    delimiters = [" - ", " | ", " : ", "—"]
    for delim in delimiters:
        if delim in title:
            parts = title.split(delim)
            title = max(parts, key=len).strip()
            
    # Generic title detection
    lower_title = title.lower()
    generic_phrases = ["news", "latest", "update", "video", "breaking", "home", "homepage"]
    words = lower_title.split()
    
    # If the title is very short, or consists mostly of generic buzzwords, reject it
    is_generic = False
    if len(title) < 15:
        is_generic = True
    else:
        generic_count = sum(1 for w in words if any(g in w for g in generic_phrases))
        if len(words) > 0 and generic_count / len(words) > 0.5:
            is_generic = True
            
    if is_generic and content:
        # Fallback to the first meaningful sentence of the content
        clean_content = re.sub(r'#+\s*', '', content) # strip markdown headers
        clean_content = clean_content.replace('\n', ' ')
        sents = [s.strip() for s in clean_content.split(". ") if s.strip()]
        for s in sents:
            if 20 < len(s) < 120: # Ensure it's a headline-sized sentence
                return s + ("." if not s.endswith(".") else "")
                
    if is_generic:
        return "" # Completely reject if it's generic and we couldn't find a fallback
        
    return title

_news_cache: dict[str, tuple[datetime.datetime, list[dict]]] = {}
_CACHE_TTL = datetime.timedelta(hours=4)

async def _fetch_curated_news_domains(location_name: str) -> list[dict]:
    from app.services.ai.tools.news_search import _tavily_search, TRUSTED_SOURCES_INDIA, TRUSTED_SOURCES_GLOBAL
    
    in_india = any(city in location_name.lower() for city in ["delhi", "mumbai", "bangalore", "chennai", "kolkata", "india", "pune", "hyderabad", "noida", "gurugram", "jaipur", "lucknow"])
    
    local_sources = TRUSTED_SOURCES_INDIA if in_india else TRUSTED_SOURCES_GLOBAL
    global_sources = TRUSTED_SOURCES_GLOBAL
    
    city = location_name.split(",")[0] if "," in location_name else location_name
    country = "India" if in_india else "Global"
    
    cache_key = f"{city}_{country}"
    now = datetime.datetime.now()
    if cache_key in _news_cache:
        cached_time, cached_articles = _news_cache[cache_key]
        if now - cached_time < _CACHE_TTL:
            logger.info(f"[Dashboard] Serving news from cache for {cache_key}")
            return cached_articles
    
    queries = [
        {"domain": "top", "q": f"Top breaking news {country}", "sources": local_sources},
        {"domain": "tech", "q": "Latest technology news", "sources": global_sources},
        {"domain": "local", "q": f"Top local news {city}", "sources": local_sources},
        {"domain": "business", "q": f"Top business and finance news {country}", "sources": local_sources},
        {"domain": "foreign", "q": "Top breaking global world news", "sources": global_sources},
        {"domain": "sports", "q": f"Top sports news {country}", "sources": local_sources},
    ]
    
    seen_headlines = []
    
    async def fetch_domain(q_info):
        try:
            results, _ = await _tavily_search(
                query=q_info["q"],
                include_domains=q_info["sources"],
                max_results=10, # Fetch extra to account for deduplication
                days=2
            )
            
            headlines = []
            for r in results:
                raw_title = r.get("title", "")
                raw_content = r.get("content", "")
                extracted = _extract_headline(raw_title, raw_content)
                
                if not extracted:
                    continue
                    
                # Semantic deduplication
                is_duplicate = False
                for seen in seen_headlines:
                    ratio = difflib.SequenceMatcher(None, extracted.lower(), seen.lower()).ratio()
                    if ratio > 0.65:
                        is_duplicate = True
                        break
                        
                if not is_duplicate:
                    headlines.append(f"• {extracted}")
                    seen_headlines.append(extracted)
                    
                if len(headlines) == 3:
                    break
                    
            domain_titles = {
                "top": "Top Headlines",
                "tech": "Technology Updates",
                "local": "Local News",
                "business": "Business & Finance",
                "foreign": "Global News",
                "sports": "Sports Highlights"
            }
            
            display_title = domain_titles.get(q_info["domain"], "News Updates")
            summary_text = "\n\n".join(headlines) if headlines else "No recent updates available."
            
            return [{
                "domain": q_info["domain"],
                "title": display_title,
                "summary": summary_text
            }]
        except Exception as e:
            logger.warning(f"[Dashboard] Failed to fetch {q_info['domain']} news: {e}")
            return []
            
    # Fetch sequentially or concurrently?
    # Because we rely on a shared seen_headlines list, and async boundaries don't interrupt synchronous loops,
    # running them with gather is actually thread-safe in Python's asyncio since there's no await during the deduplication loop.
    tasks = [fetch_domain(q) for q in queries]
    results_lists = await asyncio.gather(*tasks)
    
    all_articles = []
    for rlist in results_lists:
        all_articles.extend(rlist)
        
    # Store in cache
    _news_cache[cache_key] = (now, all_articles)
        
    return all_articles
