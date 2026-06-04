import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

load_dotenv()

from bot import handlers, state  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("workout-tracker")

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])
CRON_SECRET = os.environ["CRON_SECRET"]

# Named ptb_app (not 'application') to avoid Vercel's ASGI entrypoint
# auto-detection picking it up instead of the FastAPI `app` below.
ptb_app = (
    Application.builder()
    .token(TELEGRAM_BOT_TOKEN)
    .updater(None)
    .build()
)

ptb_app.add_handler(CommandHandler("start", handlers.start_checkin))
ptb_app.add_handler(CommandHandler("checkin", handlers.start_checkin))
ptb_app.add_handler(CallbackQueryHandler(handlers.on_callback))
ptb_app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handlers.on_voice))

# Init DB at module load — idempotent (CREATE TABLE IF NOT EXISTS), runs once
# per cold-start container.
state.init_db()

app = FastAPI()


@app.get("/")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(request: Request) -> dict:
    data = await request.json()
    async with ptb_app:
        update = Update.de_json(data, ptb_app.bot)
        await ptb_app.process_update(update)
    return {"ok": True}


@app.get("/trigger")
async def trigger(authorization: str | None = Header(default=None)) -> dict:
    if authorization != f"Bearer {CRON_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    class _Chat:
        id = TELEGRAM_CHAT_ID

        async def send_message(self, text, **kwargs):
            return await ptb_app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, **kwargs)

    class _Update:
        @property
        def effective_chat(self):
            return _Chat()

    async with ptb_app:
        await handlers.start_checkin(_Update(), None)
    return {"ok": True, "triggered_chat_id": TELEGRAM_CHAT_ID}
