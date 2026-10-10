# daily-weather 🌤👔

Telegram bot: har kuni ertalab soat **07:00** da (sizning vaqt zonangizda) bugungi
ob-havoni va **qanday kiyinish kerakligi** haqida tavsiya yuboradi.

## Qanday ishlaydi
1. Foydalanuvchi `/start` bosadi → bot **"📍 Joylashuvni yuborish"** tugmasini ko'rsatadi.
2. Tugma bosilganda Telegram telefonning GPS joylashuvini yuboradi.
3. Bot joylashuv bo'yicha vaqt zonasini aniqlaydi (masalan `Asia/Tashkent`) va
   har kuni 07:00 ga xabar rejalashtiradi.
4. Ob-havo [Open-Meteo](https://open-meteo.com/) dan olinadi — bepul, API kalit kerak emas.
5. Kiyim tavsiyasi "his qilinadigan" harorat, yomg'ir/qor, shamol, UV va kun
   davomidagi harorat farqiga qarab tuziladi.

## Buyruqlar
| Buyruq | Vazifasi |
|---|---|
| `/start` | Boshlash va joylashuv yuborish |
| `/obhavo` | Hozir bugungi ob-havo va tavsiyani olish |
| `/vaqt 06:30` | Kundalik xabar vaqtini o'zgartirish |
| `/joylashuv` | Joylashuvni yangilash |
| `/stop` | Xabarlarni to'xtatish |

## Ishga tushirish
1. Telegramda [@BotFather](https://t.me/BotFather) ga `/newbot` yozib, token oling.
2. O'rnating va ishga tushiring:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   export TELEGRAM_BOT_TOKEN="123456:ABC..."
   python -m weatherbot.bot
   ```
Bot doimiy ishlab turishi kerak (masalan VPS, Railway, Render yoki uy kompyuterida),
aks holda ertalabki xabarlar yuborilmaydi. Foydalanuvchilar `weatherbot.db`
(SQLite) faylida saqlanadi, bot qayta ishga tushganda jadval tiklanadi.

## Testlar
```bash
pip install pytest
python -m pytest
```
