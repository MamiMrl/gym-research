# Gym Tracking — Project Status

> Read `README.md` first — it's the canonical onboarding doc. This file is the quick orientation + don'ts.

## Project Overview

A weekly gym-progression tracker. The current implementation (**System B**) is a Telegram voice-memo bot deployed on Vercel. A prior implementation (**System A**, email-based) was retired 2026-06-03 and lives in `legacy_email/`.

## Directory layout

```
.
├── README.md                  Collaborator onboarding (start here)
├── CLAUDE.md                  This file
├── .env.example               All env vars (Telegram, Groq, PDF, email)
│
├── main.py, requirements.txt, Dockerfile, vercel.json, Procfile, railway.json
├── bot/        Telegram handlers (voice + text flow), keyboards, Postgres state
├── core/       llm_client (Llama 3.3), transcribe (Whisper), pdf, email, prompt, schedule
├── config/     schedule.json — live source of truth, rewritten by LLM on every Submit
├── templates/  plan.html — Jinja2 A4 PDF template
├── scripts/    test_plan.py — local smoke-test for plan generation
├── .github/    workflow_dispatch fallback (cron handled by Vercel)
│
├── legacy_email/              System A — retired 2026-06-03 (see its README.md)
├── docs/                      Training plans + scientific references
└── notes/                     Archived design docs + session history (see below)
```

## Architecture (System B — current)

**Flow:** Vercel cron (`vercel.json`, `0 8 * * 0`) → GET `/trigger` → `/checkin` DM with planned schedule → user sends voice memo (or text) → Whisper transcribes → Llama 3.3 70B applies progression rules → confirmation card with diff → user taps **Confirm** → PDF (PDFShift) → email (Resend) → `config/schedule.json` rewritten.

- **LLM:** `llama-3.3-70b-versatile` on Groq with `json_object` response format + Pydantic `WeeklyPlan` validation. Output structure enforced via explicit JSON skeleton in the system prompt. See `core/llm_client.py`, `core/prompt.py`.
- **ASR:** `whisper-large-v3-turbo` on Groq (`core/transcribe.py`). Text messages bypass transcription and go straight to plan generation.
- **State:** Neon Postgres via `psycopg` v3 (`bot/state.py`). Tables: `checkin_state`, `checkin_history`. `DATABASE_URL` injected by Vercel–Neon integration.
- **PDF:** PDFShift API (`core/pdf.py`) — Jinja2 template, no system libs.

**Current status:** Live on Vercel. End-to-end flow verified 2026-06-08.

## Don'ts / critical constraints

- **Never name anything `app` or `application` in `main.py`** unless it's the FastAPI ASGI instance. Vercel's Python runtime auto-picks the first match and will mis-bind PTB. PTB stays as `ptb_app`.
- **Use `BIGINT` for any Telegram user/chat/message ID column.** `INTEGER` overflows on real chat IDs.
- **In `psycopg` v3, one `execute()` = one statement.** For multi-table schema setup, call `execute()` once per statement.
- **Don't add FastAPI `lifespan=` for the bot on serverless.** Use `async with ptb_app:` per-invocation — Vercel's shutdown window is too short for PTB teardown.
- **WeasyPrint is incompatible with Vercel** (system libs missing). PDF rendering goes through PDFShift.
- **SQLite is ephemeral on serverless.** All persistent state goes to Neon Postgres.
- **`config/schedule.json` is the live source of truth**, rewritten by the LLM on every Submit. `docs/personal-workout-plan.md` is historical reference only — don't sync from it.
- **System A is retired.** Don't resurrect `legacy_email/` code or the disabled routine `trig_01XUTpwZgjKkJw6VDq4HpZSh`.
- **`llama-3.3-70b-versatile` does not support `json_schema` response format on Groq.** Use `json_object` + explicit JSON skeleton in the system prompt instead.
- **Before pushing LLM prompt changes**, run `python3 scripts/test_plan.py` locally to validate end-to-end.

## Deeper docs (open on demand)

- `README.md` — collaborator onboarding, env vars, deploy steps.
- `notes/system-b-history.md` — session history, deployment-bug write-ups, architecture decisions.
- `notes/system-a-design.md` — full design of the retired email system.
- `legacy_email/README.md` — System A retirement note.
- `docs/personal-workout-plan.md`, `docs/Gym-planning.md`, `docs/golden-encyklopedia-building-muscle.md`, `docs/injury-recovery.md` — training references.

## User context

- 79 kg, 26 yo, 10+ years training experience. Timezone: Europe/Berlin.
- Delivery email: `mami.maral@icloud.com` (Resend-verified). Resend sender: `onboarding@resend.dev` sandbox.
