"""Local smoke-test for the Light Weight weekly newsletter.

Usage:
    python3 scripts/test_newsletter.py                 # render to /tmp + open in browser
    python3 scripts/test_newsletter.py --deload        # render the deload variant
    python3 scripts/test_newsletter.py --issue 17      # pick a specific issue number (affects hero rotation)
    python3 scripts/test_newsletter.py --no-hero       # render with show_hero=false
    python3 scripts/test_newsletter.py --send          # actually send via Resend to YOUR_EMAIL
    python3 scripts/test_newsletter.py --send --deload # send the deload variant for real

Synthesises a "this week" from config/schedule.json and a "next week"
that mutates a few loads + a skipped exercise, so the recap stats
read sensibly. Uses the real fact picker, real hero picker, real
Jinja render, real plain-text fallback — same code path as the
production Sunday send, minus the Telegram trigger.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

# Load .env so APP_BASE_URL, CRON_SECRET, RESEND_API_KEY etc. flow through.
ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

# Make `core` and `templates` importable when run from anywhere.
sys.path.insert(0, str(ROOT))

from jinja2 import Environment, FileSystemLoader, select_autoescape  # noqa: E402

from core import facts, hero, newsletter, signing  # noqa: E402
from core.email import _plain_text  # noqa: E402


def _synthesise_next_week(this_week: dict, deload: bool) -> dict:
    nxt = json.loads(json.dumps(this_week))
    nxt["week_label"] = "DELOAD week" if deload else "Week N+1 — Upper/Lower"
    nxt["deload"] = deload
    nxt["deload_reason"] = "Six weeks of progression + sleep poor." if deload else None
    for s in nxt["sessions"]:
        for e in s["exercises"]:
            e["status"] = "as_planned"
            if not deload:
                if e["name"] == "Bench Press":
                    e["load_kg"] = 72.5
                if e["name"] == "Barbell Squat":
                    e["load_kg"] = 92.5
                if e["name"] == "Pec Deck":
                    e["status"] = "skipped"
            else:
                # Deload mirrors current loads, halves sets.
                e["sets"] = max(1, e["sets"] // 2)
    return nxt


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--deload", action="store_true", help="Render the deload variant.")
    p.add_argument("--no-hero", action="store_true", help="Hide the hero photo.")
    p.add_argument("--issue", type=int, default=14, help="Issue number (controls hero rotation + CTA token).")
    p.add_argument("--send", action="store_true", help="Actually send via Resend to YOUR_EMAIL.")
    args = p.parse_args()

    base_url = os.environ.get("APP_BASE_URL", "").rstrip("/")
    if args.send and not base_url:
        print("WARNING: APP_BASE_URL not set — hero img and CTA href will be broken in the sent email.", file=sys.stderr)

    this_week = json.loads((ROOT / "config" / "schedule.json").read_text())
    next_week = _synthesise_next_week(this_week, args.deload)

    transcript = (
        "Knees sore, slept badly all week, deload time."
        if args.deload
        else "Bench felt easy, squat smooth. Skipped pec deck — shoulder pinched."
    )

    picked = facts.pick_fact(transcript, deload=args.deload, used_ids=[])
    hero_file = hero.pick_hero(args.issue)

    # For local browser preview, fall back to file:// so the hero loads
    # without a deployed server. When --send is used, prefer the real
    # https URL since email clients can't open file:// URLs.
    if args.no_hero:
        hero_dict = None
    elif args.send and base_url:
        hero_dict = {"url": f"{base_url}/static/hero/{hero_file}", "alt": "Light Weight weekly hero"}
    else:
        hero_dict = {"url": f"file://{(ROOT / 'assets' / 'hero' / hero_file).resolve()}", "alt": "Light Weight weekly hero"}

    cta_href = (
        f"{base_url}/plan/{args.issue}.pdf?t={signing.sign_week(args.issue)}"
        if base_url
        else "#"
    )

    ctx = newsletter.build_context(
        this_week=this_week,
        next_week=next_week,
        transcript=transcript,
        issue_number=args.issue,
        fact=picked,
        hero=hero_dict,
        cta_href=cta_href,
        today=date.today(),
    )

    env = Environment(loader=FileSystemLoader(str(ROOT / "templates")), autoescape=select_autoescape(["html"]))
    tmpl = env.get_template("newsletter.html")
    html = tmpl.render(**ctx)
    text = _plain_text(ctx)

    out_html = Path("/tmp/newsletter.html")
    out_text = Path("/tmp/newsletter.txt")
    out_html.write_text(html)
    out_text.write_text(text)

    print(f"  Issue     : {ctx['issue_str']}  ·  {ctx['date_str']}")
    print(f"  Subject   : {ctx['subject']}")
    print(f"  Preheader : {ctx['preheader']}")
    print(f"  Fact      : {picked['id']}")
    print(f"  Hero      : {hero_file if hero_dict else '(hidden)'}")
    print(f"  CTA       : {cta_href}")
    print(f"  HTML      : {out_html}  ({out_html.stat().st_size} bytes)")
    print(f"  TXT       : {out_text}  ({out_text.stat().st_size} bytes)")

    if not args.send:
        # Open the rendered HTML in the default browser on macOS.
        if sys.platform == "darwin":
            subprocess.run(["open", str(out_html)], check=False)
        print("\nDry-run only. Pass --send to actually deliver via Resend.")
        return

    api_key = os.environ.get("RESEND_API_KEY", "")
    from_addr = os.environ.get("RESEND_FROM", "onboarding@resend.dev")
    to_addr = os.environ.get("YOUR_EMAIL", "")
    if not api_key or not to_addr:
        sys.exit("ERROR: RESEND_API_KEY / YOUR_EMAIL must be set in .env to use --send.")

    import resend  # local import so dry-runs don't need the package installed
    resend.api_key = api_key

    print(f"\nSending to {to_addr} from {from_addr}…")
    resp = resend.Emails.send({
        "from":    from_addr,
        "to":      to_addr,
        "subject": ctx["subject"] + " (test)",
        "html":    html,
        "text":    text,
        # PDF attachment intentionally omitted — this script renders the
        # email layout, not the full Confirm flow. Use the actual bot
        # /confirm path or trigger the Vercel cron for the full PDF send.
    })
    email_id = resp.get("id") if isinstance(resp, dict) else getattr(resp, "id", None)
    print(f"Resend accepted email id={email_id}")
    if not email_id:
        sys.exit(f"WARNING: no email ID in response — full response: {resp}")


if __name__ == "__main__":
    main()
