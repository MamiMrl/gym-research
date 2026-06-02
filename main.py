import logging
import os
from contextlib import asynccontextmanager

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
TRIGGER_SECRET = os.environ["TRIGGER_SECRET"]

application = (
    Application.builder()
    .token(TELEGRAM_BOT_TOKEN)
    .updater(None)
    .build()
)

application.add_handler(CommandHandler("start", handlers.start_checkin))
application.add_handler(CommandHandler("checkin", handlers.start_checkin))
application.add_handler(CallbackQueryHandler(handlers.on_callback))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.on_text))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    state.init_db()
    await application.initialize()
    await application.start()
    logger.info("Bot started")
    try:
        yield
    finally:
        await application.stop()
        await application.shutdown()
        logger.info("Bot stopped")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(request: Request) -> dict:
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}


@app.post("/trigger")
async def trigger(authorization: str | None = Header(default=None)) -> dict:
    expected = f"Bearer {TRIGGER_SECRET}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Simulate /checkin invocation by injecting a synthetic update.
    class _Chat:
        id = TELEGRAM_CHAT_ID

        async def send_message(self, text, **kwargs):
            return await application.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, **kwargs)

    class _Update:
        @property
        def effective_chat(self):
            return _Chat()

    await handlers.start_checkin(_Update(), None)
    return {"ok": True, "triggered_chat_id": TELEGRAM_CHAT_ID}
