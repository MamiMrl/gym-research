import base64
import logging
import os

import resend

logger = logging.getLogger(__name__)


def send_plan_email(pdf_path: str, week_label: str) -> dict:
    resend.api_key = os.environ["RESEND_API_KEY"]

    to_addr = os.environ["YOUR_EMAIL"]
    from_addr = os.environ.get("RESEND_FROM", "workout@yourdomain.com")

    with open(pdf_path, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode()

    safe_label = week_label.replace(" ", "-").replace("/", "-")

    logger.info("Sending plan email from=%s to=%s week=%s", from_addr, to_addr, week_label)

    resp = resend.Emails.send({
        "from":    from_addr,
        "to":      to_addr,
        "subject": f"Week {week_label} — workout plan",
        "html":    f"<p>Your plan for <strong>{week_label}</strong> is attached. Print and go.</p>",
        "attachments": [
            {
                "filename": f"plan-{safe_label}.pdf",
                "content":  pdf_b64,
            }
        ],
    })

    email_id = resp.get("id") if isinstance(resp, dict) else getattr(resp, "id", None)
    logger.info("Resend accepted email id=%s to=%s", email_id, to_addr)

    if not email_id:
        raise RuntimeError(f"Resend returned no email ID — possible delivery failure: {resp}")

    return resp
