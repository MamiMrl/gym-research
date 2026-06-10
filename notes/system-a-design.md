# System A — Full design docs (RETIRED)

Archived from `CLAUDE.md` on 2026-06-08. System A was retired 2026-06-03.
See `legacy_email/README.md` for the retirement context. Code lives in `legacy_email/`.

---

**Original status:** ✅ Complete & Deployed
**Last Updated:** May 27, 2026
**Deployed Routine ID:** `trig_01XUTpwZgjKkJw6VDq4HpZSh` (now disabled)
**Schedule (historical):** Every Sunday at 8 AM Berlin time (6 AM UTC)

---

## Executive Summary

Fully automated system that managed weekly gym training progression through email. Every Sunday:

1. Checks Gmail for the progress reply from last week
2. Parses input (`MON: + | Felt great`, etc.)
3. Updates the database with new weights and history
4. Detects deload need using science-backed thresholds + the user's own training philosophy
5. Generates next week's HTML (BVB-inspired dark theme, printable to PDF)
6. Sends the new plan via email

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Cloud Scheduled Routine (Sunday 8 AM Berlin)                   │
│  Runs: Claude Agent + Gmail MCP                                 │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ├─ Checks Gmail for your reply
           ├─ Runs: python3 weekly_gym_update.py process --reply "..."
           ├─ Updates: progress_log.json
           ├─ Generates: Workout_Plan_Week_N.html
           └─ Sends: Email with new HTML link + reply template

┌─────────────────────────────────────────────────────────────────┐
│  Local Files (in gym-research/)                                 │
├─────────────────────────────────────────────────────────────────┤
│ • progress_log.json ................ All training data (JSON)   │
│ • weekly_gym_update.py ............. Main logic (900 lines)     │
│ • generate_workout_pdf.py .......... Modified for external data │
│ • Workout_Plan_Week_N.pdf ......... Generated weekly            │
└─────────────────────────────────────────────────────────────────┘
```

## How It Works

### Week 1 (first run)
Routine runs → `is_first_run: true` → `python3 weekly_gym_update.py process` → generates `Workout_Plan_Week_1.html` → emails it with reply template.

### Week 2+
Routine reads Gmail reply → parses `MON: + | comment` format → updates `progress_log.json` (weights only; exercise structure stays identical week-to-week) → increments counters → checks deload conditions → generates `Workout_Plan_Week_N.html` → sends with recap.

### Deload week
Triggered by 6 consecutive progression weeks, fatigue keywords, or 2+ weeks decline → generates plan with same weights but reduced sets (3→2, 4→2, ~50–60% volume) → email banner explains protocol → counters reset after deload.

## The Three Core Files

### 1. `weekly_gym_update.py` — The Brain

CLI:
```bash
python3 weekly_gym_update.py init       # Seed progress_log.json from Week 1
python3 weekly_gym_update.py status     # Print current state JSON
python3 weekly_gym_update.py process                          # First run / no reply
python3 weekly_gym_update.py process --reply "MON: +\n..."    # Process weekly reply
python3 weekly_gym_update.py process --no-reply               # Send reminder, no changes
```

Key functions: `parse_reply`, `update_weights`, `detect_deload`, `update_fatigue_counters`, `apply_deload_to_progress`, `build_week_data`, `generate_pdf`, `build_progress_summary`.

Weight increments:
```python
WEIGHT_INCREMENTS = {
    'barbell':      2.5,
    'dumbbell':     1.0,
    'bw_weighted':  1.25,
    'bw_only':      0.0,
    'skip':         0.0,
    'machine':      2.5,
    'cable_side':   2.5,
}
```

### 2. `generate_workout_pdf.py` — PDF Creator

Originally hardcoded Week 1 data; modified to accept external data:
```python
week_data = build_week_data(progress, is_deload=True)
generator = WorkoutPDFGenerator(output_path)
generator.build_pdf(week_data=week_data, week_num=8, is_deload=True)
```

Title becomes `"Week N — Upper/Lower Split  ⚠ DELOAD WEEK"` when `is_deload=True`. Set reductions apply via `DELOAD_SETS_REDUCTION` mapping.

### 3. `progress_log.json` — The Database

Structure:
- `meta`: `current_week`, `is_first_run`, `last_email_sent_date`, `last_email_subject`
- `deload`: `is_deload_week`, `consecutive_progression_weeks`, `consecutive_no_progress_weeks`, `last_deload_date`, `deload_count_total`, `deload_history`
- `fatigue_tracking`: `consecutive_no_progress_weeks`, `days_consecutive_decline` (per MON/WED/FRI/SAT)
- `exercises`: per-day arrays with `{num, exercise, sets, reps, weight, weight_kg, weight_type, rest, history[]}`
- `week_history`: per-week records with responses, comments, counts, deload flags

**Key insight:** Each exercise stores both `weight` (display string `"70 kg"`) and `weight_kg` (numeric). Separates display from arithmetic.

## Deload Algorithm

Five triggers:
1. **Hard cap:** 6 consecutive progression weeks (research: 4–8 weeks; Schoenfeld 2018 — 8 weeks at high volume approaches overreaching).
2. **Stall:** 3+ weeks with zero `+` responses.
3. **Decline:** 2+ consecutive `-` on the same day.
4. **Fatigue keywords** in comments: `joint pain`, `tired`, `exhausted`, `failed`, `no energy`, `hurt`, `burned out`, `very sore`, `still sore`, `deload`, etc.
5. Otherwise no trigger — counters increment and may trigger next Sunday.

Counters reset after deload (`consecutive_progression_weeks = 0`, `days_consecutive_decline = {...0}`).

## Email Communication

Subject: `Week N Gym Plan — Upper/Lower Split` (or `+ DELOAD WEEK`).
Body includes prior-week recap + this-week plan summary + reply template:
```
MON: [+/-/stay] | [optional comment]
WED: [+/-/stay] | [optional comment]
FRI: [+/-/stay] | [optional comment]
SAT: [+/-/stay] | [optional comment]
```
Attachment: `Workout_Plan_Week_N.pdf`.

## Research Foundation

- **Deload every 4–8 weeks:** Gym-planning.md + Schoenfeld et al. (2016).
- **6-week hard cap:** Schoenfeld et al. (2018) — 8 weeks at high volume approaches non-functional overreaching.
- **Weight increments:** Grgic et al. (2018) — 6+ sets/week per muscle minimum.
- **Deload protocol (same weights, 50–60% volume):** Schoenfeld et al. (2017) — low-load (≤60% 1RM) doesn't sacrifice hypertrophy.
- **Stall definition:** Schoenfeld et al. (2017) — minimum 6-week block to assess progress.
- **Fatigue keywords:** Dupuy et al. (2018) — DOMS resolves 24–72h normally; prolonged DOMS = incomplete recovery. Coffey & Hawley (2017) — accumulated fatigue mechanisms.

## Troubleshooting

**Weights not updating:** Check reply format (`MON: + | comment`). Check `last_email_sent_date` in `progress_log.json`. Manually test with `--reply "MON: + | Test"`.

**Unexpected deload:** Check `consecutive_progression_weeks` (=6?), `consecutive_no_progress_weeks` (=3+?), `days_consecutive_decline` (=2+?), and comments for fatigue keywords.

**PDF not generating:** Check `legacy_outputs/Workout_Plan_Week_N.pdf` exists. Manually run `python3 generate_workout_pdf.py`.

**Routine not running:** Check https://claude.ai/code/routines/trig_01XUTpwZgjKkJw6VDq4HpZSh (currently disabled).

## File Manifest (historical)

```
/Users/neu/Downloads/gym-research/
├── weekly_gym_update.py ........... Main script (900+ lines)
├── generate_workout_html.py ....... HTML generator (BVB design)
├── progress_log.json .............. Training database
├── legacy_outputs/ ................ Generated HTML/PDFs (gitignored)
└── docs/ .......................... Plans + research PDFs
```

## Design Philosophy

- **Consistent week-to-week exercise structure** (Mon/Wed/Fri/Sat never change); only weights adjust.
- **Visual:** HTML with BVB dark theme (black + yellow), printable to PDF. Bebas Neue / Inter / JetBrains Mono.

## Routine Deployment (historical)

- **Routine ID:** `trig_01XUTpwZgjKkJw6VDq4HpZSh`
- **Schedule:** `0 6 * * 0` (Sundays 6 AM UTC = 8 AM Berlin)
- **Environment:** Bridge (Mac) — `env_01Vi3ihUFAehV1rZTWKgkdFP` (env lost 2026-05-31)
- **Model:** Claude Sonnet 4.6
- **MCP:** Gmail
- **Status:** Disabled / retired
