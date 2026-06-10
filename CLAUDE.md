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
├── templates/  plan.html — Jinja2 A4-landscape PDF template (BVB dark theme, 2×2 workout grid + run stickers)
├── scripts/    test_plan.py, test_email.py — local smoke-tests
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
- **PDF:** PDFShift API (`core/pdf.py`) — A4 landscape, Jinja2 template, no system libs. Template: BVB dark theme (black + `#FDE100`), Bebas Neue headers, JetBrains Mono for numbers. **2 pages**: page 1 = all 4 workouts in a 2×2 grid (each card ~134mm × 85mm, cut along the 6mm gap crosshair → 4 notebook-sized stickers); page 2 = 8 run stickers in a 4×2 grid (cut-out). Page size, margins, gap, and per-card dimensions live as constants at the top of `core/pdf.py` and are threaded into the Jinja template — single source of truth, change there only. PDFShift is told `format: "A4", landscape: True` explicitly (CSS `@page` alone is unreliable for orientation). Smoke-test: `python3 -m core.pdf /tmp/plan.pdf && open /tmp/plan.pdf` (needs `PDFSHIFT_API_KEY` in `.env`).

**Current status:** Live on Vercel. End-to-end flow verified 2026-06-08. Email delivery fixed 2026-06-09 (custom domain `mami-gym-bot-update.xyz`). Add `gym@mami-gym-bot-update.xyz` to iCloud contacts to keep out of junk.

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
- **PDFShift needs explicit `format` + `landscape` in the API payload — CSS `@page size` alone is not enough.** Without it, PDFShift defaults to A4 portrait regardless of what `@page` says, and a wide landscape grid silently spills onto a 2nd page. Keep `"format": "A4", "landscape": True` in `core/pdf.py`.
- **PDF layout constants (page dims, margins, grid gap, card size) belong as module-level constants at the top of `core/pdf.py`**, threaded into the Jinja template via context vars. They are *not* env vars (don't vary per deploy) and *not* duplicated in the template (divergence between PDFShift API and CSS `@page` cuts content). Single source of truth.
- **Before pushing LLM prompt changes**, run `python3 scripts/test_plan.py` locally to validate end-to-end.

## Deeper docs (open on demand)

- `README.md` — collaborator onboarding, env vars, deploy steps.
- `notes/system-b-history.md` — session history, deployment-bug write-ups, architecture decisions.
- `notes/system-a-design.md` — full design of the retired email system.
- `legacy_email/README.md` — System A retirement note.
- `docs/personal-workout-plan.md`, `docs/Gym-planning.md`, `docs/golden-encyklopedia-building-muscle.md`, `docs/injury-recovery.md` — training references.

## Email delivery

- **Resend requires a verified custom domain** to deliver reliably to iCloud (and other providers). `onboarding@resend.dev` is silently dropped by Apple Mail. Set `RESEND_FROM` to an address on a domain you've verified in Resend → Domains.
- Run `python3 scripts/test_email.py` locally to confirm delivery before deploying.
