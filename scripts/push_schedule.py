"""Push config/schedule.json to the live `schedule` table (ADR-002).

Use this after manually restructuring the plan (add/drop a session or
exercise). Editing the file alone does nothing at runtime anymore.

Usage:
    python3 scripts/push_schedule.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from bot import state  # noqa: E402
from core.schedule import SEED_PATH  # noqa: E402

with open(SEED_PATH) as f:
    plan = json.load(f)

state.init_db()
current = state.get_schedule()
if current is None:
    print(f"Seeding live plan: {plan.get('week_label')!r}")
else:
    print(
        f"Replacing live plan: {current.get('week_label')!r}"
        f" -> {plan.get('week_label')!r}"
    )
state.set_schedule(plan)
print("Done.")
