"""Weekly Light Weight newsletter — render + send.

Replaces the old one-line email body. Pulls the picked fact, picked hero
photo, signed CTA URL and structured newsletter context, renders
templates/newsletter.html, attaches the PDF, and ships through Resend
with a plain-text fallback for spam-filter-friendly delivery.
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

import resend
from jinja2 import Environment, FileSystemLoader, select_autoescape

from core import facts, hero, newsletter, signing

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)
_tmpl = _env.get_template("newsletter.html")


def send_newsletter(
    *,
    this_week: dict,
    next_week: dict,
    transcript: str,
    week_number: int,
    used_fact_ids: list[str] | None = None,
    pdf_path: str,
) -> str:
    """Render and send the weekly newsletter. Returns the picked fact_id
    so the caller can persist it in checkin_history (repeat-avoidance)."""
    resend.api_key = os.environ["RESEND_API_KEY"]
    to_addr = os.environ["YOUR_EMAIL"]
    from_addr = os.environ.get("RESEND_FROM", "workout@yourdomain.com")
    base_url = os.environ.get("APP_BASE_URL", "").rstrip("/")

    picked_fact = facts.pick_fact(transcript, bool(next_week.get("deload")), used_fact_ids or [])
    hero_file = hero.pick_hero(week_number)
    hero_dict = None
    if hero_file and base_url:
        hero_dict = {
            "url": f"{base_url}/static/hero/{hero_file}",
            "alt": "Light Weight — weekly hero",
        }

    cta_href = (
        f"{base_url}/plan/{week_number}.pdf?t={signing.sign_week(week_number)}"
        if base_url
        else "#"
    )

    ctx = newsletter.build_context(
        this_week=this_week,
        next_week=next_week,
        transcript=transcript,
        issue_number=week_number,
        fact=picked_fact,
        hero=hero_dict,
        cta_href=cta_href,
    )

    html_body = _tmpl.render(**ctx)
    text_body = _plain_text(ctx)

    with open(pdf_path, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode()
    pdf_name = f"light-weight-week-{week_number}.pdf"

    logger.info(
        "Sending newsletter from=%s to=%s week=%s fact=%s hero=%s",
        from_addr, to_addr, week_number, picked_fact["id"], hero_file,
    )

    resp = resend.Emails.send({
        "from":    from_addr,
        "to":      to_addr,
        "subject": ctx["subject"],
        "html":    html_body,
        "text":    text_body,
        "attachments": [
            {"filename": pdf_name, "content": pdf_b64},
        ],
    })

    email_id = resp.get("id") if isinstance(resp, dict) else getattr(resp, "id", None)
    logger.info("Resend accepted email id=%s to=%s", email_id, to_addr)
    if not email_id:
        raise RuntimeError(f"Resend returned no email ID — possible delivery failure: {resp}")

    return picked_fact["id"]


def _plain_text(ctx: dict) -> str:
    """Minimal plain-text alternative for clients that block HTML.
    Mirrors the newsletter's reading order so the message still flows."""
    lines = [
        f"LIGHT WEIGHT · Issue {ctx['issue_str']} · {ctx['date_str']}",
        "",
    ]
    if ctx["deload"]:
        lines += ["⚠ DELOAD WEEK — same loads, ~50% volume, supercompensate.", ""]

    f = ctx["fact"]
    lines += [
        "SCIENCE",
        f"{f['headline_prefix']}{f['highlight']}{f['headline_suffix']}",
        f"  — {f['citation']}",
        "",
        "WHY IT MATTERS",
        f["why_it_matters"],
        "",
    ]

    r = ctx["recap"]
    lines += [
        "LAST WEEK",
        f"  Sessions: {r['sessions_str']}   "
        f"Load added: {r['kg_added_str']} kg   "
        f"Skipped: {r['skipped_count']}",
        "",
    ]

    lines += ["THIS WEEK"]
    for row in ctx["plan_rows"]:
        deload_note = f"  ({row['deload_note']})" if row["deload_note"] else ""
        lines.append(
            f"  {row['day']:>3}  {row['session']} — {row['top_set_name']} {row['top_set_load']}{deload_note}"
        )
    lines += ["", f"PDF: {ctx['cta']['href']}", "", ctx["footer"]["tagline"]]
    return "\n".join(lines)
