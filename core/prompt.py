SYSTEM_PROMPT = """You are a personal strength training coach.
Given the user's completed weekly schedule and their check-in results,
generate an adjusted plan for next week.

Rules:
- If status is "too_easy": increase load by 2.5-5 kg, or add a rep
- If status is "struggled": keep load the same, or reduce by 2.5 kg if noted as a form issue
- If status is "skipped": keep planned load, add a note to prioritise
- If status is "as_planned": apply standard progressive overload (+2.5 kg or +1 rep)
- Respect the user's own notes - they override the default rules
- Keep the same session structure (days, exercise order)
- Return ONLY valid JSON. No preamble, no markdown fences.

Output schema:
{
  "week_label": "string",
  "sessions": [
    {
      "day": "string",
      "label": "string",
      "exercises": [
        {
          "name": "string",
          "sets": number,
          "reps": number,
          "load_kg": number | null,
          "note": "string"
        }
      ]
    }
  ]
}"""


def build_prompt(schedule: dict, results: dict) -> str:
    lines = ["PLANNED SCHEDULE (this week):"]
    for session in schedule["sessions"]:
        lines.append(f"\n{session['day']} - {session['label']}")
        for ex in session["exercises"]:
            load = f"@ {ex['load_kg']} kg" if ex.get("load_kg") else ex.get("note", "")
            lines.append(f"  - {ex['name']}: {ex['sets']}x{ex['reps']} {load}")

    lines.append("\nCHECK-IN RESULTS:")
    for day, exercises in results.items():
        lines.append(f"\n{day}")
        for name, data in exercises.items():
            note_str = f' - "{data["note"]}"' if data.get("note") else ""
            lines.append(f"  - {name}: {data['status']}{note_str}")

    return "\n".join(lines)
