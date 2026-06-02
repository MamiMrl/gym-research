import json
import os

import anthropic

from core.prompt import SYSTEM_PROMPT, build_prompt

_client = None

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def generate_plan(schedule: dict, results: dict) -> dict:
    user_message = build_prompt(schedule, results)

    message = _get_client().messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text.strip()
    return json.loads(raw)
