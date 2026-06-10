"""Local smoke-test for the Resend email flow.

Usage:
    python3 scripts/test_email.py

Loads .env, sends a plain-text test email (no PDF) to YOUR_EMAIL,
and prints the full Resend API response so you can see exactly
what the API returns and whether delivery succeeded.
"""

import os
import sys
from pathlib import Path

# Load .env from repo root. Use python-dotenv (already a dep) so quoted
# values are handled correctly — a hand-rolled splitlines parser leaks
# literal "quotes" into env vars and Resend rejects the bogus API key.
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import resend  # noqa: E402

api_key = os.environ.get("RESEND_API_KEY", "")
from_addr = os.environ.get("RESEND_FROM", "onboarding@resend.dev")
to_addr = os.environ.get("YOUR_EMAIL", "")

print(f"  RESEND_API_KEY : {'SET (' + api_key[:8] + '...)' if api_key else 'NOT SET'}")
print(f"  RESEND_FROM    : {from_addr}")
print(f"  YOUR_EMAIL     : {to_addr}")
print()

if not api_key:
    sys.exit("ERROR: RESEND_API_KEY is not set.")
if not to_addr:
    sys.exit("ERROR: YOUR_EMAIL is not set.")

resend.api_key = api_key

print("Sending test email via Resend…")
try:
    resp = resend.Emails.send({
        "from":    from_addr,
        "to":      to_addr,
        "subject": "Gym bot — email delivery test",
        "html":    "<p>This is a delivery test from your gym bot. If you see this, email works.</p>",
    })
    print("Resend response:", resp)
    print()
    if isinstance(resp, dict) and resp.get("id"):
        print(f"SUCCESS — email ID: {resp['id']}")
        print("Check your inbox (and spam folder) for the test email.")
    else:
        print("WARNING: no 'id' in response — something may be wrong.")
        print("Full response above.")
except Exception as exc:
    print(f"EXCEPTION from Resend SDK: {type(exc).__name__}: {exc}")
    print()
    print("Common causes:")
    print("  - onboarding@resend.dev can only deliver to your Resend account email.")
    print("    If YOUR_EMAIL differs from the email you signed up to Resend with,")
    print("    you need to add a custom domain or verify that address in Resend.")
    print("  - Invalid RESEND_API_KEY.")
