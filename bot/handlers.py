import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot import state as st
from bot.keyboards import CONFIRM_KEYBOARD
from core import llm_client, pdf, transcribe
from core.email import send_plan_email
from core.schedule import load_schedule, save_schedule

logger = logging.getLogger(__name__)


def _format_schedule(schedule: dict) -> str:
    lines = [f"*{schedule['week_label']}*", ""]
    for session in schedule["sessions"]:
        lines.append(f"*{session['day']} — {session['label']}*")
        for ex in session["exercises"]:
            load = f"{ex['load_kg']} kg" if ex.get("load_kg") is not None else "BW"
            lines.append(f"  • {ex['name']}: {ex['sets']}×{ex['reps']} @ {load}")
        lines.append("")
    return "\n".join(lines)


def _format_diff(old: dict, new: dict) -> str:
    """Side-by-side diff of weights between old and new plan, plus deload flag."""
    lines = []
    if new.get("deload"):
        lines.append("⚠ *DELOAD WEEK*")
        if new.get("deload_reason"):
            lines.append(f"   _{new['deload_reason']}_")
        lines.append("")

    lines.append(f"*Next week:* {new['week_label']}")
    lines.append("")

    old_by_day = {s["day"]: s for s in old["sessions"]}
    for new_session in new["sessions"]:
        lines.append(f"*{new_session['day']} — {new_session['label']}*")
        old_session = old_by_day.get(new_session["day"], {"exercises": []})
        old_by_name = {e["name"]: e for e in old_session.get("exercises", [])}
        for new_ex in new_session["exercises"]:
            old_ex = old_by_name.get(new_ex["name"], {})
            old_load = old_ex.get("load_kg")
            new_load = new_ex.get("load_kg")
            old_sets = old_ex.get("sets")
            new_sets = new_ex.get("sets")

            load_str = (
                f"{new_load} kg" if new_load is not None else "BW"
            )
            arrow = ""
            if old_load is not None and new_load is not None and old_load != new_load:
                delta = new_load - old_load
                arrow = f"  ({old_load}→{new_load}, {'+' if delta >= 0 else ''}{delta:g} kg)"
            sets_str = (
                f"{new_sets}×{new_ex['reps']}"
                if old_sets == new_sets
                else f"{new_sets}×{new_ex['reps']} (was {old_sets})"
            )
            lines.append(f"  • {new_ex['name']}: {sets_str} @ {load_str}{arrow}")
        lines.append("")
    return "\n".join(lines)


def _format_strava_section(summary: dict | None) -> str:
    if not summary or summary.get("count", 0) == 0:
        return ""
    lines = ["", "*Strava (past 7 days):*"]
    lines.append(
        f"  {summary['count']} activities, "
        f"{summary['total_distance_km']} km, "
        f"{summary['total_moving_time_min']} min moving"
    )
    flags = summary.get("hr_flags") or []
    if flags:
        lines.append("  ⚠ HR flags:")
        for f in flags:
            lines.append(f"    • {f}")
    return "\n".join(lines)


async def start_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    st.start_checkin(chat_id)

    # Try to fetch + persist Strava activities. Failure is non-fatal.
    strava_summary = None
    try:
        from core import strava
        from bot.state import _conn  # noqa: WPS437 — internal helper
        activities = strava.fetch_recent_activities(7)
        with _conn() as conn:
            strava.persist_activities(conn, activities)
        strava_summary = strava.summarize(activities)
        st.set_state(chat_id, strava_summary=strava_summary)
    except Exception as exc:
        logger.warning("Strava fetch failed (non-fatal): %s", exc)

    schedule = load_schedule()
    intro = (
        f"*Weekly check-in: {schedule['week_label']}*\n\n"
        "Here's this week's planned schedule. When you're ready, send me a "
        "*voice memo* summarising how each session went — exercises, weights, "
        "how it felt. I'll parse it, propose next week's loads, and show you "
        "before anything gets emailed.\n"
    )
    await update.effective_chat.send_message(intro, parse_mode="Markdown")
    await update.effective_chat.send_message(_format_schedule(schedule), parse_mode="Markdown")

    strava_section = _format_strava_section(strava_summary)
    if strava_section:
        await update.effective_chat.send_message(strava_section, parse_mode="Markdown")


async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    s = st.get_state(chat_id)
    if s is None:
        await update.effective_chat.send_message(
            "No active check-in. Send /checkin to start."
        )
        return

    voice = update.message.voice or update.message.audio
    if voice is None:
        return

    await update.effective_chat.send_message("Got it. Transcribing…")

    try:
        tg_file = await voice.get_file()
        audio_bytes = bytes(await tg_file.download_as_bytearray())
    except Exception as exc:
        logger.exception("Voice download failed")
        await update.effective_chat.send_message(f"Couldn't download voice: {exc}")
        return

    try:
        transcript = transcribe.transcribe(audio_bytes, filename="voice.ogg")
    except Exception as exc:
        logger.exception("Transcription failed")
        await update.effective_chat.send_message(f"Transcription failed: {exc}")
        return

    if not transcript:
        await update.effective_chat.send_message(
            "Transcript came back empty — try recording again."
        )
        return

    st.set_state(chat_id, voice_file_id=voice.file_id, transcript=transcript)

    await update.effective_chat.send_message(
        f"*Transcript:*\n_{transcript}_\n\nGenerating proposed plan…",
        parse_mode="Markdown",
    )

    schedule = load_schedule()
    strava_summary = s.get("strava_summary")
    try:
        new_plan = llm_client.generate_plan(schedule, transcript, strava_summary)
    except Exception as exc:
        logger.exception("LLM plan generation failed")
        await update.effective_chat.send_message(
            f"Plan generation failed: {exc}\n\nSend /checkin to retry."
        )
        return

    st.set_state(chat_id, proposed_changes=new_plan)

    diff = _format_diff(schedule, new_plan)
    await update.effective_chat.send_message(
        diff + "\n\nConfirm to email the PDF, or re-record if anything is wrong.",
        parse_mode="Markdown",
        reply_markup=CONFIRM_KEYBOARD,
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "confirm":
        await _on_confirm(update, context)
    elif data == "rerecord":
        await _on_rerecord(update, context)


async def _on_rerecord(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    st.set_state(chat_id, transcript="", proposed_changes={})
    await update.effective_chat.send_message(
        "Cleared. Send a new voice memo whenever you're ready."
    )


async def _on_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    s = st.get_state(chat_id)
    if s is None or not s.get("proposed_changes"):
        await update.effective_chat.send_message("Nothing to confirm. Send /checkin.")
        return

    new_plan = s["proposed_changes"]
    await update.effective_chat.send_message("Generating PDF and sending email…")

    try:
        pdf_path = pdf.render_pdf(new_plan, output_path="/tmp/plan.pdf")
    except Exception as exc:
        logger.exception("PDF render failed")
        await update.effective_chat.send_message(f"PDF render failed: {exc}")
        return

    try:
        send_plan_email(pdf_path, new_plan["week_label"])
    except Exception as exc:
        logger.exception("Email send failed")
        await update.effective_chat.send_message(f"Email failed: {exc}")
        return

    schedule = load_schedule()
    save_schedule(new_plan)

    week_number = st.latest_week_number() + 1
    st.end_checkin(
        chat_id,
        week_number=week_number,
        schedule=schedule,
        transcript=s.get("transcript"),
        strava_summary=s.get("strava_summary"),
    )

    await update.effective_chat.send_message(
        f"Done. Week {week_number} plan emailed: *{new_plan['week_label']}*",
        parse_mode="Markdown",
    )
