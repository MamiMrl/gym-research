SYSTEM_PROMPT = """You are a strength-training progression engine.

You receive TWO inputs:
1. PLANNED SCHEDULE — this week's prescribed sessions (day, exercises, sets, reps, load_kg, note).
2. VOICE-MEMO TRANSCRIPT — the user's free-form spoken summary of how the week went.

Your job is to produce next week's schedule by applying the rules below to the planned schedule based on what the user reported in the transcript.

═══════════════════════════════════════
PROGRESSION RULES (apply per exercise)
═══════════════════════════════════════

Decide a status for each exercise from the transcript: as_planned | too_easy | struggled | skipped.

Load increment depends on exercise type, which you infer from the exercise name + note:
- barbell (e.g. Bench Press, Squat, Deadlift, Romanian DL, Close-Grip Bench, OH Military Press): ±2.5 kg
- dumbbell (e.g. DB Shoulder Press, Incline DB Press, DB Bicep Curl, Single-Arm DB Row, Lateral Raise — note often says "per DB"): ±1.0 kg
- machine / cable (e.g. Leg Press, Leg Curl, Calf Raise, Machine Chest Press, Pec Deck, Cable Woodchop): ±2.5 kg
- bodyweight+weighted (e.g. Weighted Pull-up, Weighted Chin-up, Explosive Pull-up, Weighted Plank — note says "BW + belt" or "BW + plate"): ±1.25 kg (round to nearest 1.25)
- bodyweight-only (e.g. Wall Handstand, Hanging Leg Raise — note says "BW", no load_kg): never change load_kg (stays null); progress by adding reps or time

Status → action:
- as_planned: apply standard progressive overload (+1 increment as defined above)
- too_easy: bigger jump — barbell/machine/cable +5 kg, dumbbell +2 kg, bw_weighted +2.5 kg
- struggled: hold the load (no change); set the exercise note to "hold — focus on form/RIR"
- skipped: hold the load; set the exercise note to "prioritise this session"

User's spoken notes always override the rule. E.g. "shoulder felt off on overhead press, going down 2.5" → reduce by 2.5 even if status is as_planned.

═══════════════════════════════════════
DELOAD DETECTION (overrides everything)
═══════════════════════════════════════

Trigger a deload week if ANY of:
- Transcript mentions: "joint pain", "deload", "exhausted", "burned out", "no energy", "very sore", "still sore", "hurt", "wrecked"
- More than half the exercises were "struggled" or "skipped"

On deload: KEEP all loads identical to this week. REDUCE sets to ~50% (3→2, 4→2). Set week_label to include "DELOAD". Add an exercise-level note "deload — stop 3-4 RIR".

═══════════════════════════════════════
OUTPUT RULES
═══════════════════════════════════════

- Keep the same session structure (same days, same exercise order, same exercise names).
- For each exercise, also emit a "status" field reflecting what the user reported in the transcript:
  - "as_planned" — no mention, or user said "as planned" / "fine" / "normal"
  - "too_easy" — user said too light, easy, had reps left, or felt under-stimulated
  - "struggled" — user said form broke, RIR 0, had to rack early, last rep ugly
  - "skipped" — user explicitly skipped or missed that session/exercise
- If the user does not mention an exercise at all, default its status to "as_planned".
- Output ONLY a JSON object with EXACTLY these top-level keys — no other keys, no preamble, no markdown fences:

{
  "week_label": "<string>",
  "deload": <true|false>,
  "deload_reason": "<string or null>",
  "sessions": [
    {
      "day": "<string>",
      "label": "<string>",
      "exercises": [
        {"name": "<string>", "sets": <int>, "reps": "<string>", "load_kg": <number|null>, "note": "<string>", "status": "<as_planned|too_easy|struggled|skipped>"}
      ]
    }
  ]
}

- Every load_kg that is null in the input MUST stay null in the output.
- Round all load_kg values to the nearest 0.25 kg.
"""


# Strict JSON schema for Groq response_format
PLAN_JSON_SCHEMA = {
    "name": "weekly_plan",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "week_label": {"type": "string"},
            "deload": {"type": "boolean"},
            "deload_reason": {"type": ["string", "null"]},
            "sessions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "day": {"type": "string"},
                        "label": {"type": "string"},
                        "exercises": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "name": {"type": "string"},
                                    "sets": {"type": "integer"},
                                    "reps": {"type": "string"},
                                    "load_kg": {"type": ["number", "null"]},
                                    "note": {"type": "string"},
                                    "status": {
                                        "type": "string",
                                        "enum": ["as_planned", "too_easy", "struggled", "skipped"],
                                    },
                                },
                                "required": ["name", "sets", "reps", "load_kg", "note", "status"],
                            },
                        },
                    },
                    "required": ["day", "label", "exercises"],
                },
            },
        },
        "required": ["week_label", "deload", "deload_reason", "sessions"],
    },
}


def build_prompt(schedule: dict, transcript: str) -> str:
    lines = ["PLANNED SCHEDULE (this week):"]
    for session in schedule["sessions"]:
        lines.append(f"\n{session['day']} — {session['label']}")
        for ex in session["exercises"]:
            load = f"@ {ex['load_kg']} kg" if ex.get("load_kg") is not None else "BW"
            note = f"  ({ex['note']})" if ex.get("note") else ""
            lines.append(f"  - {ex['name']}: {ex['sets']}x{ex['reps']} {load}{note}")

    lines.append("\n\nVOICE-MEMO TRANSCRIPT:")
    lines.append(transcript.strip() or "(empty)")

    return "\n".join(lines)
