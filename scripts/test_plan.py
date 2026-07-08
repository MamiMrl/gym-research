"""Local smoke-test for plan generation — no Telegram or Vercel needed.

Usage:
    python3 scripts/test_plan.py
    python3 scripts/test_plan.py "bench press felt easy, squat was hard"
"""
import json
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from core.llm_client import generate_plan
from core.schedule import SEED_PATH

DEFAULT_TRANSCRIPT = (
    "Everything went as planned this week. Bench press felt solid at 70 kg. "
    "Squat was tough, keep the weight the same. Deadlift was fine."
)

transcript = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TRANSCRIPT

# Seed file, not the live DB plan — this smoke-tests the LLM plumbing and
# must stay runnable without DATABASE_URL (Neon vars are Sensitive in Vercel
# and can't be pulled locally).
print("Loading schedule (seed file)…")
with open(SEED_PATH) as f:
    schedule = json.load(f)

print(f"Transcript: {transcript}\n")
print("Calling LLM…")
plan = generate_plan(schedule, transcript)

print("\n--- Result ---")
print(json.dumps(plan, indent=2))
