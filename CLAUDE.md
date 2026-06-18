# Gym Tracking — Project Status

> Read `README.md` first — it's the canonical onboarding doc. This file is the quick orientation + don'ts.

## Project Overview

A weekly gym-progression tracker. **System B** (live): Telegram voice-memo bot on Vercel. Sunday cron → Whisper → Llama 3.3 → PDF → "Light Weight" newsletter via Resend. **System A** (retired 2026-06-03) — email rule engine, archived in `legacy_email/`.

Full architecture, env vars, deploy steps, troubleshooting: see `README.md`.

## Directory layout

```
.
├── main.py, vercel.json, requirements.txt
├── bot/        Telegram handlers + Postgres state
├── core/       llm_client, transcribe, pdf, email, newsletter, facts, hero, signing, schedule, prompt
├── config/     schedule.json — live source of truth, rewritten by the LLM each Submit
├── templates/  plan.html (PDF), newsletter.html (email)
├── data/       facts.json — curated science-fact pool
├── assets/     hero/*.jpg — rotated newsletter photos
├── scripts/    test_plan.py, test_email.py, test_newsletter.py — smoke tests
├── DESIGN-Weekly-Science-Newsletter/   Newsletter design source (JSX + HTML)
├── docs/       Training references
├── notes/      History, archived design, operational runbooks
└── legacy_email/   System A (retired)
```

## Don'ts / critical constraints

- **Never name anything `app` or `application` in `main.py`** unless it's the FastAPI instance. PTB stays `ptb_app`.
- **Use `BIGINT` for any Telegram user/chat/message ID column.** `INTEGER` overflows.
- **In `psycopg` v3, one `execute()` = one statement.** Multi-statement strings silently truncate.
- **No FastAPI `lifespan=` for the bot on serverless.** Use `async with ptb_app:` per-invocation.
- **`CREATE TABLE IF NOT EXISTS` is a no-op against pre-existing prod tables** — for every new column, also add an idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` in `bot/state.py:init_db`. Skipping this silently breaks INSERTs (see `notes/system-b-history.md`, 2026-06-11 transcript-column incident).
- **WeasyPrint is incompatible with Vercel.** PDF goes through PDFShift.
- **SQLite is ephemeral on serverless.** All persistent state → Neon Postgres.
- **`config/schedule.json` is the live source of truth**, rewritten by the LLM each Submit. `docs/personal-workout-plan.md` is historical reference only — don't sync from it.
- **System A is retired.** Don't resurrect `legacy_email/` code or routine `trig_01XUTpwZgjKkJw6VDq4HpZSh`.
- **`llama-3.3-70b-versatile` does not support `json_schema` on Groq.** Use `json_object` + explicit JSON skeleton in the system prompt + Pydantic validation.
- **PDFShift needs explicit `format` + `landscape` in the API payload.** CSS `@page` alone is unreliable — silently defaults to portrait and the grid spills to a 2nd page.
- **PDF layout constants live at the top of `core/pdf.py`** and are threaded into the Jinja template. Don't duplicate them in the template.
- **Before pushing LLM prompt changes**: `python3 scripts/test_plan.py`. For newsletter changes: `python3 scripts/test_newsletter.py`.

## Deeper docs (open on demand)

- `README.md` — collaborator onboarding, env vars, deploy, troubleshooting, newsletter design, future stages.
- `notes/newsletter-constraints.md` — load-bearing newsletter design rules (brand, fact source, hero rotation, email-safe HTML).
- `notes/email-operations.md` — Resend domain setup, Apple Mail Privacy Protection behavior.
- `notes/secrets-runbook.md` — where each env var comes from and how to rotate it.
- `notes/system-b-history.md` — session history, deployment bugs, architecture decisions.
- `notes/system-a-design.md` — full design of the retired email system.
- `legacy_email/README.md` — System A retirement note.
- `docs/` — training references (workout plan, periodization, injury recovery).
