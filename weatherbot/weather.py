"""Open-Meteo (bepul, API kalit kerak emas) orqali bugungi ob-havoni olish."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO ob-havo kodlari -> (o'zbekcha tavsif, emoji)
WEATHER_CODES: dict[int, tuple[str, str]] = {
    0: ("Ochiq osmon", "☀️"),
    1: ("Asosan ochiq", "🌤"),
    2: ("Qisman bulutli", "⛅"),
    3: ("Bulutli", "☁️"),
    45: ("Tuman", "🌫"),
    48: ("Qirovli tuman", "🌫"),
    51: ("Yengil shivalama", "🌦"),
    53: ("Shivalama yomg'ir", "🌦"),
    55: ("Kuchli shivalama", "🌧"),
    56: ("Muzlovchi shivalama", "🌧"),
    57: ("Kuchli muzlovchi shivalama", "🌧"),
    61: ("Yengil yomg'ir", "🌦"),
    63: ("Yomg'ir", "🌧"),
    65: ("Kuchli yomg'ir", "🌧"),
    66: ("Muzlovchi yomg'ir", "🌧"),
    67: ("Kuchli muzlovchi yomg'ir", "🌧"),
    71: ("Yengil qor", "🌨"),
    73: ("Qor", "🌨"),
    75: ("Kuchli qor", "❄️"),
    77: ("Qor donalari", "🌨"),
    80: ("Yengil jala", "🌦"),
    81: ("Jala", "🌧"),
    82: ("Kuchli jala", "⛈"),
    85: ("Qor aralash jala", "🌨"),
    86: ("Kuchli qor jala", "❄️"),
    95: ("Momaqaldiroq", "⛈"),
    96: ("Do'l bilan momaqaldiroq", "⛈"),
    99: ("Kuchli do'l bilan momaqaldiroq", "⛈"),
}

SNOW_CODES = {71, 73, 75, 77, 85, 86}
RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}


@dataclass
class DailyForecast:
    timezone: str
    weather_code: int
    temp_min: float
    temp_max: float
    feels_min: float
    feels_max: float
    precip_probability: int  # %
    precip_sum: float  # mm
    wind_max: float  # km/soat
    uv_index: float
    morning_temp: float  # soat 08:00 dagi harorat

    @property
    def description(self) -> str:
        return WEATHER_CODES.get(self.weather_code, ("Noma'lum", "🌡"))[0]

    @property
    def emoji(self) -> str:
        return WEATHER_CODES.get(self.weather_code, ("Noma'lum", "🌡"))[1]

    @property
    def is_snowy(self) -> bool:
        return self.weather_code in SNOW_CODES

    @property
    def is_rainy(self) -> bool:
        return self.weather_code in RAIN_CODES or self.precip_probability >= 50


def parse_forecast(data: dict) -> DailyForecast:
    daily = data["daily"]
    hourly = data.get("hourly", {})
    temps = hourly.get("temperature_2m") or []
    # hourly[0] = bugun 00:00 (mahalliy vaqt), shuning uchun 8-indeks = 08:00
    morning = temps[8] if len(temps) > 8 else daily["temperature_2m_min"][0]
    return DailyForecast(
        timezone=data.get("timezone", "UTC"),
        weather_code=int(daily["weather_code"][0]),
        temp_min=daily["temperature_2m_min"][0],
        temp_max=daily["temperature_2m_max"][0],
        feels_min=daily["apparent_temperature_min"][0],
        feels_max=daily["apparent_temperature_max"][0],
        precip_probability=int(daily["precipitation_probability_max"][0] or 0),
        precip_sum=daily["precipitation_sum"][0] or 0.0,
        wind_max=daily["wind_speed_10m_max"][0] or 0.0,
        uv_index=daily["uv_index_max"][0] or 0.0,
        morning_temp=morning,
    )


async def fetch_today(lat: float, lon: float) -> DailyForecast:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join(
            [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "apparent_temperature_min",
                "precipitation_probability_max",
                "precipitation_sum",
                "wind_speed_10m_max",
                "uv_index_max",
            ]
        ),
        "hourly": "temperature_2m",
        "timezone": "auto",
        "forecast_days": 1,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(FORECAST_URL, params=params)
        resp.raise_for_status()
        return parse_forecast(resp.json())


async def fetch_timezone(lat: float, lon: float) -> str:
    """Joylashuv bo'yicha vaqt zonasini aniqlash (masalan, Asia/Tashkent)."""
    params = {"latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 1}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(FORECAST_URL, params=params)
        resp.raise_for_status()
        return resp.json().get("timezone", "UTC")
