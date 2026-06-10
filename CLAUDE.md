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
├── notes/                     Archived design docs + session history (see below)
├── data/        facts.json — curated science-fact pool for the newsletter (~25 entries)
├── assets/      hero/*.jpg — curated copyright-free hero photos, rotated per issue
└── DESIGN-Weekly-Science-Newsletter/   Source assets for the "Light Weight" newsletter (canvas JSX + HTML preview)
```

## Architecture (System B — current)

**Flow:** Vercel cron (`vercel.json`, `0 8 * * 0`) → GET `/trigger` → `/checkin` DM with planned schedule → user sends voice memo (or text) → Whisper transcribes → Llama 3.3 70B applies progression rules → confirmation card with diff → user taps **Confirm** → PDF (PDFShift) → email (Resend) → `config/schedule.json` rewritten.

- **LLM:** `llama-3.3-70b-versatile` on Groq with `json_object` response format + Pydantic `WeeklyPlan` validation. Output structure enforced via explicit JSON skeleton in the system prompt. See `core/llm_client.py`, `core/prompt.py`.
- **ASR:** `whisper-large-v3-turbo` on Groq (`core/transcribe.py`). Text messages bypass transcription and go straight to plan generation.
- **State:** Neon Postgres via `psycopg` v3 (`bot/state.py`). Tables: `checkin_state`, `checkin_history`. `DATABASE_URL` injected by Vercel–Neon integration.
- **PDF:** PDFShift API (`core/pdf.py`) — A4 landscape, Jinja2 template, no system libs. Template: BVB dark theme (black + `#FDE100`), Bebas Neue headers, JetBrains Mono for numbers. **2 pages**: page 1 = all 4 workouts in a 2×2 grid (each card ~134mm × 85mm, cut along the 6mm gap crosshair → 4 notebook-sized stickers); page 2 = 8 run stickers in a 4×2 grid (cut-out). Page size, margins, gap, and per-card dimensions live as constants at the top of `core/pdf.py` and are threaded into the Jinja template — single source of truth, change there only. PDFShift is told `format: "A4", landscape: True` explicitly (CSS `@page` alone is unreliable for orientation). Smoke-test: `python3 -m core.pdf /tmp/plan.pdf && open /tmp/plan.pdf` (needs `PDFSHIFT_API_KEY` in `.env`).
- **Newsletter:** the Sunday email body is the branded **Light Weight** newsletter (`templates/newsletter.html`, hi-fi design from `DESIGN-Weekly-Science-Newsletter/newsletter-hifi.jsx`). Each issue carries: masthead (issue + date) → optional deload strip → hero photo → one curated science fact + citation + "why it matters" → last-week recap (sessions/+kg/skipped + biggest-jump line) → this-week plan rows → signed PDF download CTA → footer. PDF stays attached. Source: `core/email.py` (send_newsletter), `core/newsletter.py` (context builder), `core/facts.py` + `data/facts.json` (curated 25-fact pool with deterministic tag-match picker), `core/hero.py` + `assets/hero/*.jpg` (12 photos, rotated by issue number), `core/signing.py` (HMAC for the CTA URL). `GET /plan/{week_number}.pdf?t=<hmac>` re-renders from `checkin_history.schedule_snapshot` on demand. Smoke-test: `python3 scripts/test_newsletter.py` (dry-run to /tmp + browser preview) or `python3 scripts/test_newsletter.py --send` (real Resend send).

**Current status:** Live on Vercel. End-to-end flow verified 2026-06-08. Email delivery fixed 2026-06-09 (custom domain `mami-gym-bot-update.xyz`). Add `gym@mami-gym-bot-update.xyz` to iCloud contacts to keep out of junk. Newsletter rebrand shipped 2026-06-10.

## Newsletter constraints (do not break)

- **Brand wordmark stays `LIGHT WEIGHT.`** with the yellow period accent. Alternates from the identity board (Overload / Tension / Volume) are explicit non-choices — see `DESIGN-Weekly-Science-Newsletter/identity-boards.jsx`.
- **Hi-fi is the chosen visual system** (rounded cards, Bebas Neue display). The elevated/stencil variant (`newsletter-elevated.jsx`) is documented but not used.
- **Facts come from `data/facts.json` only.** No LLM in the fact path — picker is deterministic tag-match against the transcript with repeat-avoidance via `checkin_history.used_fact_id`. When the pool ages out (~25 weeks), top it up by extending the JSON, not by switching to LLM generation.
- **Hero rotation is deterministic by `issue_number % len(pool)`.** Don't introduce randomness — the cycle is meant to be predictable for the maintainer.
- **CTA is HMAC-signed via `core/signing.py`.** Token derived from `CRON_SECRET`. Don't shorten below 16 hex chars; don't add expiry (archive use case needs old links to stay alive).
- **`APP_BASE_URL` must be set** for the hero `<img src>` and CTA `href` to resolve in production. Without it, both fall back gracefully but the email is missing pieces.
- **Per-exercise `status` field on the LLM is load-bearing** — the recap math (sessions-done, skipped-count) reads from it. The Pydantic model defaults to `as_planned` so legacy plans still validate, but new prompts should always request the field.
- **Email-safe template rules** (in `templates/newsletter.html`): all CSS inline, tables for layout, `bgcolor=` alongside `style:background` for Outlook, numeric width/height attrs on `<img>` + `<td>`, hidden preheader span first thing in `<body>`. Don't switch to flex/grid — Outlook desktop will fall back to block.

**Future-scaling note (do not delete):** the signed-PDF endpoint re-renders on every click via PDFShift. Fine for a single-subscriber v1; if subscriber count grows past ~5 or PDFShift quota tightens, migrate to "render once on Confirm → cache to Vercel Blob / R2 → endpoint streams from blob". The HMAC token logic stays the same; only the byte source flips. Documented in detail in `README.md` § "Future scaling".

**Future-vision note (do not delete):** product trajectory is **stage 0** (single-tenant Telegram) → **stage 1** (manual friend onboarding, maintainer types in their plan + ferries their voice memo) → **stage 2** (landing page + magic-link signup) → **stage 3** (browser-recorded check-ins, no Telegram) → **stage 4** (full mobile app, eliminates Telegram + PDF + email entirely). Engine (LLM rules, facts, newsletter template, PDF) is reusable through stage 3; stage 4 absorbs everything. Don't pre-build past the current stage — each stage is only justified when the previous one breaks. Full detail in `README.md` § "Future vision".

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
- **Apple Mail "Your network blocks remote content" is not your network** — it's Mail Privacy Protection, a per-recipient default since iOS 15 / macOS Monterey. Triggered by any `<img src="https://…">` in the body. Recipient clicks "Load remote content" once; subsequent issues from the same `RESEND_FROM` usually auto-load (especially once that address is in the recipient's Contacts). **Don't try to "fix" this for single-tenant** — accept the one-time click. If/when shipping to friends and the warning friction becomes the bottleneck, swap the hero `<img>` to an inline base64 data URI (~10 LOC in `core/email.py`, email size goes 17 KB → ~85 KB; PDF attachment already dominates the payload). The CTA URL stays remote — it's a click target, not auto-loaded, so the privacy filter doesn't apply.

## Secrets — where each key lives

- **`RESEND_API_KEY`** — generate at `resend.com/api-keys`, scope to the verified domain (`mami-gym-bot-update.xyz`). Shown once on creation; if lost, rotate by generating a new one and revoking the old. Used at runtime in `core/email.py` and `scripts/test_*.py`.
- **`CRON_SECRET`** — generate locally with `openssl rand -hex 32`. Vercel injects it as `Authorization: Bearer …` on every `/trigger` invocation; also the HMAC key for signed PDF download URLs (`core/signing.py`). **In the Vercel dashboard, you can mark it Sensitive or not** — single-tenant trade-off: marking Sensitive hides the value after creation (more hygienic, but you can't read it back, so save to a password manager *immediately* or you'll need to rotate to recover). At stage 0/1 the practical risk delta is small; at stage 2+ (multi-tenant) treat Sensitive as required.
- **`GROQ_API_KEY`, `PDFSHIFT_API_KEY`, `TELEGRAM_BOT_TOKEN`** — issued by each provider's dashboard. Same "save on creation or rotate to recover" pattern.
- **`DATABASE_URL`** — injected automatically by the Vercel ↔ Neon integration. Don't set manually in production; pull locally with `vercel env pull .env` if you need to debug against the live DB.
