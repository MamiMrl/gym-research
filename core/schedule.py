"""Live-plan accessor. The plan lives in the Postgres `schedule` table
(ADR-002); config/schedule.json is only the bootstrap seed."""
import json
from pathlib import Path

from bot import state

SEED_PATH = Path(__file__).resolve().parent.parent / "config" / "schedule.json"


def load_schedule() -> dict:
    plan = state.get_schedule()
    if plan is not None:
        return plan
    # First read after migration: prefer the newest archived snapshot — the
    # real progression only survived there while the file write was ephemeral
    # on Vercel. The seed file is the fresh-install fallback.
    plan = state.latest_schedule_snapshot()
    if plan is None:
        with open(SEED_PATH) as f:
            plan = json.load(f)
    state.set_schedule(plan)
    return plan


def save_schedule(plan: dict) -> None:
    state.set_schedule(plan)
