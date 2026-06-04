import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone

import httpx

log = logging.getLogger(__name__)

STRAVA_TOKEN_URL = "https://www.strava.com/api/v3/oauth/token"
STRAVA_API_BASE = "https://www.strava.com/api/v3"

# Module-level token cache: {"access_token": str, "expires_at": int (epoch)}
_token_cache: dict = {}


def _client_id() -> str:
    return os.environ["STRAVA_CLIENT_ID"]


def _client_secret() -> str:
    return os.environ["STRAVA_CLIENT_SECRET"]


def _refresh_token() -> str:
    return os.environ["STRAVA_REFRESH_TOKEN"]


def _user_max_hr() -> float | None:
    v = os.environ.get("USER_MAX_HR")
    return float(v) if v else None


def refresh_access_token() -> str:
    """Exchange the long-lived refresh token for a fresh access token. Cached
    until expiry (Strava access tokens last 6 hours)."""
    now = int(time.time())
    if _token_cache.get("access_token") and _token_cache.get("expires_at", 0) > now + 60:
        return _token_cache["access_token"]

    resp = httpx.post(
        STRAVA_TOKEN_URL,
        data={
            "client_id": _client_id(),
            "client_secret": _client_secret(),
            "refresh_token": _refresh_token(),
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = int(data["expires_at"])
    return data["access_token"]


def fetch_recent_activities(days: int = 7) -> list[dict]:
    """Fetch activities from the past `days` days."""
    token = refresh_access_token()
    after = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    resp = httpx.get(
        f"{STRAVA_API_BASE}/athlete/activities",
        headers={"Authorization": f"Bearer {token}"},
        params={"after": after, "per_page": 50},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def persist_activities(conn, activities: list[dict]) -> None:
    """UPSERT into strava_activities. `conn` is an open psycopg connection."""
    for a in activities:
        conn.execute(
            """
            INSERT INTO strava_activities
                (id, type, start_date, distance_m, moving_time_s, avg_hr, max_hr, name, raw)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                type          = EXCLUDED.type,
                start_date    = EXCLUDED.start_date,
                distance_m    = EXCLUDED.distance_m,
                moving_time_s = EXCLUDED.moving_time_s,
                avg_hr        = EXCLUDED.avg_hr,
                max_hr        = EXCLUDED.max_hr,
                name          = EXCLUDED.name,
                raw           = EXCLUDED.raw,
                fetched_at    = NOW()
            """,
            (
                a["id"],
                a.get("type"),
                a.get("start_date"),
                a.get("distance"),
                a.get("moving_time"),
                a.get("average_heartrate"),
                a.get("max_heartrate"),
                a.get("name"),
                json.dumps(a),
            ),
        )


def summarize(activities: list[dict], user_max_hr: float | None = None) -> dict:
    """Produce a digest for the LLM prompt and the confirmation card."""
    if user_max_hr is None:
        user_max_hr = _user_max_hr()

    total_distance_m = sum(a.get("distance") or 0 for a in activities)
    total_moving_s = sum(a.get("moving_time") or 0 for a in activities)

    digest_activities = []
    hr_flags: list[str] = []

    for a in activities:
        max_hr = a.get("max_heartrate")
        avg_hr = a.get("average_heartrate")
        digest_activities.append({
            "start_date": a.get("start_date", ""),
            "type": a.get("type", ""),
            "name": a.get("name", ""),
            "distance_km": (a.get("distance") or 0) / 1000.0,
            "moving_time_min": int((a.get("moving_time") or 0) / 60),
            "avg_hr": avg_hr,
            "max_hr": max_hr,
        })

        if user_max_hr and max_hr:
            pct = max_hr / user_max_hr
            if pct >= 0.95:
                hr_flags.append(
                    f"{a.get('name', a.get('type', 'activity'))} "
                    f"{a.get('start_date', '')[:10]}: max HR {int(max_hr)} "
                    f"({int(pct*100)}% of max {int(user_max_hr)}) — high CNS load"
                )

    return {
        "count": len(activities),
        "total_distance_km": round(total_distance_m / 1000.0, 1),
        "total_moving_time_min": int(total_moving_s / 60),
        "user_max_hr": user_max_hr,
        "activities": digest_activities,
        "hr_flags": hr_flags,
    }
