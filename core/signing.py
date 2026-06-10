"""HMAC signing for the newsletter's signed-PDF download URL.

The CTA button in each weekly email links to /plan/{week_number}.pdf?t=<token>.
The token is a short HMAC-SHA256 of the week number using CRON_SECRET as the
key. Only the server can produce it; anyone with the link can verify it.

No expiry — old issues stay browsable forever, which is a feature for the
archive use case.
"""

from __future__ import annotations

import hmac
import hashlib
import os

_TOKEN_LEN = 16  # 64 bits of HMAC — plenty for "not enumerable"


def _key() -> bytes:
    secret = os.environ.get("CRON_SECRET")
    if not secret:
        raise RuntimeError("CRON_SECRET is not set — cannot sign newsletter URLs")
    return secret.encode()


def sign_week(week_number: int) -> str:
    return hmac.new(_key(), str(week_number).encode(), hashlib.sha256).hexdigest()[:_TOKEN_LEN]


def verify_week(week_number: int, token: str) -> bool:
    expected = sign_week(week_number)
    return hmac.compare_digest(expected, token or "")
