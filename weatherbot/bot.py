"""Telegram bot: har kuni ertalab ob-havo va kiyim tavsiyasini yuboradi."""

from __future__ import annotations

import datetime as dt
import logging
import os
import re

import pytz
from telegram import (
    BotCommand,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .clothing import build_message
from .storage import Storage, User
from .weather import fetch_timezone, fetch_today

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("weatherbot")

LOCATION_KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("📍 Joylashuvni yuborish", request_location=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

TIME_RE = re.compile(r"^([01]?\d|2[0-3])[:.]([0-5]\d)$")


def storage(context: ContextTypes.DEFAULT_TYPE) -> Storage:
    return context.application.bot_data["storage"]


def schedule_user(app: Application, user: User) -> None:
    """Foydalanuvchi uchun kundalik xabarni (uning vaqt zonasida) rejalashtiradi."""
    for job in app.job_queue.get_jobs_by_name(str(user.chat_id)):
        job.schedule_removal()
    when = dt.time(user.hour, user.minute, tzinfo=pytz.timezone(user.timezone))
    app.job_queue.run_daily(
        daily_job, time=when, chat_id=user.chat_id, name=str(user.chat_id)
    )
    log.info("Scheduled %s at %s %s", user.chat_id, when.strftime("%H:%M"), user.timezone)


async def send_forecast(context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    try:
        forecast = await fetch_today(user.lat, user.lon)
    except Exception:
        log.exception("Weather fetch failed for %s", user.chat_id)
        await context.bot.send_message(
            user.chat_id, "😔 Ob-havo ma'lumotini olib bo'lmadi. Keyinroq /obhavo ni bosing."
        )
        return
    await context.bot.send_message(
        user.chat_id, build_message(forecast, user.name), parse_mode=ParseMode.HTML
    )


async def daily_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    user = storage(context).get(context.job.chat_id)
    if user:
        await send_forecast(context, user)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Assalomu alaykum! 👋\n\n"
        "Men har kuni ertalab soat <b>07:00</b> da sizga bugungi ob-havoni va "
        "qanday kiyinish kerakligini yuboraman.\n\n"
        "Buning uchun pastdagi tugmani bosib, telefoningiz joylashuvini yuboring 👇",
        parse_mode=ParseMode.HTML,
        reply_markup=LOCATION_KEYBOARD,
    )


async def on_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    loc = msg.location
    chat_id = msg.chat_id
    old = storage(context).get(chat_id)

    # Jonli joylashuv yangilanishi: faqat koordinatani yangilaymiz, xabar yubormaymiz
    if update.edited_message:
        if old:
            old.lat, old.lon = loc.latitude, loc.longitude
            storage(context).save(old)
        return

    try:
        tz = await fetch_timezone(loc.latitude, loc.longitude)
    except Exception:
        log.exception("Timezone lookup failed")
        tz = "Asia/Tashkent"

    user = User(
        chat_id=chat_id,
        name=update.effective_user.first_name if update.effective_user else None,
        lat=loc.latitude,
        lon=loc.longitude,
        timezone=tz,
        hour=old.hour if old else 7,
        minute=old.minute if old else 0,
    )
    storage(context).save(user)
    schedule_user(context.application, user)

    await msg.reply_text(
        f"✅ Joylashuv saqlandi! (vaqt zonasi: {tz})\n"
        f"Har kuni soat <b>{user.hour:02d}:{user.minute:02d}</b> da xabar yuboraman.\n\n"
        "Buyruqlar:\n"
        "/obhavo — hozir bugungi ob-havoni ko'rish\n"
        "/vaqt 06:30 — xabar vaqtini o'zgartirish\n"
        "/joylashuv — joylashuvni yangilash\n"
        "/stop — xabarlarni to'xtatish\n\n"
        "Mana bugungi ma'lumot 👇",
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardRemove(),
    )
    await send_forecast(context, user)


async def weather_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = storage(context).get(update.effective_chat.id)
    if not user:
        await update.message.reply_text(
            "Avval joylashuvingizni yuboring 👇", reply_markup=LOCATION_KEYBOARD
        )
        return
    await send_forecast(context, user)


async def ask_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Yangi joylashuvni yuboring 👇", reply_markup=LOCATION_KEYBOARD
    )


async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = storage(context).get(update.effective_chat.id)
    if not user:
        await update.message.reply_text(
            "Avval joylashuvingizni yuboring 👇", reply_markup=LOCATION_KEYBOARD
        )
        return
    match = TIME_RE.match(context.args[0]) if context.args else None
    if not match:
        await update.message.reply_text(
            f"Hozirgi vaqt: {user.hour:02d}:{user.minute:02d}\n"
            "O'zgartirish uchun masalan: /vaqt 06:30"
        )
        return
    user.hour, user.minute = int(match[1]), int(match[2])
    storage(context).save(user)
    schedule_user(context.application, user)
    await update.message.reply_text(
        f"⏰ Endi har kuni soat {user.hour:02d}:{user.minute:02d} da xabar yuboraman."
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    storage(context).delete(chat_id)
    for job in context.job_queue.get_jobs_by_name(str(chat_id)):
        job.schedule_removal()
    await update.message.reply_text(
        "🛑 Kundalik xabarlar to'xtatildi. Qayta boshlash uchun /start bosing."
    )


async def post_init(app: Application) -> None:
    await app.bot.set_my_commands(
        [
            BotCommand("start", "Botni boshlash"),
            BotCommand("obhavo", "Bugungi ob-havo va kiyim tavsiyasi"),
            BotCommand("vaqt", "Xabar vaqtini o'zgartirish (masalan 06:30)"),
            BotCommand("joylashuv", "Joylashuvni yangilash"),
            BotCommand("stop", "Xabarlarni to'xtatish"),
        ]
    )
    for user in app.bot_data["storage"].all():
        schedule_user(app, user)


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan")

    app = Application.builder().token(token).post_init(post_init).build()
    app.bot_data["storage"] = Storage(os.environ.get("DB_PATH", "weatherbot.db"))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("obhavo", weather_now))
    app.add_handler(CommandHandler("vaqt", set_time))
    app.add_handler(CommandHandler("joylashuv", ask_location))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.LOCATION, on_location))

    log.info("Bot ishga tushdi")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
