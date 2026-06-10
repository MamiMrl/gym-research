"""Newsletter context builder.

Turns (this_week, next_week, transcript, issue_number, fact, hero, cta_href)
into the flat dict that `templates/newsletter.html` consumes. The template
is intentionally dumb — every piece of copy or formatting lives here.

See IMPLEMENTATION-newsletter.md for the full schema and rationale.
"""

from __future__ import annotations

from datetime import date

ACCENT = "#FDE100"
BRAND_NAME = "LIGHT WEIGHT"


def build_context(
    *,
    this_week: dict,
    next_week: dict,
    transcript: str,
    issue_number: int,
    fact: dict,
    hero: dict | None = None,
    cta_href: str,
    today: date | None = None,
) -> dict:
    today = today or date.today()
    deload = bool(next_week.get("deload"))

    return {
        "issue_number": issue_number,
        "issue_str": f"{issue_number:03d}",
        "date_str": _date_str(today),
        "week_label": next_week.get("week_label", ""),
        "deload": deload,
        "deload_reason": next_week.get("deload_reason"),
        "accent": ACCENT,
        "name": BRAND_NAME,

        "show_hero": hero is not None,
        "hero_image_url": (hero or {}).get("url"),
        "hero_alt": (hero or {}).get("alt", "Light Weight weekly hero"),

        "fact": _fact_block(fact),
        "recap": _recap(this_week, next_week, deload),
        "plan_rows": _plan_rows(next_week, deload),

        "cta": {
            "href": cta_href,
            "label_main": "DOWNLOAD THIS WEEK'S PLAN",
            "label_sub": "PDF · A4 · print & glue into your notebook",
        },
        "footer": {
            "tagline": (
                "Reply with a voice memo telling me how each session went — "
                "next Sunday's plan adjusts your loads automatically."
            ),
        },

        "subject": _subject(issue_number, deload, fact),
        "preheader": _preheader(deload, fact),
    }


# ── formatting helpers ────────────────────────────────────────────────────

def _date_str(d: date) -> str:
    # "SUN · JUN 9" — matches the design preheader.
    return d.strftime("%a · %b %-d").upper()


def _format_load(load_kg: float | None) -> str:
    if load_kg is None:
        return "BW"
    if load_kg == int(load_kg):
        return f"{int(load_kg)} kg"
    return f"{load_kg:g} kg"


def _day_short(day: str) -> str:
    return day[:3].upper()


# ── top set + plan rows ───────────────────────────────────────────────────

def _top_set(exercises: list[dict]) -> tuple[str, str]:
    """Pick the heaviest loaded exercise as the 'top set' for a session.
    Falls back to the first exercise (and BW) if nothing is loaded."""
    weighted = [e for e in exercises if e.get("load_kg") is not None]
    if not weighted:
        first = exercises[0]
        return first["name"], "BW"
    heaviest = max(weighted, key=lambda x: x["load_kg"])
    return heaviest["name"], _format_load(heaviest["load_kg"])


def _plan_rows(plan: dict, deload: bool) -> list[dict]:
    rows = []
    for s in plan.get("sessions", []):
        name, load = _top_set(s["exercises"])
        rows.append({
            "day": _day_short(s["day"]),
            "session": s["label"],
            "top_set_name": name,
            "top_set_load": load,
            "deload_note": "↓ ½ sets" if deload else None,
        })
    return rows


# ── recap (sessions, +kg, skipped, biggest jump) ──────────────────────────

def _match_pairs(this_week: dict, next_week: dict):
    """Yield (this_ex, next_ex) for every exercise matched by (day, name)."""
    nxt_idx = {
        (s["day"], e["name"]): e
        for s in next_week.get("sessions", [])
        for e in s["exercises"]
    }
    for s in this_week.get("sessions", []):
        for e in s["exercises"]:
            key = (s["day"], e["name"])
            if key in nxt_idx:
                yield e, nxt_idx[key]


def _recap(this_week: dict, next_week: dict, deload: bool) -> dict:
    sessions_planned = len(this_week.get("sessions", []))

    # A session counts as "done" unless every exercise in next_week is marked skipped.
    sessions_done = 0
    skipped_count = 0
    for s in next_week.get("sessions", []):
        statuses = [e.get("status", "as_planned") for e in s["exercises"]]
        skipped_count += sum(1 for x in statuses if x == "skipped")
        if any(x != "skipped" for x in statuses):
            sessions_done += 1

    # +kg added: sum positive deltas. Biggest jump: argmax delta.
    kg_added = 0.0
    biggest_jump: tuple[str, float] | None = None
    biggest_delta = 0.0
    for prev, nxt in _match_pairs(this_week, next_week):
        p, n = prev.get("load_kg"), nxt.get("load_kg")
        if p is None or n is None:
            continue
        delta = n - p
        if delta > 0:
            kg_added += delta
        if delta > biggest_delta:
            biggest_delta = delta
            biggest_jump = (nxt["name"], n)

    highlight = _highlight_line(deload, biggest_jump)

    return {
        "sessions_done": sessions_done,
        "sessions_planned": sessions_planned,
        "sessions_str": f"{sessions_done}/{sessions_planned}",
        "kg_added": kg_added,
        "kg_added_str": _format_kg_added(kg_added),
        "skipped_count": skipped_count,
        "highlight_html": highlight,
    }


def _format_kg_added(kg: float) -> str:
    if kg <= 0:
        return "0"
    if kg == int(kg):
        return f"+{int(kg)}"
    return f"+{kg:g}"


def _highlight_line(deload: bool, biggest_jump: tuple[str, float] | None) -> str:
    if deload:
        return (
            "Six straight weeks of progression in the log. That earned this "
            "deload — recover like it's part of the program, because it is."
        )
    if biggest_jump:
        name, load = biggest_jump
        return (
            f"Biggest jump: <strong>{name} → {_format_load(load)}</strong>. "
            "Momentum's real — keep the form tight."
        )
    return "Steady week. Same loads, same tempo — boring is the goal."


# ── fact block ────────────────────────────────────────────────────────────

def _fact_block(fact: dict) -> dict:
    return {
        "id": fact["id"],
        "headline_prefix": fact["headline_prefix"],
        "highlight": fact["highlight"],
        "headline_suffix": fact["headline_suffix"],
        "citation": fact["citation"],
        "why_it_matters": fact["why_it_matters"],
    }


# ── subject + preheader ───────────────────────────────────────────────────

def _subject(issue_number: int, deload: bool, fact: dict) -> str:
    if deload:
        return f"Light Weight · Issue {issue_number} — Deload week, back off to grow"
    return f"Light Weight · Issue {issue_number} — {fact['highlight']} beats the alternative"


def _preheader(deload: bool, fact: dict) -> str:
    if deload:
        return "Same loads · half the volume · supercompensate, don't grind."
    return f"{fact['headline_prefix']}{fact['highlight']}{fact['headline_suffix']}"
