"""Ob-havoga qarab kiyim tavsiyasi va ertalabki xabar matni."""

from __future__ import annotations

from .weather import DailyForecast


def clothing_advice(f: DailyForecast) -> list[str]:
    """Kunning eng sovuq "his qilinadigan" haroratiga qarab kiyim tanlaydi."""
    t = min(f.feels_min, f.morning_temp)
    tips: list[str] = []

    if t <= -10:
        tips += [
            "🧥 Qalin qishki kurtka yoki po'stin",
            "🧶 Termo ichki kiyim + jun sviter",
            "🧣 Sharf, 🧤 qo'lqop va issiq shapka — albatta",
            "🥾 Issiq qishki botinka va jun paypoq",
        ]
    elif t <= 0:
        tips += [
            "🧥 Qishki kurtka",
            "🧶 Sviter yoki issiq kofta",
            "🧣 Sharf, qo'lqop va shapka",
            "🥾 Issiq yopiq poyabzal",
        ]
    elif t <= 8:
        tips += [
            "🧥 Issiq kurtka yoki palto",
            "👕 Ichiga sviter yoki xudi",
            "👖 Shim (jinsi yoki issiq shim)",
            "👟 Yopiq poyabzal",
        ]
    elif t <= 14:
        tips += [
            "🧥 Yengil kurtka yoki plashch",
            "👕 Uzun yengli futbolka yoki yupqa sviter",
            "👖 Shim",
        ]
    elif t <= 19:
        tips += [
            "👕 Uzun yengli ko'ylak yoki yengil kofta",
            "🧥 Kechqurun uchun yupqa kurtka olib oling",
            "👖 Jinsi yoki yengil shim",
        ]
    elif t <= 25:
        tips += [
            "👕 Futbolka yoki yengil ko'ylak",
            "👖 Yengil shim yoki yubka",
            "👟 Krossovka yoki yengil poyabzal",
        ]
    else:
        tips += [
            "👕 Yengil, och rangli, paxta yoki zig'ir kiyim",
            "🩳 Shorti yoki yengil yubka",
            "🩴 Ochiq, yengil poyabzal",
        ]

    # Kun davomida harorat katta farq qilsa — qatlamli kiyinish
    if f.temp_max - f.temp_min >= 10:
        tips.append(
            f"🔄 Kun davomida harorat {f.temp_min:.0f}° dan {f.temp_max:.0f}° gacha "
            "o'zgaradi — qatlamli kiyining, ustki kiyimni yechib olsa bo'ladigan qilib"
        )

    if f.is_snowy:
        tips.append("❄️ Qor yog'adi — suv o'tkazmaydigan, sirpanmaydigan poyabzal kiying")
    elif f.is_rainy:
        tips.append(
            f"☂️ Yomg'ir ehtimoli {f.precip_probability}% — soyabon yoki yomg'irpo'sh oling"
        )
        if f.precip_sum >= 5:
            tips.append("👢 Suv o'tkazmaydigan poyabzal kiygan ma'qul")

    if f.wind_max >= 30:
        tips.append(
            f"💨 Kuchli shamol ({f.wind_max:.0f} km/soat) — shamol o'tkazmaydigan ustki kiyim"
        )

    if f.uv_index >= 6:
        tips.append("🕶 Quyosh kuchli (UV yuqori) — ko'zoynak, kepka va quyoshdan himoya kremi")
    elif f.uv_index >= 3 and f.temp_max >= 20:
        tips.append("🧢 Kepka yoki shlyapa kiysangiz yaxshi")

    if f.temp_max >= 32:
        tips.append("💧 Juda issiq — ko'proq suv iching va yonigizda suv olib yuring")

    return tips


def build_message(f: DailyForecast, name: str | None = None) -> str:
    greeting = f"Xayrli tong, {name}! ☀️" if name else "Xayrli tong! ☀️"
    lines = [
        greeting,
        "",
        f"<b>Bugungi ob-havo:</b> {f.emoji} {f.description}",
        f"🌡 Harorat: {f.temp_min:.0f}° ... {f.temp_max:.0f}°C",
        f"🤔 His qilinadi: {f.feels_min:.0f}° ... {f.feels_max:.0f}°C",
        f"🌅 Ertalab (08:00): {f.morning_temp:.0f}°C",
        f"☔ Yog'in ehtimoli: {f.precip_probability}%",
        f"💨 Shamol: {f.wind_max:.0f} km/soat",
        "",
        "<b>👔 Bugun nima kiyish kerak:</b>",
    ]
    lines += [f"• {tip}" for tip in clothing_advice(f)]
    lines += ["", "Kuningiz xayrli o'tsin! 😊"]
    return "\n".join(lines)
