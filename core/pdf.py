from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def render_pdf(plan: dict, output_path: str = "/tmp/plan.pdf") -> str:
    template = _env.get_template("plan.html")
    html_str = template.render(
        week_label=plan["week_label"],
        sessions=plan["sessions"],
        generated_date=date.today().strftime("%d %B %Y"),
    )
    HTML(string=html_str).write_pdf(output_path)
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
