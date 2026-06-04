# Gym Tracking — Project Status

> Read this header and `README.md` before doing any work. `README.md` is the canonical onboarding doc for collaborators; this file is the deeper status log + System A design appendix.

## Directory layout (refreshed 2026-06-04)

```
.
├── README.md                  Collaborator onboarding (start here)
├── CLAUDE.md                  This file — status + System A design appendix
│
├── # System B — Telegram bot (Vercel deploy target)
├── main.py, requirements.txt, Dockerfile, Procfile, railway.json, vercel.json
├── bot/, core/, config/, templates/, .github/
│
├── legacy_email/              System A — retired 2026-06-03, archived for reference
│   ├── README.md              Retirement note + how it worked
│   ├── weekly_gym_update.py, generate_workout_html.py, generate_workout_pdf.py
│   ├── progress_log.json, routine_agent.md
│   └── outputs/               Generated HTML/PDF (gitignored)
│
└── docs/                      Training plans + scientific references
    ├── personal-workout-plan.{md,html,pdf}
    ├── Gym-planning.md, golden-encyklopedia-building-muscle.md, injury-recovery.md
    └── research/              Source PDFs (gitignored)
```

## System A: Email-based tracker (RETIRED 2026-06-03)

**Status:** ☠ Retired. Routine `trig_01XUTpwZgjKkJw6VDq4HpZSh` is permanently disabled (renamed `Weekly Gym Progress Update (RETIRED 2026-06-03)`; its original Mac Bridge environment was lost on 2026-05-31, and we superseded it with System B rather than rebuilding).
**Code:** moved to `legacy_email/`, hardcoded `/Users/neu/Downloads/gym-research/` paths rewritten to be relative to the folder so the scripts still run locally.
**Flow (historical):** Gmail reply → script parses `MON: + / WED: stay / …` → updates weights → emails next week's HTML
**Docs:** `legacy_email/README.md` for the retirement context; full algorithm + design notes below in this file (sections starting at "Executive Summary").

## System B: Telegram-bot tracker (NEW — being built)

**Status:** 🟡 Deployed on Vercel, **Telegram webhook registration pending** (last touched 2026-06-04)
**Trigger:** Vercel cron (`vercel.json`, `0 8 * * 0`) → GET `/trigger` → Telegram conversation → Submit → LLM → PDF → Resend email
**PDF:** PDFShift managed API (`core/pdf.py`) — renders Jinja2 HTML template, no system libs required
**State:** Neon Postgres (`bot/state.py`, `psycopg` v3) — `checkin_state` + `checkin_history` tables, `DATABASE_URL` injected by Vercel–Neon integration
**LLM:** `openai/gpt-oss-20b` on Groq. See `core/llm_client.py`.
**Code:** `main.py`, `bot/`, `core/`, `config/schedule.json`, `templates/plan.html`, `vercel.json`
**Docs:** See `README.md` for env vars, deploy steps, conversation flow, and LLM fallback notes.

### Session history

**2026-06-02:** Built steps 6–10 of the original plan — PDF renderer, Resend email, FastAPI webhook server, bot conversation loop, Anthropic-backed LLM client, Dockerfile + Railway config, GitHub Actions cron, first README. All modules `py_compile`-clean. First commit (`557331e`).

**2026-06-03 (morning):**
- Swapped Anthropic for OpenAI-compatible gpt-oss-20b client with Groq fallback (`core/llm_client.py` replaces `core/claude_client.py`). Verified Groq model ID `openai/gpt-oss-20b` against [Groq docs](https://console.groq.com/docs/model/openai/gpt-oss-20b).
- Reorganized the repo root: 11 research PDFs → `docs/research/`, 5 reference markdown/HTML files → `docs/`.
- Discovered System A's cloud routine was already auto-disabled (env lost) — **retired System A entirely**: moved source into `legacy_email/` (with hardcoded paths rewritten relative), renamed the dead routine to `(RETIRED 2026-06-03)`, replaced its prompt with a do-not-resurrect note.
- Wired `GROQ_API_KEY` into `.env`. Primary `OSS_*` left unset — Groq is the sole LLM provider for now.
- Rewrote `README.md` as the canonical collaborator entry point and refreshed this file.

**2026-06-03 (continued):**
- Added `RESEND_API_KEY`, `RESEND_FROM` (`onboarding@resend.dev` sandbox), and `YOUR_EMAIL` (`mami.maral@icloud.com`) to `.env`. All required env vars are now set.
- Local PDF smoke-test passed: Homebrew Python `.venv` + WeasyPrint rendered correctly.
- Seeded `config/schedule.json` with the real Upper/Lower routine (Mon/Wed/Fri/Sat). Weights reflect current working loads as of this date.
- Schedule changes vs. `docs/personal-workout-plan.md` Week 1: DB Shoulder Press 15 kg, Explosive Pull-up BW+5, DB Bicep Curl 11 kg (increased from 10 kg). Hack Squat removed from Saturday, replaced with Cable Woodchop (high-to-low, 3×12/side @ 12.5 kg) for oblique work — the original plan had no rotational/anti-rotation core exercise.
- Deployed to Railway: fixed `${PORT}` expansion bug (`railway.json` startCommand bypassed shell; removed it so Dockerfile CMD runs instead). Telegram webhook registered successfully.
- **Railway abandoned** — free credits ($5) exhausted by repeated healthcheck retries during failed deploys.
- Fixed LLM JSON parsing: Groq's `json_object` response_format returned empty `failed_generation` in production. Removed `response_format` entirely; system prompt already enforces JSON output; client now strips markdown fences defensively (`core/llm_client.py`).

**2026-06-04:**
- Platform decision: **Vercel** (replaces both Railway and Fly.io). Serverless Python ASGI, native FastAPI support, built-in cron, free Hobby tier.
- Researched Vercel constraints (official docs). Two hard blockers resolved:
  1. **WeasyPrint incompatible** — replaced `core/pdf.py` with PDFShift API (`httpx.post` to `https://api.pdfshift.io/v3/convert/pdf`, `X-API-Key` header, `{"source": html_str, "format": "A4"}` body). Jinja2 template rendering unchanged. `PDFSHIFT_API_KEY` added to Vercel secrets.
  2. **SQLite ephemeral on serverless** — replaced `bot/state.py` with Neon Postgres via `psycopg` v3. Schema: `JSONB` columns for `results`/`schedule_snapshot`, `GENERATED ALWAYS AS IDENTITY` for auto-increment. `DATABASE_URL` injected by Vercel–Neon integration. All function signatures unchanged — `handlers.py` required no edits.
- `main.py` refactored for serverless: removed FastAPI `lifespan=` (Vercel's shutdown window is 500ms — too short for PTB teardown); replaced with `async with ptb_app:` per-invocation (PTB's official serverless pattern). PTB object renamed from `application` → `ptb_app` to avoid Vercel ASGI entrypoint collision (Vercel scans for `app` or `application`). `/trigger` changed from POST → GET; `TRIGGER_SECRET` → `CRON_SECRET`.
- `vercel.json` created: cron `0 8 * * 0` → GET `/trigger`.
- Vercel project `gym-research` created (Hobby, `MamiMrl/gym-research`, FastAPI preset). All secrets set via dashboard. Neon integration `neon-cyan-nest` connected (Vercel Marketplace → Native Integrations).
- First deploy failed: entrypoint collision (`main:application` was PTB object, not ASGI). Fixed by renaming to `ptb_app` (commit `b1b3ac0`). Redeploy in progress.

### What's left to do for System B

**Vercel secrets status (2026-06-04):** All required keys set in Vercel dashboard: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GROQ_API_KEY`, `GROQ_MODEL`, `CRON_SECRET`, `RESEND_API_KEY`, `RESEND_FROM` (`onboarding@resend.dev`), `YOUR_EMAIL` (`mami.maral@icloud.com`), `PDFSHIFT_API_KEY`. `DATABASE_URL` injected by Neon integration. Primary `OSS_*` unset — Groq is sole LLM provider.

Remaining steps before first live run:

1. ☑ ~~All code changes complete and pushed~~ (commits `30787e5`, `b1b3ac0`)
2. ☐ **Confirm Vercel deploy is green** — check Deployments tab, verify `GET /` returns `{"status": "ok"}`
3. ☐ **Register Telegram webhook**: `curl -F "url=https://gym-research.vercel.app/webhook" "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook"`
4. ☐ **End-to-end test**: `curl https://gym-research.vercel.app/trigger -H "Authorization: Bearer $CRON_SECRET"` → expect Telegram DM → submit → email with PDF to `mami.maral@icloud.com`

### Open design questions / decisions deferred

- ~~**Schedule seeding**~~ ✅ Resolved (2026-06-03): `config/schedule.json` now contains the real Upper/Lower routine. `docs/personal-workout-plan.md` is a historical reference only — `config/schedule.json` is the live source of truth and is rewritten by the LLM on every Submit.
- ~~**Resend domain**~~ ✅ Resolved: using `onboarding@resend.dev` sandbox; delivery address `mami.maral@icloud.com` is the Resend-verified recipient.
- ~~**JSON mode upgrade**~~ ✅ Resolved differently (2026-06-03): `response_format=json_object` caused empty responses on Groq in production — removed entirely. System prompt enforces JSON; client strips fences. If malformed JSON reappears, migrate to `json_schema` strict mode (see `README.md` LLM design section).
- ~~**Deploy platform**~~ ✅ Resolved (2026-06-04): Vercel. Railway (credits exhausted), Fly.io (superseded). All code changes complete.
- ~~**PDF on serverless**~~ ✅ Resolved (2026-06-04): PDFShift API replaces WeasyPrint. 50 free conversions/month, no system libs needed.
- ~~**State on serverless**~~ ✅ Resolved (2026-06-04): Neon Postgres replaces SQLite. `DATABASE_URL` injected by Vercel–Neon integration (`neon-cyan-nest`).
- ~~**Bot lifecycle on serverless**~~ ✅ Resolved (2026-06-04): `async with ptb_app:` per-invocation. PTB renamed from `application` → `ptb_app` to avoid Vercel ASGI entrypoint collision.

---

# System A — Full design docs

**Project Status:** ✅ Complete & Deployed
**Last Updated:** May 27, 2026
**Deployed Routine ID:** `trig_01XUTpwZgjKkJw6VDq4HpZSh`
**Next Run:** Every Sunday at 8 AM Berlin time (6 AM UTC)

---

## Executive Summary

This is a fully automated system that manages weekly gym training progression through email. Every Sunday morning, the system:

1. **Checks your Gmail** for your progress reply from last week
2. **Parses your input** (which exercises got heavier/lighter/stayed same + how you felt)
3. **Updates the database** with new weights and tracks performance history
4. **Detects when you need a deload week** using science-backed thresholds + your own training philosophy
5. **Generates next week's HTML** with beautiful Borussia Dortmund-inspired dark theme (printable to PDF)
6. **Sends you the new plan** via email with a reply template for next week

**Zero ongoing setup required.** Just reply to emails each week with your progress in the simple format: `MON: + | Felt great` (increase weight) or `MON: - | Shoulder pain` (decrease) or `MON: stay | Good session` (keep same).

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Cloud Scheduled Routine (Sunday 8 AM Berlin)                   │
│  Runs: Claude Agent + Gmail MCP                                 │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ├─ Checks Gmail for your reply
           │
           ├─ Runs: python3 weekly_gym_update.py process --reply "..."
           │         (or --no-reply if no email found)
           │
           ├─ Updates: progress_log.json
           │           (weights, history, deload flags)
           │
           ├─ Generates: Workout_Plan_Week_N.html
           │             (via generate_workout_html.py — BVB dark theme)
           │
           └─ Sends: Email with new HTML link + reply template
              To: muhammed.maral99@gmail.com

┌─────────────────────────────────────────────────────────────────┐
│  Local Files (on your Mac in gym-research/)                     │
├─────────────────────────────────────────────────────────────────┤
│ • progress_log.json ................ All training data (JSON)   │
│ • weekly_gym_update.py ............. Main logic (900 lines)     │
│ • generate_workout_pdf.py .......... Modified for external data │
│ • Workout_Plan_Week_N.pdf ......... Generated weekly            │
│ • CLAUDE.md (this file) ............ Project documentation      │
└─────────────────────────────────────────────────────────────────┘
```

---

## How It Works: Step-by-Step

### Week 1 (First Run)

```
Sunday 8 AM → Routine checks status → "is_first_run: true"
         ↓
Runs: python3 weekly_gym_update.py process
         ↓
Generates: Workout_Plan_Week_1.html (BVB dark theme)
         ↓
Sends: Email to you with HTML link + reply template
         ↓
You: Do your 4 workouts (Mon, Wed, Fri, Sat) — same exercises every week
```

### Week 2+ (Ongoing)

```
Sunday 8 AM → Routine checks Gmail for your reply
         ↓
Finds: Email with "MON: +\nWED: stay\nFRI: -\nSAT: +"
         ↓
Runs: python3 weekly_gym_update.py process --reply "<email body>"
         ↓
Updates progress_log.json:
  • SAME exercise structure every week (Mon/Wed/Fri/Sat exercises never change)
  • Only WEIGHTS are adjusted based on your feedback:
    - MON: + → Bench Press: 70 kg → 72.5 kg
    - WED: stay → Barbell Squat: 90 kg → 90 kg (no change)
    - FRI: - → DB Shoulder Press: 12.5 kg → 11.25 kg
    - SAT: + → Deadlift: 115 kg → 117.5 kg
  • Counters: +1 week of progression, resets decline counts
         ↓
Checks deload conditions (6 weeks? Fatigue? 2+ weeks decline?)
         ↓
Generates: Workout_Plan_Week_2.html with updated weights only
         ↓
Sends: Email with recap + new plan
         ↓
Loop repeats next Sunday
```

**KEY DESIGN:** Exercise structure stays identical week-to-week. This allows you to track progress on the same movements and compare performance across weeks without confusion from changing exercises.

### When Deload Triggers

```
Week 8: You hit 6 consecutive weeks of "+", OR
        Your comment has "joint pain", OR
        3 weeks with zero "+" responses
         ↓
Routine detects deload condition
         ↓
Generates: Workout_Plan_Week_8.pdf with:
  ✓ SAME weights as Week 7
  ✗ REDUCED sets: 3→2, 4→2 (50-60% volume)
  + Email note: "Same weights, fewer sets, more RIR"
         ↓
After deload week, normal progression resumes
```

---

## The Three Core Files

### 1. `weekly_gym_update.py` — The Brain

**What it does:** Parses replies, updates weights, detects deload, generates JSON output for email.

**Public interface (CLI):**

```bash
# First-time setup
python3 weekly_gym_update.py init
# → Creates progress_log.json seeded from Week 1 data

# Check current state
python3 weekly_gym_update.py status
# → Prints: {"current_week": 2, "is_deload_week": false, ...}

# First run (no reply expected)
python3 weekly_gym_update.py process
# → Generates Week 1 PDF, outputs JSON for agent to email

# Process weekly reply
python3 weekly_gym_update.py process --reply "MON: +\nWED: stay\n..."
# → Updates weights, checks deload, generates Week 2 PDF

# No reply this week (send reminder)
python3 weekly_gym_update.py process --no-reply
# → Resends same week's plan, no weight changes
```

**Key functions:**

| Function                                 | Purpose                                                                    |
| ---------------------------------------- | -------------------------------------------------------------------------- |
| `parse_reply(email_body)`                | Extract MON/WED/FRI/SAT ±/stay from email text                             |
| `update_weights(progress, parsed_reply)` | Apply weight changes (+2.5kg compounds, +1kg isolation)                    |
| `detect_deload(progress, parsed_reply)`  | Check: 6 weeks? Stall? Fatigue keywords? Decline?                          |
| `update_fatigue_counters()`              | Track consecutive progression/decline/no-progress weeks                    |
| `apply_deload_to_progress()`             | Set `is_deload_week=True`, log deload reason                               |
| `build_week_data()`                      | Convert JSON exercises → PDF-ready dict (applies set reductions if deload) |
| `generate_pdf()`                         | Call `generate_workout_pdf.py` with week data                              |
| `build_progress_summary()`               | Create human-readable recap for email                                      |

**Weight type handling:**

```python
WEIGHT_INCREMENTS = {
    'barbell':      2.5,      # "70 kg" → 72.5 kg
    'dumbbell':     1.0,      # "22.5 kg/DB" → 23.5 kg/DB
    'bw_weighted':  1.25,     # "BW + 5 kg" → BW + 6.25 kg
    'bw_only':      0.0,      # "BW" → never changes
    'skip':         0.0,      # "start moderate" → user sets manually
    'machine':      2.5,      # "36 kg" → 38.5 kg
    'cable_side':   2.5,      # "10 kg/side" → 12.5 kg/side
}
```

**Example: How weight updates work**

```python
# User replied: "MON: +"
# Bench Press: weight="70 kg", weight_kg=70.0, weight_type="barbell"

old_kg = 70.0
increment = WEIGHT_INCREMENTS['barbell']  # 2.5
new_kg = old_kg + 2.5  # 72.5
ex['weight'] = format_weight_string(72.5, 'barbell', '70 kg')  # "72.5 kg"
ex['history'].append({'week': 2, 'weight': '72.5 kg', 'weight_kg': 72.5, 'action': 'increase'})
```

---

### 2. `generate_workout_pdf.py` — The PDF Creator

**What changed:** Originally hardcoded Week 1 data. Now accepts external data.

**Original call:**

```python
generator = WorkoutPDFGenerator(output_path)
generator.build_pdf()  # Hardcoded week_data
```

**New call (from weekly_gym_update.py):**

```python
week_data = build_week_data(progress, is_deload=True)  # From JSON
generator = WorkoutPDFGenerator(output_path)
generator.build_pdf(week_data=week_data, week_num=8, is_deload=True)
```

**Title handling:**

```python
# Old: title = 'Week 1 — Upper/Lower Split'
# New:
title = f"Week {week_num} — Upper/Lower Split"
if is_deload:
    title += "  ⚠ DELOAD WEEK"
# Result: "Week 8 — Upper/Lower Split  ⚠ DELOAD WEEK"
```

**Set reductions during deload:**

```python
def build_week_data(progress, is_deload=False):
    # ...
    if is_deload:
        # 3→2 sets, 4→2 sets (50-60% volume)
        ex_copy['sets'] = DELOAD_SETS_REDUCTION.get(str(ex['sets']), str(ex['sets']))
    # Weights stay the same; only sets are reduced in the PDF
```

---

### 3. `progress_log.json` — The Database

**Structure (simplified):**

```json
{
  "meta": {
    "current_week": 2,
    "is_first_run": false,
    "last_email_sent_date": "2026-05-26",
    "last_email_subject": "Week 1 Gym Plan — Upper/Lower Split"
  },
  "deload": {
    "is_deload_week": false,
    "consecutive_progression_weeks": 1,
    "consecutive_no_progress_weeks": 0,
    "last_deload_date": null,
    "deload_count_total": 0,
    "deload_history": []
  },
  "fatigue_tracking": {
    "consecutive_no_progress_weeks": 0,
    "days_consecutive_decline": {"MON": 0, "WED": 0, "FRI": 0, "SAT": 0}
  },
  "exercises": {
    "monday": [
      {
        "num": "1",
        "exercise": "Bench Press",
        "sets": "3",
        "reps": "6–8",
        "weight": "72.5 kg",      // Updated from "70 kg"
        "weight_kg": 72.5,         // Numeric value for math
        "weight_type": "barbell",  // For increment logic
        "rest": "3 min",
        "history": [
          {"week": 1, "weight": "70 kg", "weight_kg": 70.0, "action": "initial"},
          {"week": 2, "weight": "72.5 kg", "weight_kg": 72.5, "action": "increase"}
        ]
      },
      // ... more exercises
    ],
    "wednesday": [...],
    "friday": [...],
    "saturday": [...]
  },
  "week_history": [
    {
      "week": 1,
      "date": "2026-05-26",
      "reply_found": false,
      "responses": {},
      "comments": {},
      "deload_triggered": false,
      "deload_reason": null,
      "plus_count": 0,
      "minus_count": 0,
      "stay_count": 0
    },
    {
      "week": 2,
      "date": "2026-06-02",
      "reply_found": true,
      "responses": {"MON": "+", "WED": "stay", "FRI": "-", "SAT": "+"},
      "comments": {"MON": "Bench felt great", "WED": "Quads sore", ...},
      "deload_triggered": false,
      "deload_reason": null,
      "plus_count": 2,
      "minus_count": 1,
      "stay_count": 1
    }
  ]
}
```

**Key insight:** Each exercise stores BOTH `weight` (display string, e.g., "70 kg") and `weight_kg` (numeric, e.g., 70.0). This separates concerns:

- `weight_kg` used for calculations (+/- increments)
- `weight` used for PDF display and user communication
- `weight_type` used to look up the correct increment

---

## Deload Algorithm Explained

### The Five Deload Triggers

**1. Hard cap: 6 consecutive progression weeks**

```python
if deload_info['consecutive_progression_weeks'] >= 6:
    return True, "6 consecutive weeks of progression — scheduled deload"
```

- Why 6? Your Gym-planning.md says 4-8 weeks; research (Schoenfeld) says 8 weeks approaches overreaching; 6 is midpoint
- Resets after deload week

**2. Stall: 3+ consecutive weeks with zero progression**

```python
if fatigue['consecutive_no_progress_weeks'] >= 3:
    return True, "3 consecutive weeks with no progression"
```

- Triggered when a week has zero `+` responses across all 4 days
- Indicates adaptation plateau

**3. Decline: 2+ consecutive weeks of minus on same day**

```python
for day, count in fatigue['days_consecutive_decline'].items():
    if count >= 2:
        return True, f"2 consecutive weeks of decline on {day}"
```

- Tracks per-day decline (MON, WED, FRI, SAT separately)
- Two `-` responses in a row on same day = warning signal

**4. Fatigue keywords in comments**

```python
FATIGUE_KEYWORDS = [
    (r'joint pain', 'joint pain'),    # Explicit from your docs
    (r'\btired\b', 'tired'),
    (r'\bexhausted\b', 'exhausted'),
    (r'\bfailed\b', 'failed'),
    (r'no energy', 'no energy'),
    (r'\bhurt\b', 'hurt'),
    (r'burned out', 'burned out'),
    (r'very sore', 'very sore'),
    (r'still sore', 'still sore'),
    (r'\bdeload\b', 'deload'),        # Explicit request
    # ... more
]

all_comments = ' '.join(r.get('comment', '').lower() for r in parsed_reply.values())
for pattern, display in FATIGUE_KEYWORDS:
    if re.search(pattern, all_comments):
        return True, f"Fatigue signal: {display}"
```

- Uses regex word boundaries to avoid "deadlift" matching `\bdead\b`
- Catches muscle damage signals (DOMS), CNS fatigue ("no energy"), joint stress

**5. No explicit trigger, but conditions met?**

```python
# Falls through to: return False, None
# Next Sunday, counters increment and may trigger then
```

### How Counters Work

```
Week 1: User replies "MON: +, WED: +, FRI: +"
  → consecutive_progression_weeks = 1
  → consecutive_no_progress_weeks = 0
  → SAT: stay → days_consecutive_decline['SAT'] = 0

Week 2: User replies "MON: stay, WED: stay, FRI: stay, SAT: -"
  → plus_count = 0 → consecutive_no_progress_weeks = 1
  → days_consecutive_decline['SAT'] = 1

Week 3: User replies "MON: +, WED: +, FRI: +, SAT: -"
  → plus_count = 3 → consecutive_no_progress_weeks = 0
  → consecutive_progression_weeks = 2
  → days_consecutive_decline['SAT'] = 2 → TRIGGERS DELOAD

... OR ...

Week 6: User has "+" every week for 6 weeks straight
  → consecutive_progression_weeks = 6 → TRIGGERS DELOAD (hard cap)
```

### After Deload

```python
if deload_triggered:
    fatigue['consecutive_no_progress_weeks'] = 0
    fatigue['days_consecutive_decline'] = {d: 0 for d in DAYS}
    deload_info['consecutive_progression_weeks'] = 0
    deload_info['weeks_since_last_deload'] = 0
    deload_info['last_deload_date'] = date.today().isoformat()
    deload_info['deload_count_total'] += 1
```

- All counters reset to zero after deload
- Lets you build up progression again from scratch
- Tracks total deloads for history

---

## Email Communication

### What You Receive (Sunday 8 AM)

**Subject:** `Week 1 Gym Plan — Upper/Lower Split`  
**Body:**

```
Hey Mami,

Week 1 workout plan attached — print it or open on your phone.

--- LAST WEEK RECAP ---
No reply was received for last week.

--- THIS WEEK'S PLAN ---
See the attached PDF for all exercises, sets, reps, and weights.

Shoulder rehab: 5×45s isometric external rotation hold before Mon, Fri, Sat sessions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REPLY WITH YOUR SCORES for this week's workouts:
  + = increase weights next week
  - = decrease weights next week
  stay = keep the same
  Add a comment after | (optional but helpful for tracking)

MON: [+/-/stay] | [optional comment]
WED: [+/-/stay] | [optional comment]
FRI: [+/-/stay] | [optional comment]
SAT: [+/-/stay] | [optional comment]

Example:
MON: + | Bench felt strong, had energy left
WED: stay | Quads are still recovering
FRI: - | Shoulder was acting up
SAT: + | Great session
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Train hard.
```

**Attachment:** `Workout_Plan_Week_1.pdf` (4KB, A4 page, 2x2 grid layout)

### What You Send Back (Week 2+)

**Reply to the email:**

```
MON: + | Bench was great, hit a 77.5kg PR
WED: stay | Quads still sore from last week
FRI: + | Shoulders feeling good
SAT: - | Deadlift felt heavy, had to back off
```

The routine reads this, parses it, and updates next week's PDF.

### Deload Week Email

**Subject:** `Week 8 Gym Plan — DELOAD WEEK`  
**Body includes:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DELOAD WEEK — Your body needs this.
Same weights as last week. Fewer sets (50-60% volume).
Stop 3-4 RIR — do NOT approach failure.
Focus on movement quality, joints, and CNS recovery.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

--- LAST WEEK RECAP ---
Progression: MON, WED, FRI, SAT — weights increased.
[Your comments here]

⚠ DELOAD TRIGGERED — 6 consecutive weeks of progression — scheduled deload (4-8 week cycle)
Same weights, ~50% sets, 3-4 RIR. Let joints and CNS recover.
```

---

## Research Foundation

### Where the Algorithm Comes From

**Deload Frequency (Every 4-8 weeks):**

- Source: Gym-planning.md (YOUR OWN PLAN)
- Science basis: Schoenfeld et al. (2016) — "scheduling regular periods of reduced training frequencies every few weeks (deloading)"

**6-Week Hard Cap:**

- YOUR PLAN: 4-8 weeks
- SCIENCE: Schoenfeld et al. (2018) — 8 weeks at high volume (30-45 sets/week) approaches non-functional overreaching
- LOGIC: 6 weeks = midpoint, safer upper bound

**Weight Increments (2.5 kg compounds, 1 kg isolation):**

- YOUR PLAN: "+1 rep on top set OR +2.5 kg" progression rule
- SCIENCE: Grgic et al. (2018) — 6+ sets/week per muscle minimum for strength
- Your split: 2x/week per muscle, so ~12-20 sets/week optimal

**Deload Protocol (Same weights, 50-60% volume):**

- YOUR PLAN: "Deload: every 4–8 weeks, 50–60% volume"
- "Intensity (weights): same — keep the same loads"
- "More RIR (reps in reserve)"
- SCIENCE: Schoenfeld et al. (2017) — Low-load training (≤60% 1RM, 20-30 reps) doesn't sacrifice hypertrophy

**Stall Definition (2-3 weeks no progress):**

- YOUR PLAN: "cannot add reps or sets for 2–3 weeks"
- SCIENCE: Schoenfeld et al. (2017) — Minimum 6-week training block needed to assess progress meaningfully
- LOGIC: At 3 weeks with no progress, deload is likely needed

**Fatigue Keywords (tiredness, joint pain, soreness):**

- Dupuy et al. (2018) — DOMS normally resolves 24-72h; prolonged DOMS + elevated perceived fatigue = incomplete recovery
- Coffey & Hawley (2017) — Accumulated fatigue mechanisms degrade performance
- YOUR PLAN: "Joint pain → drop load, run isometric protocol"

---

## How to Use This System

### For Regular Use

```bash
# Every Sunday, you receive an email at 8 AM Berlin time
# 1. Read the email
# 2. Do your 4 workouts during the week
# 3. Reply to the email with your progress
#    Format: MON: + | Great session
#            WED: stay | Sore quads
#            FRI: - | Shoulder pain
#            SAT: + | Strong deadlift
# 4. Next Sunday, routine processes your reply and sends new week
# 5. Loop continues
```

### For Manual Testing

```bash
cd /Users/neu/Downloads/gym-research

# Reset everything
python3 weekly_gym_update.py init

# Check status
python3 weekly_gym_update.py status
# Output: {"current_week": 1, "is_first_run": true, ...}

# Simulate Week 1
python3 weekly_gym_update.py process
# Output: JSON with Week 1 plan

# Simulate Week 2 with strong response (no deload)
python3 weekly_gym_update.py process --reply "MON: + | Great
WED: + | Good
FRI: + | Strong
SAT: + | Excellent"

# Simulate Week 8 with 6 weeks progression (should trigger deload)
# ... repeat the above 6 times ...
# Then run process again → should get "is_deload": true

# Simulate fatigue trigger
python3 weekly_gym_update.py process --reply "MON: stay | Joint pain
WED: - | Tired
FRI: - | No energy
SAT: stay | Beat"
```

### Viewing Your Progress

```bash
# View all your training history
cat progress_log.json | python3 -m json.tool

# Check current week and deload status
python3 weekly_gym_update.py status

# View a specific exercise's weight history
python3 -c "
import json
with open('progress_log.json') as f:
    data = json.load(f)
    bench = data['exercises']['monday'][0]  # Bench Press
    print(f'Exercise: {bench[\"exercise\"]}')
    print(f'Current weight: {bench[\"weight\"]}')
    print(f'History:')
    for entry in bench['history']:
        print(f'  Week {entry[\"week\"]}: {entry[\"weight\"]} ({entry[\"action\"]})')
"
```

---

## Troubleshooting Guide

### Issue: "Weights not updating"

**Check:**

1. Did you reply to the email with the correct format?
   ```
   ✓ MON: + | Great session
   ✗ Monday: increase
   ✗ +++ all lifts
   ```
2. Did the agent find your reply? Check the output of `weekly_gym_update.py status`
3. Is `last_email_sent_date` in progress_log.json set to the date you sent the email?

**Fix:** Manually test the script:

```bash
python3 weekly_gym_update.py process --reply "MON: + | Test"
# Check if it outputs is_deload: false, new weights in JSON
```

### Issue: "Deload triggered unexpectedly"

**Check `progress_log.json`:**

- `consecutive_progression_weeks` = 6? (Hard cap)
- `consecutive_no_progress_weeks` = 3+? (Stall)
- Check `fatigue_tracking.days_consecutive_decline` = 2+ on any day? (Decline)
- Check the email you sent — did it contain a fatigue keyword?

**Fatigue keywords that trigger deload:**

- "joint pain", "joint ache"
- "tired", "exhausted", "pain", "hurt"
- "no energy", "couldn't", "dead", "burned out", "struggling", "wrecked"
- "very sore", "still sore", "always sore" (only sustained soreness, not just DOMS)
- "no strength", "feeling weak"
- "deload" (explicit request)

**Fix:** Review your comment in the email — did you use any of these words?

### Issue: "PDF not generating"

**Check:**

1. Does `/Users/neu/Downloads/gym-research/legacy_outputs/Workout_Plan_Week_N.pdf` exist?
2. Are both files present and unmodified?
   - `generate_workout_pdf.py` (with build_pdf signature change)
   - `progress_log.json` (created by `init` command)

**Fix:** Manually test PDF generation:

```bash
python3 generate_workout_pdf.py
# Should create Workout_Plan_Week_1.pdf (or current week)
# Check the file size > 4KB
```

### Issue: "Routine not running on Sunday"

**Check:**

1. Is the routine enabled? Visit: https://claude.ai/code/routines/trig_01XUTpwZgjKkJw6VDq4HpZSh
2. Is "Next run at" showing future date?
3. Does it show "Status: Enabled"?

**Fix:** If disabled, re-enable from the URL above. If more than 1 week past next run date, manually trigger:

```bash
# Contact support or trigger manually:
python3 weekly_gym_update.py process
# Then update progress_log.json manually:
# Set meta.last_email_sent_date to today's date
```

---

## File Manifest

```
/Users/neu/Downloads/gym-research/
├── CLAUDE.md ................................. This documentation file
├── weekly_gym_update.py ....................... Main script (900+ lines)
│   ├── CLI: init, status, process
│   ├── Parses email replies
│   ├── Updates weights in JSON
│   ├── Detects deload conditions
│   └── Generates JSON output for agent
│
├── generate_workout_html.py ................... HTML generator (BVB design)
│   ├── Beautiful dark theme + yellow accents
│   ├── Printable to PDF from browser
│   ├── Generates: Workout_Plan_Week_N.html
│   ├── Fonts: Bebas Neue (headings), Inter (body), JetBrains Mono (tech)
│   └── Used by: weekly_gym_update.py
│
├── progress_log.json .......................... Your training database
│   ├── Created by: python3 weekly_gym_update.py init
│   ├── Updated by: weekly_gym_update.py (via agent)
│   ├── Stores: Exercises, weights, history, deload flags
│   └── Never edit manually (use the script)
│
├── legacy_outputs/ ............................ Generated HTMLs + PDFs (gitignored)
│   └── Workout_Plan_Week_N.{html,pdf} ......... Beautiful dark theme, landscape A4
│
└── docs/ ...................................... Training plans + research (reference)
    ├── personal-workout-plan.{md,html,pdf} .... Your training plan
    ├── Gym-planning.md ........................ Programming theory
    ├── golden-encyklopedia-building-muscle.md . Your notes
    ├── injury-recovery.md ..................... Shoulder protocol
    └── research/ .............................. Scientific PDFs (gitignored)
        └── *.pdf (10+ files — Schoenfeld, Grgic, Dupuy, etc.)
```

> **Note:** System B (Telegram bot) lives at the repo root alongside System A. See the directory layout at the top of this file or `README.md` for the full picture.

---

## Design Philosophy

### Exercise Structure (MAY 27, 2026 UPDATE)

✅ **Consistent week-to-week**: Same exercises every week (Mon/Wed/Fri/Sat never change)  
✅ **Weights only adjust**: Only load changes based on your feedback, not exercise selection  
✅ **Clean analysis**: Easier to track progress on same movements across multiple weeks  
✅ **Stable routine**: Reduces confusion from constantly changing exercises

### Visual Design (MAY 27, 2026 UPDATE)

✅ **HTML with BVB theme**: Beautiful dark theme (black + yellow) inspired by Borussia Dortmund  
✅ **Browser-friendly**: Open in browser, print to PDF for professional output  
✅ **Responsive layout**: 2-column day cards, landscape A4 format  
✅ **Typography**: Bebas Neue (headings), Inter (body), JetBrains Mono (technical)

---

## Maintenance & Future Enhancements

### Current Capabilities

✅ Weekly email-based progress tracking  
✅ Automatic weight adjustments (+2.5 kg compounds, +1 kg isolation)  
✅ Science-backed deload detection (6+ weeks, stalls, fatigue)  
✅ Complete training history (every exercise, every week)  
✅ Beautiful HTML workouts with BVB dark theme (printable to PDF)  
✅ No manual intervention needed (fully automated)

### Potential Improvements

- [ ] Multi-week progression trends (chart your gains)
- [ ] Custom fatigue thresholds per muscle group
- [ ] Soft deloads (first trigger = more RIR, second trigger = reduced volume)
- [ ] Auto-email reminder if no reply by Friday
- [ ] Integration with wearables (HRV, sleep) for better deload detection
- [ ] Recovery mode weeks (lighter training after high-volume blocks)
- [ ] Injury-specific protocols (shoulder, knee, back modifications)
- [ ] Strength standards comparison (e.g., "Bench: 102.5 kg = 1.3× BW, beginner+")

---

## Routine Deployment Details

**Routine ID:** `trig_01XUTpwZgjKkJw6VDq4HpZSh`  
**Name:** Weekly Gym Progress Update  
**Schedule:** `0 6 * * 0` (Sundays 6 AM UTC = 8 AM Berlin)  
**Cron Next Fire:** May 31, 2026 at 6:03 AM UTC  
**Environment:** Bridge (your Mac) — `env_01Vi3ihUFAehV1rZTWKgkdFP`  
**Model:** Claude Sonnet 4.6  
**MCP Connections:** Gmail (read & send emails)  
**Allowed Tools:** Bash, Read, Write, Edit, Glob, Grep  
**Status:** ✅ Enabled

**Manage at:** https://claude.ai/code/routines/trig_01XUTpwZgjKkJw6VDq4HpZSh

---

## Quick Start for Next Session

1. **Read this file** to understand architecture
2. **Check status:** `python3 weekly_gym_update.py status`
3. **View progress:** `cat progress_log.json | python3 -m json.tool`
4. **Manual test:** `python3 weekly_gym_update.py process --reply "MON: +"`
5. **Monitor routine:** Visit https://claude.ai/code/routines/trig_01XUTpwZgjKkJw6VDq4HpZSh

If issues arise, check the **Troubleshooting Guide** above.

---

**System Status:** ✅ Production Ready  
**Last Tested:** May 27, 2026  
**Deployed:** May 26, 2026  
**User Email:** muhammed.maral99@gmail.com  
**User Timezone:** Europe/Berlin  
**User Stats:** 79 kg, 26 years old, 10+ years training experience
