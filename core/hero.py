"""Hero photo picker for the weekly newsletter.

Photos live in assets/hero/ (compressed, 1200x480, 2.5:1 to match the
hi-fi email's 600x240 letterbox slot). Picker rotates deterministically
by issue number so the cycle wraps cleanly with no "used" tracking.

Returns the bare filename — the email caller prepends APP_BASE_URL to
build the absolute https:// URL the rendered email links to.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

HERO_DIR = Path(__file__).resolve().parent.parent / "assets" / "hero"


@lru_cache(maxsize=1)
def _heroes() -> list[str]:
    return sorted(p.name for p in HERO_DIR.glob("*.jpg"))


def pick_hero(issue_number: int) -> str | None:
    """Return e.g. "07.jpg" — or None if the pool is empty."""
    pool = _heroes()
    if not pool:
        return None
    return pool[issue_number % len(pool)]
