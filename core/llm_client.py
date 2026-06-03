import json
import logging
import os
from typing import Optional

from openai import OpenAI, OpenAIError

from core.prompt import SYSTEM_PROMPT, build_prompt

log = logging.getLogger(__name__)

PRIMARY_BASE_URL = os.environ.get("OSS_BASE_URL")
PRIMARY_API_KEY = os.environ.get("OSS_API_KEY")
PRIMARY_MODEL = os.environ.get("OSS_MODEL", "openai/gpt-oss-20b")

GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")

PRIMARY_TIMEOUT_S = float(os.environ.get("OSS_TIMEOUT_S", "60"))

_primary: Optional[OpenAI] = None
_fallback: Optional[OpenAI] = None


def _get_primary() -> Optional[OpenAI]:
    global _primary
    if _primary is None and PRIMARY_BASE_URL and PRIMARY_API_KEY:
        _primary = OpenAI(
            base_url=PRIMARY_BASE_URL,
            api_key=PRIMARY_API_KEY,
            timeout=PRIMARY_TIMEOUT_S,
        )
    return _primary


def _get_fallback() -> Optional[OpenAI]:
    global _fallback
    if _fallback is None and GROQ_API_KEY:
        _fallback = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY)
    return _fallback


def _call(client: OpenAI, model: str, user_message: str) -> dict:
    resp = client.chat.completions.create(
        model=model,
        max_tokens=2048,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    raw = (resp.choices[0].message.content or "").strip()
    # Strip markdown fences if the model wraps the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def generate_plan(schedule: dict, results: dict) -> dict:
    user_message = build_prompt(schedule, results)

    primary = _get_primary()
    if primary is not None:
        try:
            return _call(primary, PRIMARY_MODEL, user_message)
        except (OpenAIError, json.JSONDecodeError, ValueError) as e:
            log.warning("Primary gpt-oss endpoint failed (%s); falling back to Groq", e)

    fallback = _get_fallback()
    if fallback is None:
        raise RuntimeError(
            "No LLM available: set OSS_BASE_URL+OSS_API_KEY (primary) "
            "or GROQ_API_KEY (fallback)."
        )
    return _call(fallback, GROQ_MODEL, user_message)
