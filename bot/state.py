import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = os.environ.get("STATE_DB_PATH", str(Path(__file__).resolve().parent.parent / "state.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS checkin_state (
    chat_id      INTEGER PRIMARY KEY,
    session_idx  INTEGER NOT NULL DEFAULT 0,
    exercise_idx INTEGER NOT NULL DEFAULT 0,
    awaiting_note INTEGER NOT NULL DEFAULT 0,
    results      TEXT NOT NULL DEFAULT '{}',
    started_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS checkin_history (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    week_number       INTEGER NOT NULL,
    completed_at      TEXT NOT NULL,
    schedule_snapshot TEXT NOT NULL,
    results           TEXT NOT NULL
);
"""


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as c:
        c.executescript(SCHEMA)


def start_checkin(chat_id: int) -> None:
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as c:
        c.execute("DELETE FROM checkin_state WHERE chat_id = ?", (chat_id,))
        c.execute(
            "INSERT INTO checkin_state (chat_id, started_at) VALUES (?, ?)",
            (chat_id, now),
        )


def get_state(chat_id: int) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM checkin_state WHERE chat_id = ?", (chat_id,)).fetchone()
    if not row:
        return None
    return {
        "chat_id": row["chat_id"],
        "session_idx": row["session_idx"],
        "exercise_idx": row["exercise_idx"],
        "awaiting_note": bool(row["awaiting_note"]),
        "results": json.loads(row["results"]),
        "started_at": row["started_at"],
    }


def set_state(
    chat_id: int,
    *,
    session_idx: int | None = None,
    exercise_idx: int | None = None,
    awaiting_note: bool | None = None,
    results: dict | None = None,
) -> None:
    fields = []
    values = []
    if session_idx is not None:
        fields.append("session_idx = ?")
        values.append(session_idx)
    if exercise_idx is not None:
        fields.append("exercise_idx = ?")
        values.append(exercise_idx)
    if awaiting_note is not None:
        fields.append("awaiting_note = ?")
        values.append(1 if awaiting_note else 0)
    if results is not None:
        fields.append("results = ?")
        values.append(json.dumps(results))
    if not fields:
        return
    values.append(chat_id)
    with _conn() as c:
        c.execute(f"UPDATE checkin_state SET {', '.join(fields)} WHERE chat_id = ?", values)


def end_checkin(chat_id: int, *, week_number: int, schedule: dict, results: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as c:
        c.execute(
            "INSERT INTO checkin_history (week_number, completed_at, schedule_snapshot, results) VALUES (?, ?, ?, ?)",
            (week_number, now, json.dumps(schedule), json.dumps(results)),
        )
        c.execute("DELETE FROM checkin_state WHERE chat_id = ?", (chat_id,))


def latest_week_number() -> int:
    with _conn() as c:
        row = c.execute("SELECT COALESCE(MAX(week_number), 0) AS n FROM checkin_history").fetchone()
    return int(row["n"]) if row else 0
