import json
from pathlib import Path

SCHEDULE_PATH = Path(__file__).resolve().parent.parent / "config" / "schedule.json"


def load_schedule() -> dict:
    with open(SCHEDULE_PATH) as f:
        return json.load(f)


def save_schedule(plan: dict) -> None:
    with open(SCHEDULE_PATH, "w") as f:
        json.dump(plan, f, indent=2)
        f.write("\n")
