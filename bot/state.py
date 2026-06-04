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
                strava_summary   JSONB,
                started_at       TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkin_history (
                id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                week_number       INTEGER NOT NULL,
                completed_at      TEXT NOT NULL,
                schedule_snapshot JSONB NOT NULL,
                transcript        TEXT,
                strava_summary    JSONB
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS strava_activities (
                id              BIGINT PRIMARY KEY,
                type            TEXT,
                start_date      TIMESTAMPTZ,
                distance_m      REAL,
                moving_time_s   INTEGER,
                avg_hr          REAL,
                max_hr          REAL,
                name            TEXT,
                raw             JSONB,
                fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)


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
        "strava_summary": row["strava_summary"],
        "started_at": row["started_at"],
    }


def set_state(
    chat_id: int,
    *,
    voice_file_id: str | None = None,
    transcript: str | None = None,
    proposed_changes: dict | None = None,
    strava_summary: dict | None = None,
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
    if strava_summary is not None:
        fields.append("strava_summary = %s")
        values.append(json.dumps(strava_summary))
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
    strava_summary: dict | None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO checkin_history (week_number, completed_at, schedule_snapshot, transcript, strava_summary)"
            " VALUES (%s, %s, %s, %s, %s)",
            (
                week_number,
                now,
                json.dumps(schedule),
                transcript,
                json.dumps(strava_summary) if strava_summary else None,
            ),
        )
        conn.execute("DELETE FROM checkin_state WHERE chat_id = %s", (chat_id,))


def latest_week_number() -> int:
    with _conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(week_number), 0) AS n FROM checkin_history"
        ).fetchone()
    return int(row["n"]) if row else 0
