SYSTEM_PROMPT = """You are a strength-training progression engine.

You receive THREE inputs:
1. PLANNED SCHEDULE — this week's prescribed sessions (day, exercises, sets, reps, load_kg, note).
2. VOICE-MEMO TRANSCRIPT — the user's free-form spoken summary of how the week went.
3. STRAVA SUMMARY (optional) — cardio activity context from the past 7 days.

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
- Strava summary shows sustained max HR > 95% of user max for multiple sessions (sign of CNS load)
- More than half the exercises were "struggled" or "skipped"

On deload: KEEP all loads identical to this week. REDUCE sets to ~50% (3→2, 4→2). Set week_label to include "DELOAD". Add an exercise-level note "deload — stop 3-4 RIR".

═══════════════════════════════════════
OUTPUT RULES
═══════════════════════════════════════

- Keep the same session structure (same days, same exercise order, same exercise names).
- Output ONLY the JSON object matching the response schema. No preamble. No markdown fences.
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
                                },
                                "required": ["name", "sets", "reps", "load_kg", "note"],
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


def build_prompt(schedule: dict, transcript: str, strava_summary: dict | None = None) -> str:
    lines = ["PLANNED SCHEDULE (this week):"]
    for session in schedule["sessions"]:
        lines.append(f"\n{session['day']} — {session['label']}")
        for ex in session["exercises"]:
            load = f"@ {ex['load_kg']} kg" if ex.get("load_kg") is not None else "BW"
            note = f"  ({ex['note']})" if ex.get("note") else ""
            lines.append(f"  - {ex['name']}: {ex['sets']}x{ex['reps']} {load}{note}")

    lines.append("\n\nVOICE-MEMO TRANSCRIPT:")
    lines.append(transcript.strip() or "(empty)")

    if strava_summary:
        lines.append("\n\nSTRAVA SUMMARY (past 7 days):")
        lines.append(
            f"  {strava_summary.get('count', 0)} activities, "
            f"{strava_summary.get('total_distance_km', 0):.1f} km total, "
            f"{strava_summary.get('total_moving_time_min', 0)} min moving."
        )
        for a in strava_summary.get("activities", []):
            lines.append(
                f"  - {a.get('start_date', '')[:10]} {a.get('type', '')}: "
                f"{a.get('distance_km', 0):.1f} km, "
                f"avg HR {a.get('avg_hr') or '–'}, max HR {a.get('max_hr') or '–'}"
            )
        flags = strava_summary.get("hr_flags") or []
        if flags:
            lines.append("  HR flags:")
            for f in flags:
                lines.append(f"    ⚠ {f}")

    return "\n".join(lines)
