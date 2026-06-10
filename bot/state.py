import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get("DATABASE_URL", "")


@contextmanager
def _conn():
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        yield conn


def init_db() -> None:
    # One execute() per statement — psycopg v3 rule.
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkin_state (
                chat_id          BIGINT PRIMARY KEY,
                voice_file_id    TEXT,
                transcript       TEXT,
                proposed_changes JSONB,
                started_at       TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkin_history (
                id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                week_number       INTEGER NOT NULL,
                completed_at      TEXT NOT NULL,
                schedule_snapshot JSONB NOT NULL,
                transcript        TEXT
            )
        """)
        # ALTER stays idempotent — safe to call on every cold boot.
        conn.execute(
            "ALTER TABLE checkin_history ADD COLUMN IF NOT EXISTS used_fact_id TEXT"
        )


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
        "voice_file_id": row["voice_file_id"],
        "transcript": row["transcript"],
        "proposed_changes": row["proposed_changes"],
        "started_at": row["started_at"],
    }


def set_state(
    chat_id: int,
    *,
    voice_file_id: str | None = None,
    transcript: str | None = None,
    proposed_changes: dict | None = None,
) -> None:
    fields = []
    values = []
    if voice_file_id is not None:
        fields.append("voice_file_id = %s")
        values.append(voice_file_id)
    if transcript is not None:
        fields.append("transcript = %s")
        values.append(transcript)
    if proposed_changes is not None:
        fields.append("proposed_changes = %s")
        values.append(json.dumps(proposed_changes))
    if not fields:
        return
    values.append(chat_id)
    with _conn() as conn:
        conn.execute(
            f"UPDATE checkin_state SET {', '.join(fields)} WHERE chat_id = %s",
            values,
        )


def end_checkin(
    chat_id: int,
    *,
    week_number: int,
    schedule: dict,
    transcript: str | None,
    used_fact_id: str | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO checkin_history (week_number, completed_at, schedule_snapshot, transcript, used_fact_id)"
            " VALUES (%s, %s, %s, %s, %s)",
            (week_number, now, json.dumps(schedule), transcript, used_fact_id),
        )
        conn.execute("DELETE FROM checkin_state WHERE chat_id = %s", (chat_id,))


def latest_week_number() -> int:
    with _conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(week_number), 0) AS n FROM checkin_history"
        ).fetchone()
    return int(row["n"]) if row else 0


def recent_fact_ids(limit: int = 8) -> list[str]:
    """Most-recent N used_fact_id values, newest first, NULLs excluded.
    Used by the fact picker to avoid repeats within the recent window."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT used_fact_id FROM checkin_history"
            " WHERE used_fact_id IS NOT NULL"
            " ORDER BY id DESC LIMIT %s",
            (limit,),
        ).fetchall()
    return [r["used_fact_id"] for r in rows]


def get_history_by_week(week_number: int) -> dict | None:
    """Fetch a historical check-in (used by the signed-PDF endpoint to
    re-render a past week's plan from the snapshot)."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT week_number, completed_at, schedule_snapshot, transcript, used_fact_id"
            " FROM checkin_history WHERE week_number = %s ORDER BY id DESC LIMIT 1",
            (week_number,),
        ).fetchone()
    if not row:
        return None
    return dict(row)
