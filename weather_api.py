import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

DEFAULT_LOCATION = "Multan, Pakistan"


def get_weather(location: str):
    location = (location or "").strip()
    if not location:
        location = DEFAULT_LOCATION

    geo = requests.get(
        GEOCODE_URL,
        params={
            "name": location,
            "count": 5,
            "language": "en",
            "format": "json",
        },
        timeout=20,
    )
    geo.raise_for_status()
    geo_data = geo.json()

    results = geo_data.get("results") or []
    if not results:
        return False, f"Couldn't find location: {location}", None

    # Prefer Pakistan if user asked for Multan or if Pakistan appears in the query
    chosen = results[0]
    query_lower = location.lower()

    for place in results:
        name = (place.get("name") or "").lower()
        country = (place.get("country") or "").lower()
        admin1 = (place.get("admin1") or "").lower()

        if "multan" in query_lower and name == "multan" and country == "pakistan":
            chosen = place
            break

        if "pakistan" in query_lower and country == "pakistan":
            chosen = place
            break

    lat = chosen["latitude"]
    lon = chosen["longitude"]
    name = chosen.get("name", "")
    country = chosen.get("country", "")
    admin1 = chosen.get("admin1", "")
    timezone = chosen.get("timezone", "auto")

    weather = requests.get(
        WEATHER_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "forecast_days": 3,
            "timezone": timezone,
        },
        timeout=20,
    )
    weather.raise_for_status()
    data = weather.json()

    return True, "", {
        "resolved_query": location,
        "location": f"{name}, {admin1}, {country}".strip(", ").replace(", ,", ","),
        "latitude": lat,
        "longitude": lon,
        "timezone": data.get("timezone", timezone),
        "data": data,
    }


def weather_code_to_text(code):
    mapping = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return mapping.get(code, f"Unknown ({code})")


def format_weather_result(result: dict) -> str:
    current = result["data"].get("current", {})
    daily = result["data"].get("daily", {})
    units = result["data"].get("current_units", {})

    temp_unit = units.get("temperature_2m", "°C")
    wind_unit = units.get("wind_speed_10m", "km/h")
    humidity_unit = units.get("relative_humidity_2m", "%")

    lines = [
        f"Resolved location: {result['location']}",
        f"Timezone: {result.get('timezone', 'Unknown')}",
        f"Coordinates: {result['latitude']}, {result['longitude']}",
        "",
        "Current weather:",
        f"- Temperature: {current.get('temperature_2m')} {temp_unit}",
        f"- Feels like: {current.get('apparent_temperature')} {temp_unit}",
        f"- Humidity: {current.get('relative_humidity_2m')} {humidity_unit}",
        f"- Wind speed: {current.get('wind_speed_10m')} {wind_unit}",
        f"- Condition: {weather_code_to_text(current.get('weather_code'))}",
    ]

    dates = daily.get("time", [])
    highs = daily.get("temperature_2m_max", [])
    lows = daily.get("temperature_2m_min", [])
    rain = daily.get("precipitation_probability_max", [])
    codes = daily.get("weather_code", [])

    if dates:
        lines.append("")
        lines.append("3-day forecast:")
        for d, hi, lo, pr, code in zip(dates, highs, lows, rain, codes):
            lines.append(
                f"- {d}: {weather_code_to_text(code)}, high {hi}{temp_unit}, low {lo}{temp_unit}, rain chance {pr}%"
            )

    return "\n".join(lines)