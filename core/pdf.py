import os
from datetime import date
from pathlib import Path

import httpx
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
PDFSHIFT_URL = "https://api.pdfshift.io/v3/convert/pdf"

_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def render_pdf(plan: dict, output_path: str = "/tmp/plan.pdf") -> str:
    template = _env.get_template("plan.html")
    html_str = template.render(
        week_label=plan["week_label"],
        sessions=plan["sessions"],
        generated_date=date.today().strftime("%d %B %Y"),
    )

    response = httpx.post(
        PDFSHIFT_URL,
        headers={"X-API-Key": os.environ["PDFSHIFT_API_KEY"]},
        json={"source": html_str, "format": "A4"},
        timeout=60,
    )
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path


if __name__ == "__main__":
    import json
    import sys

    schedule_path = Path(__file__).resolve().parent.parent / "config" / "schedule.json"
    with open(schedule_path) as f:
        plan = json.load(f)

    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/plan.pdf"
    path = render_pdf(plan, out)
    print(f"Wrote PDF to {path}")
