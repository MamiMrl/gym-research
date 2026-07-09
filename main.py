import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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
from core import pdf, signing  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("workout-tracker")

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])
CRON_SECRET = os.environ["CRON_SECRET"]
TELEGRAM_WEBHOOK_SECRET = os.environ["TELEGRAM_WEBHOOK_SECRET"]

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
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.on_text))

# Init DB at module load — idempotent (CREATE TABLE IF NOT EXISTS), runs once
# per cold-start container.
state.init_db()

app = FastAPI()

# Serve the curated hero photos used as <img src> in the weekly newsletter.
# Newsletter callers build absolute URLs via APP_BASE_URL + /static/hero/<file>.
_HERO_DIR = Path(__file__).resolve().parent / "assets" / "hero"
if _HERO_DIR.is_dir():
    app.mount("/static/hero", StaticFiles(directory=str(_HERO_DIR)), name="hero")


@app.get("/")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/plan/{week_number}.pdf")
async def download_plan(week_number: int, t: str = "") -> FileResponse:
    """Signed PDF download for the weekly newsletter CTA.

    HMAC-gated by signing.verify_week. The schedule is fetched from
    checkin_history and re-rendered on the fly via PDFShift — see
    README → "Future scaling" for when to cache instead.
    """
    if not signing.verify_week(week_number, t):
        raise HTTPException(status_code=403, detail="Invalid or missing token")

    row = state.get_history_by_week(week_number)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No archived plan for week {week_number}")

    snapshot = row["schedule_snapshot"]
    out_path = f"/tmp/plan-week-{week_number}.pdf"
    try:
        pdf.render_pdf(snapshot, output_path=out_path)
    except Exception as exc:
        logger.exception("PDF re-render failed for week %s", week_number)
        raise HTTPException(status_code=502, detail=f"PDF render failed: {exc}") from exc

    return FileResponse(
        out_path,
        media_type="application/pdf",
        filename=f"light-weight-week-{week_number}.pdf",
    )


@app.post("/webhook")
async def webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    if x_telegram_bot_api_secret_token != TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)
    if update.effective_chat is None or update.effective_chat.id != TELEGRAM_CHAT_ID:
        # Silently drop — no reply, so strangers get no confirmation the bot is alive.
        return {"ok": True}

    async with ptb_app:
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
