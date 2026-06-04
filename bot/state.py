import json
import os
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get("DATABASE_URL", "")

SCHEMA = """
CREATE TABLE IF NOT EXISTS checkin_state (
    chat_id       BIGINT PRIMARY KEY,
    session_idx   INTEGER NOT NULL DEFAULT 0,
    exercise_idx  INTEGER NOT NULL DEFAULT 0,
    awaiting_note INTEGER NOT NULL DEFAULT 0,
    results       JSONB NOT NULL DEFAULT '{}',
    started_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS checkin_history (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    week_number       INTEGER NOT NULL,
    completed_at      TEXT NOT NULL,
    schedule_snapshot JSONB NOT NULL,
    results           JSONB NOT NULL
);
"""


def _conn() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db() -> None:
    with _conn() as conn:
        conn.execute(SCHEMA)


def start_checkin(chat_id: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        conn.execute("DELETE FROM checkin_state WHERE chat_id = %s", (chat_id,))
        conn.execute(
            "INSERT INTO checkin_state (chat_id, started_at) VALUES (%s, %s)",
            (chat_id, now),
        )


def get_state(chat_id: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM checkin_state WHERE chat_id = %s", (chat_id,)
        ).fetchone()
    if not row:
        return None
    return {
        "chat_id": row["chat_id"],
        "session_idx": row["session_idx"],
        "exercise_idx": row["exercise_idx"],
        "awaiting_note": bool(row["awaiting_note"]),
        "results": row["results"],  # psycopg deserialises JSONB to dict automatically
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
        fields.append("session_idx = %s")
        values.append(session_idx)
    if exercise_idx is not None:
        fields.append("exercise_idx = %s")
        values.append(exercise_idx)
    if awaiting_note is not None:
        fields.append("awaiting_note = %s")
        values.append(1 if awaiting_note else 0)
    if results is not None:
        fields.append("results = %s")
        values.append(json.dumps(results))
    if not fields:
        return
    values.append(chat_id)
    with _conn() as conn:
        conn.execute(
            f"UPDATE checkin_state SET {', '.join(fields)} WHERE chat_id = %s",
            values,
        )


def end_checkin(chat_id: int, *, week_number: int, schedule: dict, results: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO checkin_history (week_number, completed_at, schedule_snapshot, results)"
            " VALUES (%s, %s, %s, %s)",
            (week_number, now, json.dumps(schedule), json.dumps(results)),
        )
        conn.execute("DELETE FROM checkin_state WHERE chat_id = %s", (chat_id,))


def latest_week_number() -> int:
    with _conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(week_number), 0) AS n FROM checkin_history"
        ).fetchone()
    return int(row["n"]) if row else 0
