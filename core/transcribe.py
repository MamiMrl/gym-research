import io
import logging
import os
from typing import Optional

from openai import OpenAI

log = logging.getLogger(__name__)

GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
WHISPER_MODEL = os.environ.get("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set")
        _client = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY)
    return _client


def transcribe(audio_bytes: bytes, filename: str = "voice.ogg") -> str:
    """Transcribe an audio clip via Groq Whisper. Returns plain text.

    Telegram voice memos are .oga (Ogg Opus). Whisper accepts ogg/m4a/mp3/wav.
    Language is auto-detected.
    """
    client = _get_client()
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename  # SDK uses .name to infer mime

    resp = client.audio.transcriptions.create(
        model=WHISPER_MODEL,
        file=audio_file,
        response_format="text",
    )
    # response_format=text returns a string directly
    if isinstance(resp, str):
        return resp.strip()
    # Defensive: some SDK versions return an object with .text
    return (getattr(resp, "text", "") or "").strip()
