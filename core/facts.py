"""Curated science-fact pool + picker for the weekly newsletter.

Facts live in data/facts.json (hand-seeded from docs/). The picker:
  1. Filters out deload-unsafe facts when this week is a deload.
  2. Filters out facts whose id appears in recent `used_ids` so we don't
     repeat within the last ~N issues.
  3. Scores the remaining pool by tag-match against the transcript.
  4. Returns the highest-scoring fact, breaking ties by stable order.

No LLM, no network. Picker is deterministic given (transcript, deload,
used_ids).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

FACTS_PATH = Path(__file__).resolve().parent.parent / "data" / "facts.json"


@lru_cache(maxsize=1)
def load_facts() -> list[dict]:
    with FACTS_PATH.open() as f:
        return json.load(f)


def pick_fact(
    transcript: str,
    deload: bool,
    used_ids: list[str] | None = None,
) -> dict:
    used_ids = used_ids or []
    pool = load_facts()

    if deload:
        pool = [f for f in pool if f.get("deload_safe", True)]

    # Prefer unused; if every fact has been used recently, fall back to the
    # least-recently-used (= ones earliest in the used_ids list have aged out).
    unused = [f for f in pool if f["id"] not in used_ids]
    candidates = unused or pool

    if not candidates:
        raise RuntimeError("Fact pool is empty — check data/facts.json")

    t = transcript.lower()

    def score(fact: dict) -> int:
        return sum(1 for tag in fact.get("tags", []) if tag.lower() in t)

    # Stable sort: highest score first; ties broken by pool order (which is
    # roughly impact-ordered in facts.json).
    ranked = sorted(
        enumerate(candidates),
        key=lambda item: (-score(item[1]), item[0]),
    )
    return ranked[0][1]
