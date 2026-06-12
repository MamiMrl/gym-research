import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot import state as st
from bot.keyboards import CONFIRM_KEYBOARD
from core import llm_client, pdf, transcribe
from core.email import dispatch_newsletter, prepare_newsletter
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


async def start_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    st.start_checkin(chat_id)

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


async def _generate_and_show_plan(update: Update, chat_id: int, transcript: str) -> None:
    st.set_state(chat_id, transcript=transcript)
    await update.effective_chat.send_message(
        f"*Transcript:*\n_{transcript}_\n\nGenerating proposed plan…",
        parse_mode="Markdown",
    )

    schedule = load_schedule()
    try:
        new_plan = llm_client.generate_plan(schedule, transcript)
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

    st.set_state(chat_id, voice_file_id=voice.file_id)
    await _generate_and_show_plan(update, chat_id, transcript)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    s = st.get_state(chat_id)
    if s is None:
        await update.effective_chat.send_message(
            "No active check-in. Send /checkin to start."
        )
        return

    transcript = (update.message.text or "").strip()
    if not transcript:
        return

    await _generate_and_show_plan(update, chat_id, transcript)


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
    transcript = s.get("transcript") or ""
    await update.effective_chat.send_message("Generating PDF and sending newsletter…")

    try:
        pdf_path = pdf.render_pdf(new_plan, output_path="/tmp/plan.pdf")
    except Exception as exc:
        logger.exception("PDF render failed")
        await update.effective_chat.send_message(f"PDF render failed: {exc}")
        return

    # Load this-week BEFORE save_schedule overwrites it — the newsletter recap
    # diffs (this_week → next_week) to compute +kg added, biggest jump, etc.
    this_week = load_schedule()
    week_number = st.latest_week_number() + 1
    used_ids = st.recent_fact_ids(limit=8)

    # Prepare (pure) → archive (durable) → dispatch (irreversible). The email
    # send is the LAST step on purpose: if the DB write fails after a successful
    # send, the recipient is stuck with a CTA pointing at a missing row.
    try:
        used_fact_id, email_payload = prepare_newsletter(
            this_week=this_week,
            next_week=new_plan,
            transcript=transcript,
            week_number=week_number,
            used_fact_ids=used_ids,
            pdf_path=pdf_path,
        )
    except Exception as exc:
        logger.exception("Newsletter prepare failed")
        await update.effective_chat.send_message(f"Newsletter prepare failed: {exc}")
        return

    # schedule_snapshot = the plan that's now active (= new_plan). That's what
    # GET /plan/{week_number}.pdf re-renders. end_checkin UPSERTs on week_number
    # so a retried Confirm at the same number is safe.
    save_schedule(new_plan)
    try:
        st.end_checkin(
            chat_id,
            week_number=week_number,
            schedule=new_plan,
            transcript=transcript,
            used_fact_id=used_fact_id,
        )
    except Exception as exc:
        logger.exception("Archive failed before send")
        await update.effective_chat.send_message(
            f"Archive failed, email NOT sent: {exc}"
        )
        return

    try:
        dispatch_newsletter(email_payload)
    except Exception as exc:
        logger.exception("Newsletter dispatch failed")
        await update.effective_chat.send_message(
            f"Week {week_number} archived, but email send failed: {exc}\n"
            f"Re-run /checkin to retry — the next attempt will advance to "
            f"week {week_number + 1}."
        )
        return

    await update.effective_chat.send_message(
        f"Done. Week {week_number} newsletter sent: *{new_plan['week_label']}*",
        parse_mode="Markdown",
    )
