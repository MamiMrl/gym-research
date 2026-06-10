import os
from datetime import date
from pathlib import Path

import httpx
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

load_dotenv()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
PDFSHIFT_URL = "https://api.pdfshift.io/v3/convert/pdf"

# ── Print layout ───────────────────────────────────────────────────────────
# Printed on A4 landscape, then cut into 4 cards along the grid gaps. Each
# card fits a pocket notebook (max ~140 mm × 200 mm).
# Page dims are consumed by both the PDFShift API call and the CSS @page rule
# via Jinja, so this is the single source of truth — change here only.
PAGE_WIDTH_MM = 297     # A4 long edge (landscape)
PAGE_HEIGHT_MM = 210    # A4 short edge (landscape)
PAGE_MARGIN_MM = 10     # outer page margin (all sides)
GRID_GAP_MM = 6         # gap between cards — also the cut path
TABLE_WIDTH_MM = 134    # workout-card width;  (297 - 2·10 - 6) / 2 = 135, leave 1mm slack
TABLE_HEIGHT_MM = 85    # workout-card height; (210 - 2·10 - 6 - 10 header) / 2 = 87, leave 2mm slack
# ───────────────────────────────────────────────────────────────────────────

_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def render_pdf(plan: dict, output_path: str = "/tmp/plan.pdf") -> str:
    template = _env.get_template("plan.html")
    html_str = template.render(
        week_label=plan["week_label"],
        sessions=plan["sessions"],
        generated_date=date.today().strftime("%d %B %Y"),
        deload=plan.get("deload", False),
        deload_reason=plan.get("deload_reason", ""),
        page_width_mm=PAGE_WIDTH_MM,
        page_height_mm=PAGE_HEIGHT_MM,
        page_margin_mm=PAGE_MARGIN_MM,
        grid_gap_mm=GRID_GAP_MM,
        table_width_mm=TABLE_WIDTH_MM,
        table_height_mm=TABLE_HEIGHT_MM,
    )

    # PDFShift needs the format + orientation explicitly — CSS @page alone is
    # unreliable for orientation (defaults to portrait if format is omitted).
    response = httpx.post(
        PDFSHIFT_URL,
        auth=("api", os.environ["PDFSHIFT_API_KEY"]),
        json={
            "source": html_str,
            "format": "A4",
            "landscape": True,
            "sandbox": False,
        },
        timeout=60,
    )
    if not response.is_success:
        print(response.text)
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
