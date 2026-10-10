from weatherbot.clothing import build_message, clothing_advice
from weatherbot.weather import parse_forecast


def sample(**overrides):
    daily = {
        "weather_code": [3],
        "temperature_2m_max": [12.0],
        "temperature_2m_min": [4.0],
        "apparent_temperature_max": [10.0],
        "apparent_temperature_min": [1.0],
        "precipitation_probability_max": [10],
        "precipitation_sum": [0.0],
        "wind_speed_10m_max": [12.0],
        "uv_index_max": [2.0],
    }
    for k, v in overrides.items():
        daily[k] = [v]
    return {
        "timezone": "Asia/Tashkent",
        "daily": daily,
        "hourly": {"temperature_2m": [3.0] * 8 + [5.0] + [8.0] * 15},
    }


def text(f):
    return " ".join(clothing_advice(f))


def test_parse_morning_temp():
    f = parse_forecast(sample())
    assert f.morning_temp == 5.0
    assert f.timezone == "Asia/Tashkent"
    assert f.description == "Bulutli"


def test_cold_day_needs_winter_gear():
    f = parse_forecast(sample(apparent_temperature_min=-15.0, weather_code=73))
    t = text(f)
    assert "qishki" in t and "qo'lqop" in t
    assert "Qor yog'adi" in t


def test_hot_sunny_day():
    f = parse_forecast(
        sample(
            weather_code=0,
            temperature_2m_min=26.0,
            temperature_2m_max=38.0,
            apparent_temperature_min=27.0,
            apparent_temperature_max=40.0,
            uv_index_max=9.0,
        )
    )
    f.morning_temp = 28.0
    t = text(f)
    assert "Shorti" in t
    assert "UV" in t
    assert "suv iching" in t


def test_rain_and_wind():
    f = parse_forecast(
        sample(precipitation_probability_max=80, precipitation_sum=8.0, wind_speed_10m_max=40.0)
    )
    t = text(f)
    assert "soyabon" in t
    assert "Suv o'tkazmaydigan poyabzal" in t
    assert "Kuchli shamol" in t


def test_large_temperature_swing_suggests_layers():
    f = parse_forecast(sample(temperature_2m_min=5.0, temperature_2m_max=22.0))
    assert "qatlamli" in text(f)


def test_message_contains_sections():
    msg = build_message(parse_forecast(sample()), "Ali")
    assert msg.startswith("Xayrli tong, Ali!")
    assert "Bugun nima kiyish kerak" in msg
