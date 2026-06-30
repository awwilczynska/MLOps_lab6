import calendar
import requests

from collections import defaultdict, Counter
from datetime import datetime
from typing import Annotated, Optional

from fastmcp import FastMCP
from settings import get_settings

mcp = FastMCP("OpenWeatherMap Server")
settings = get_settings()

API_KEY = settings.openweather_api_key
GEO_URL = "http://api.openweathermap.org/geo/1.0/direct"
# Free-tier 3-hourly forecast (5 days). The 16-day endpoint requires a paid plan.
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"
# Open-Meteo historical archive — free, no API key required.
# Replaces the OpenWeatherMap statistics endpoint which requires a paid plan.
MONTHLY_URL = "https://archive-api.open-meteo.com/v1/archive"


def get_coords(city: str) -> tuple[float, float]:
    """Translate a city name to (lat, lon) using the OpenWeatherMap geocoding API."""
    response = requests.get(GEO_URL, params={"q": city, "limit": 1, "appid": API_KEY})
    response.raise_for_status()
    data = response.json()
    if not data:
        raise ValueError(f"City '{city}' not found.")
    return data[0]["lat"], data[0]["lon"]


@mcp.tool(
    description=(
        "Get a daily weather forecast for a city for up to 5 days. "
        "Returns weather description, high/low temperature (°C), and precipitation for each day. "
        "Use this tool for trip dates within the next 5 days."
    )
)
def get_daily_forecast(
    city: Annotated[str, "The city name, e.g. 'Paris' or 'New York'"],
    days: Annotated[int, "Number of forecast days (1–5), defaults to 5"] = 5,
) -> str:
    try:
        days = max(1, min(days, 5))
        lat, lon = get_coords(city)
        params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"}
        resp = requests.get(FORECAST_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        # Aggregate 3-hourly data points into per-day summaries
        daily: dict = defaultdict(lambda: {"temps": [], "descs": [], "rain": 0.0, "snow": 0.0})
        for item in data["list"]:
            date = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
            daily[date]["temps"].append(item["main"]["temp"])
            daily[date]["descs"].append(item["weather"][0]["description"])
            rain_raw = item.get("rain", {})
            snow_raw = item.get("snow", {})
            daily[date]["rain"] += rain_raw.get("3h", 0) if isinstance(rain_raw, dict) else 0
            daily[date]["snow"] += snow_raw.get("3h", 0) if isinstance(snow_raw, dict) else 0

        lines = [f"Daily forecast for {city} ({days} day(s)):"]
        for date in sorted(daily.keys())[:days]:
            d = daily[date]
            hi = max(d["temps"])
            lo = min(d["temps"])
            desc = Counter(d["descs"]).most_common(1)[0][0].capitalize()
            precip = f", Rain: {d['rain']:.1f} mm" if d["rain"] > 0.1 else ""
            precip += f", Snow: {d['snow']:.1f} mm" if d["snow"] > 0.1 else ""
            lines.append(f"  {date}: {desc}, High: {hi:.1f}°C, Low: {lo:.1f}°C{precip}")

        return "\n".join(lines)

    except Exception as e:
        return f"Error getting daily forecast: {e}"


@mcp.tool(
    description=(
        "Get historical monthly average weather statistics for a city using the Open-Meteo archive. "
        "Returns average temperature (min/mean/max), wind speed, and precipitation for a given month. "
        "Use this tool when the user asks about weather beyond 5 days or for general monthly climate info. "
        "Data is sourced from the previous year's historical records and is free with no API key required."
    )
)
def get_monthly_average(
    city: Annotated[str, "The city name, e.g. 'Rome' or 'Tokyo'"],
    month: Annotated[
        Optional[int],
        "Month number (1–12). Defaults to the current month.",
    ] = None,
) -> str:
    if month is None:
        month = datetime.now().month

    try:
        if not 1 <= month <= 12:
            raise ValueError("Month number must be between 1 and 12.")

        # Use the previous complete year so the full month is always available.
        year = datetime.now().year - 1
        last_day = calendar.monthrange(year, month)[1]
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{last_day:02d}"

        lat, lon = get_coords(city)
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": (
                "temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
                "precipitation_sum,windspeed_10m_max"
            ),
            "timezone": "auto",
        }
        resp = requests.get(MONTHLY_URL, params=params)
        resp.raise_for_status()
        daily = resp.json().get("daily", {})

        def avg(lst: list) -> Optional[float]:
            vals = [v for v in lst if v is not None]
            return sum(vals) / len(vals) if vals else None

        def fmt(val: Optional[float], unit: str) -> str:
            return f"{val:.1f}{unit}" if val is not None else "N/A"

        temp_max_avg = avg(daily.get("temperature_2m_max", []))
        temp_min_avg = avg(daily.get("temperature_2m_min", []))
        temp_mean_avg = avg(daily.get("temperature_2m_mean", []))
        precip_avg = avg(daily.get("precipitation_sum", []))
        wind_avg = avg(daily.get("windspeed_10m_max", []))

        month_name = datetime(2000, month, 1).strftime("%B")
        return "\n".join([
            f"Average weather for {city} in {month_name} (based on {year} historical data):",
            f"  Avg Temperature: {fmt(temp_mean_avg, '°C')} (min {fmt(temp_min_avg, '°C')}, max {fmt(temp_max_avg, '°C')})",
            f"  Avg Wind Speed:  {fmt(wind_avg, ' km/h')}",
            f"  Avg Precipitation: {fmt(precip_avg, ' mm/day')}",
        ])

    except Exception as e:
        return f"Error getting monthly statistics: {e}"


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=settings.openweather_mcp_port,
    )
