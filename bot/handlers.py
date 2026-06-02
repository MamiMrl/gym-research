import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot import state as st
from bot.keyboards import STATUS_KEYBOARD, SKIP_NOTE_KEYBOARD, SUBMIT_KEYBOARD
from core import claude_client, pdf
from core.email import send_plan_email
from core.schedule import load_schedule, save_schedule

logger = logging.getLogger(__name__)

STATUS_LABELS = {
    "as_planned": "✓ As planned",
    "too_easy":   "↑ Too easy",
    "struggled":  "↓ Struggled",
    "skipped":    "✗ Skipped",
}


def _current_exercise(schedule: dict, s: dict):
    sessions = schedule["sessions"]
    if s["session_idx"] >= len(sessions):
        return None, None
    session = sessions[s["session_idx"]]
    exercises = session["exercises"]
    if s["exercise_idx"] >= len(exercises):
        return session, None
    return session, exercises[s["exercise_idx"]]


async def _send_session_header(update: Update, session: dict) -> None:
    await update.effective_chat.send_message(
        f"*{session['day']} — {session['label']}*",
        parse_mode="Markdown",
    )


async def _prompt_for_exercise(update: Update, session: dict, exercise: dict) -> None:
    load = f"{exercise['load_kg']} kg" if exercise.get("load_kg") else (exercise.get("note") or "bodyweight")
    text = (
        f"*{exercise['name']}*\n"
        f"{exercise['sets']}×{exercise['reps']} @ {load}\n\n"
        "How did it go?"
    )
    await update.effective_chat.send_message(text, parse_mode="Markdown", reply_markup=STATUS_KEYBOARD)


async def _advance(update: Update, schedule: dict, s: dict) -> None:
    session, exercise = _current_exercise(schedule, s)

    if exercise is not None:
        await _prompt_for_exercise(update, session, exercise)
        return

    # End of session: advance to next session
    s["session_idx"] += 1
    s["exercise_idx"] = 0
    st.set_state(s["chat_id"], session_idx=s["session_idx"], exercise_idx=0)

    session, exercise = _current_exercise(schedule, s)
    if exercise is None:
        # All done — show submit
        await update.effective_chat.send_message(
            "All exercises logged. Ready to generate next week's plan?",
            reply_markup=SUBMIT_KEYBOARD,
        )
        return

    await _send_session_header(update, session)
    await _prompt_for_exercise(update, session, exercise)


async def start_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    st.start_checkin(chat_id)
    schedule = load_schedule()
    s = st.get_state(chat_id)
    await update.effective_chat.send_message(
        f"Weekly check-in: *{schedule['week_label']}*",
        parse_mode="Markdown",
    )
    session, _ = _current_exercise(schedule, s)
    await _send_session_header(update, session)
    await _advance(update, schedule, s)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    data = query.data

    if data == "submit":
        await _on_submit(update, context)
        return

    if data == "skip_note":
        await _record_note(update, "")
        return

    if data.startswith("status:"):
        status = data.split(":", 1)[1]
        await _record_status(update, status)
        return


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    s = st.get_state(chat_id)
    if not s or not s["awaiting_note"]:
        return
    await _record_note(update, update.message.text or "")


async def _record_status(update: Update, status: str) -> None:
    chat_id = update.effective_chat.id
    s = st.get_state(chat_id)
    if s is None:
        return
    schedule = load_schedule()
    session, exercise = _current_exercise(schedule, s)
    if exercise is None:
        return

    results = s["results"]
    day = session["day"]
    results.setdefault(day, {})[exercise["name"]] = {"status": status, "note": ""}
    st.set_state(chat_id, results=results, awaiting_note=True)

    await update.effective_chat.send_message(
        f"Logged: {STATUS_LABELS.get(status, status)}\nAny note? (or tap Skip)",
        reply_markup=SKIP_NOTE_KEYBOARD,
    )


async def _record_note(update: Update, note: str) -> None:
    chat_id = update.effective_chat.id
    s = st.get_state(chat_id)
    if s is None:
        return
    schedule = load_schedule()
    session, exercise = _current_exercise(schedule, s)
    if exercise is None:
        return

    results = s["results"]
    day = session["day"]
    if day in results and exercise["name"] in results[day]:
        results[day][exercise["name"]]["note"] = note.strip()

    s["exercise_idx"] += 1
    st.set_state(
        chat_id,
        exercise_idx=s["exercise_idx"],
        results=results,
        awaiting_note=False,
    )
    s["results"] = results
    await _advance(update, schedule, s)


async def _on_submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    s = st.get_state(chat_id)
    if s is None:
        await update.effective_chat.send_message("No active check-in to submit.")
        return

    await update.effective_chat.send_message("Generating next week's plan…")

    schedule = load_schedule()
    try:
        new_plan = claude_client.generate_plan(schedule, s["results"])
    except Exception as exc:
        logger.exception("Claude generation failed")
        await update.effective_chat.send_message(f"Plan generation failed: {exc}")
        return

    pdf_path = pdf.render_pdf(new_plan, output_path="/tmp/plan.pdf")

    try:
        send_plan_email(pdf_path, new_plan["week_label"])
    except Exception as exc:
        logger.exception("Email send failed")
        await update.effective_chat.send_message(f"Email failed: {exc}")
        return

    save_schedule(new_plan)

    week_number = st.latest_week_number() + 1
    st.end_checkin(chat_id, week_number=week_number, schedule=schedule, results=s["results"])

    await update.effective_chat.send_message(
        f"Done. Week {week_number} plan emailed: *{new_plan['week_label']}*",
        parse_mode="Markdown",
    )
