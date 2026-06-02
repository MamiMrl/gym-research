import base64
import os

import resend


def send_plan_email(pdf_path: str, week_label: str) -> dict:
    resend.api_key = os.environ["RESEND_API_KEY"]

    with open(pdf_path, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode()

    safe_label = week_label.replace(" ", "-").replace("/", "-")

    return resend.Emails.send({
        "from":    os.environ.get("RESEND_FROM", "workout@yourdomain.com"),
        "to":      os.environ["YOUR_EMAIL"],
        "subject": f"Week {week_label} — workout plan",
        "html":    f"<p>Your plan for <strong>{week_label}</strong> is attached. Print and go.</p>",
        "attachments": [
            {
                "filename": f"plan-{safe_label}.pdf",
                "content":  pdf_b64,
            }
        ],
    })
