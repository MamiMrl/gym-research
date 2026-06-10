import json
import logging
import os
from typing import Optional

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ValidationError, Field

from core.prompt import SYSTEM_PROMPT, PLAN_JSON_SCHEMA, build_prompt

log = logging.getLogger(__name__)

GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set")
        _client = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY)
    return _client


class _Exercise(BaseModel):
    name: str
    sets: int
    reps: str
    load_kg: float | None
    note: str = ""
    # Default keeps legacy plans (pre-status) and quiet exercises (not mentioned
    # in the transcript) flowing through validation as "no change reported".
    status: str = "as_planned"


class _Session(BaseModel):
    day: str
    label: str
    exercises: list[_Exercise]


class WeeklyPlan(BaseModel):
    week_label: str
    deload: bool = False
    deload_reason: str | None = None
    sessions: list[_Session] = Field(min_length=1)


def generate_plan(schedule: dict, transcript: str) -> dict:
    """Call the LLM with the planned schedule + voice transcript and return the validated next-week plan as a dict."""
    user_message = build_prompt(schedule, transcript)
    client = _get_client()

    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=4096,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    raw = (resp.choices[0].message.content or "").strip()
    if not raw:
        raise RuntimeError(
            f"LLM returned empty content. finish_reason={resp.choices[0].finish_reason}"
        )

    # Defensive: strip markdown fences if model wraps despite strict mode.
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM returned invalid JSON: {e}\n---\n{raw[:500]}") from e

    try:
        plan = WeeklyPlan.model_validate(data)
    except ValidationError as e:
        raise RuntimeError(f"LLM JSON failed schema validation: {e}") from e

    return plan.model_dump()
