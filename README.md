# gym-progression-bot

Send a voice memo after your Sunday workout. Get next week's plan as a PDF in your inbox.

**gym-progression-bot** is a self-hosted Telegram bot that replaces manual spreadsheet tracking. Record a 30-second voice note describing how each session went — too easy, struggled, skipped a set — and the bot transcribes it, applies progressive overload rules, and emails you a ready-to-print PDF plan for the week ahead.

Built on: [Groq](https://groq.com) (Llama 3.3 70B + Whisper), Neon Postgres, PDFShift, Resend, Vercel.

The active system is **System B** (Telegram voice-memo bot). System A — an older email-based rule engine — was retired 2026-06-03 and lives in `legacy_email/` for reference.

> ✅ **Shipped (2026-06-10):** the Sunday email is now the full weekly newsletter — **"Light Weight."** — with a science fact of the week, last-week recap stats, and a signed PDF download. Source design: `DESIGN-Weekly-Science-Newsletter/`. Details: [Newsletter](#newsletter-light-weight) section below.

| | System A (retired) | System B (current) |
|---|---|---|
| **Channel** | Email reply | Telegram voice memo |
| **LLM** | None (rule-based) | `llama-3.3-70b-versatile` (planner) + `whisper-large-v3-turbo` (transcription) on Groq |
| **Output** | HTML email + printable plan | PDF attached to email (via Resend) |
| **Trigger** | Cloud routine `trig_01XUTpwZgjKkJw6VDq4HpZSh`, Sundays 08:00 Berlin | Vercel cron (via `vercel.json`), Sundays 08:00 UTC → GET `/trigger` |
| **Code** | `legacy_email/` | `main.py`, `bot/`, `core/`, `config/`, `templates/`, `vercel.json` |
| **Status** | ☠ Retired 2026-06-03 | ✅ Working — deploy your own fork in ~30 min |
| **Full docs** | `legacy_email/README.md` + `CLAUDE.md` (System A design appendix) | This file + `CLAUDE.md` (System B header) |

---

## Repo layout

```
.
├── README.md                  This file
├── CLAUDE.md                  Detailed project status + System A design docs
├── .gitignore
├── .env                       (gitignored) Local secrets
│
├── # ── System B (Telegram bot, deployed on Vercel) ──
├── main.py                    FastAPI app: GET /, POST /webhook, GET /trigger
├── requirements.txt
├── vercel.json                Vercel cron config (Sunday 08:00 UTC → GET /trigger)
├── Dockerfile                 Kept for local Docker dev; not used in production
├── Procfile                   Legacy buildpack fallback; not used
├── railway.json               Legacy Railway config; not used
├── bot/
│   ├── handlers.py            Telegram conversation flow (check-in → submit)
│   ├── keyboards.py           Inline keyboard (Confirm / Re-record)
│   └── state.py               Neon Postgres per-chat check-in state + history
├── core/
│   ├── schedule.py            Load/save config/schedule.json
│   ├── prompt.py              System prompt + per-week prompt builder
│   ├── llm_client.py          Groq llama-3.3-70b-versatile (json_object + Pydantic validation)
│   ├── transcribe.py          Groq whisper-large-v3-turbo (voice memo → text)
│   ├── pdf.py                 Jinja2 render → PDFShift API → PDF bytes
│   └── email.py               Resend send w/ base64 PDF attachment
├── config/schedule.json       The weekly plan — seed with your own exercises and loads
├── scripts/test_plan.py       Local smoke-test for plan generation
├── scripts/test_email.py      Local smoke-test for email delivery
├── templates/plan.html        Jinja2 A4-landscape PDF template (2×2 workout grid + run-sticker page)
├── .github/workflows/checkin.yml   Manual workflow_dispatch fallback (cron handled by Vercel)
│
├── # ── System A (retired 2026-06-03, archived for reference) ──
├── legacy_email/
│   ├── README.md              Why it's retired + how it worked
│   ├── weekly_gym_update.py   Main script — parses replies, updates weights, deload logic
│   ├── generate_workout_html.py / generate_workout_pdf.py   Renderers
│   ├── progress_log.json      Final training database snapshot
│   ├── routine_agent.md       Original cloud-routine agent prompt
│   └── outputs/               Generated weekly HTMLs/PDFs (gitignored)
│
└── docs/                      Training plans + scientific references
    ├── personal-workout-plan.md / .html / .pdf
    ├── Gym-planning.md        Periodization + deload theory
    ├── golden-encyklopedia-building-muscle.md
    ├── injury-recovery.md     Shoulder protocol
    └── research/              Source PDFs for the algorithm (gitignored)
```

---

## System B — quickstart

### Environment variables

Set locally in `.env` and in your hosting provider's environment variables:

```bash
# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# LLM + ASR — Groq is the sole provider.
# Llama 3.3 70B for planning (json_object mode), Whisper turbo for voice transcription.
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile           # does NOT support json_schema on Groq; json_object used instead
GROQ_WHISPER_MODEL=whisper-large-v3-turbo    # transcription — ~250× real-time

# PDF generation — PDFShift managed API (50 free conversions/month, no system libs needed)
# Sign up at pdfshift.io, copy the sk_... key.
PDFSHIFT_API_KEY=sk_...

# Database — Neon Postgres (injected automatically by the Vercel–Neon integration)
# For local dev: copy the DATABASE_URL from your Neon dashboard or run `vercel env pull`.
DATABASE_URL=postgresql://...

# Email
RESEND_API_KEY=re_...
RESEND_FROM=you@yourdomain.com               # Must use a verified custom domain (see Email setup below)
YOUR_EMAIL=you@yourdomain.com               # Where the weekly PDF gets sent

# Cron auth — Vercel injects this automatically as Authorization: Bearer <CRON_SECRET>
# on every cron call. Generate with: openssl rand -hex 16
CRON_SECRET=<random hex>
```

The Vercel cron in `vercel.json` fires every Sunday 08:00 UTC directly — no GitHub Actions secrets are needed.

### Local dev

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No system libraries are needed — PDF generation calls the PDFShift API over HTTPS, and state uses Neon Postgres over a connection string.

**Required `.env` keys to boot** (the app crashes with `KeyError` on startup if any are missing):
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `CRON_SECRET`, `DATABASE_URL`

For `DATABASE_URL` locally, either pull from Vercel (`vercel env pull .env`) or copy the connection string from your Neon dashboard directly.

#### Running the web app locally

```bash
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

#### Smoke-testing PDF generation locally

```bash
PDFSHIFT_API_KEY=sk_... python -m core.pdf /tmp/plan.pdf && open /tmp/plan.pdf
```

Expose port 8000 to Telegram via ngrok for full bot testing:

```bash
ngrok http 8000
curl -F "url=https://<ngrok-id>.ngrok.app/webhook" \
     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"
```

### Deploy to Vercel

Fork this repo, push to GitHub, and connect it to Vercel — auto-deploys on every push to `main`. Platform: Vercel Hobby (free tier), Python ASGI, Git-connected.

To redeploy manually or set up a fork:

```bash
npm i -g vercel      # or: brew install vercel
vercel login
vercel link          # connect local repo to the Vercel project
vercel deploy --prod
```

Secrets are managed in the Vercel dashboard (Settings → Environment Variables). Required keys: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GROQ_API_KEY`, `GROQ_MODEL`, `CRON_SECRET`, `RESEND_API_KEY`, `RESEND_FROM`, `YOUR_EMAIL`, `PDFSHIFT_API_KEY`. `DATABASE_URL` is injected automatically by the Neon Postgres integration.

After a fresh deploy, register the Telegram webhook:

```bash
curl -F "url=https://<your-app>.vercel.app/webhook" \
     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"
```

The Sunday 08:00 UTC cron is in `vercel.json` — no GitHub Actions secrets needed.

### vercel.json

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "crons": [
    {
      "path": "/trigger",
      "schedule": "0 8 * * 0"
    }
  ]
}
```

Vercel makes a **GET** request to `/trigger` and sends `Authorization: Bearer <CRON_SECRET>` automatically. The free (Hobby) tier supports one cron per project firing at most once per day; timing precision is ±59 minutes (acceptable for a weekly Sunday run).

### End-to-end test

```bash
curl https://<app>.vercel.app/trigger \
     -H "Authorization: Bearer ${CRON_SECRET}"
```

Expected within ~10 seconds:
1. Telegram DM with this week's planned schedule.
2. Bot asks for a **voice memo** summarising how each session went.
3. After you send the memo: bot replies with the transcript, then "Generating proposed plan…", then a diff showing next week's loads + a confirmation card (`Confirm & email` / `Re-record`).
4. Tap **Confirm** → email from `RESEND_FROM` with `plan-<week>.pdf` attached, `config/schedule.json` rewritten on the server, check-in archived to `checkin_history`.

### Voice-memo flow

```
/checkin (or Sunday cron → /trigger)
  → bot prints planned schedule
  → user sends voice memo OR plain text message with session notes
  → (voice) Whisper transcribes (~1–3 s) → transcript printed back
  → Llama 3.3 70B applies progression rules → proposed next-week plan
  → bot shows diff (load deltas, set changes, deload banner) + confirmation card
  → [Confirm & email]  →  PDF (PDFShift)  →  email (Resend)  →  schedule rewritten
  → [Re-record]        →  clear transcript, wait for a new memo or text
```

Rules embedded in the LLM system prompt (see `core/prompt.py`):
- Status inference: `as_planned` / `too_easy` / `struggled` / `skipped` per exercise, derived from the transcript.
- Load increments: barbell ±2.5 kg, dumbbell ±1 kg, cable/machine ±2.5 kg, BW+weighted ±1.25 kg, BW-only never changes.
- Deload triggers: 6 consecutive progression weeks, fatigue keywords (joint pain, exhausted, no energy, hurt, deload, etc.), or sustained Strava CNS load (max HR ≥ 95% `USER_MAX_HR`). On deload: keep loads, halve sets, set deload note.

State lives in **Neon Postgres** — three tables:
- `checkin_state` — single active check-in per chat (voice_file_id, transcript, proposed_changes, strava_summary). Deleted on Confirm.
- `checkin_history` — every completed check-in (week_number, schedule_snapshot, transcript, strava_summary). Never cleared.
- `strava_activities` — UPSERT'd cardio activities (id, type, distance, time, HR). Built up over time for future visualizations.

### Schedule config

`config/schedule.json` is the source of truth between weeks. Edit it manually whenever you want to restructure (add a session, drop an exercise). The LLM rewrites it on every Submit to bump loads / reps based on your check-in.

Rules:
- `load_kg: null` = bodyweight or load irrelevant
- `note` is pre-populated context the LLM can read
- Add / remove sessions and exercises freely — the bot reads it at runtime

---

## Troubleshooting

### `Could not determine the application interface for 'main:application'`

Vercel scans `main.py` for a variable named `app` or `application` to use as the ASGI entrypoint. If anything else in the file uses one of those names (e.g. a python-telegram-bot `Application` instance), Vercel grabs the wrong object and crashes. **Never name anything `app` or `application` in `main.py` unless it's the FastAPI instance.** The PTB object is named `ptb_app` for this reason.

### `psycopg.errors.NumericValueOutOfRange: integer out of range` on first trigger

Telegram user and chat IDs are 64-bit integers. Postgres `INTEGER` is 32-bit (max ~2.1 billion). Any column storing a Telegram ID must be `BIGINT`. If you recreate the schema from scratch, the `checkin_state` table already uses `BIGINT PRIMARY KEY` — don't change it back.

### Tables missing at runtime (`relation "X" does not exist`)

psycopg v3's `execute()` runs **one SQL statement per call**. Passing a string with multiple semicolon-separated statements only executes the first one — subsequent tables are silently skipped. `init_db()` calls `execute()` once per table. If you add a new table to the schema, add a new `conn.execute(...)` call for it.

### `Plan generation failed: Expecting value: line 1 column 1 (char 0)` (historical)

This was `json.loads("")` from `gpt-oss-20b` — a reasoning model that consumed the entire `max_tokens` budget on internal reasoning before producing visible `content`. Resolved 2026-06-04 evening by swapping to `llama-3.3-70b-versatile` with strict `json_schema` response_format + Pydantic validation in `core/llm_client.py`. If you see this on a fresh deploy, double-check that `GROQ_MODEL` is set to `llama-3.3-70b-versatile` in Vercel — not `openai/gpt-oss-20b`.

### `INSERT or UPDATE on checkin_state ... null value in column "..." violates not-null constraint`

The `checkin_state` schema was rewritten on 2026-06-04 evening (dropped `results`/`session_idx`/`exercise_idx`/`awaiting_note`, added `voice_file_id`/`transcript`/`proposed_changes`/`strava_summary`). `CREATE TABLE IF NOT EXISTS` is a no-op against the existing table, so the old columns persist until you drop it manually. Fix: in Neon SQL editor, run `DROP TABLE IF EXISTS checkin_state;` once, then redeploy — `init_db()` will recreate it with the new schema. `checkin_history` and `strava_activities` are unaffected.

### Strava call failed in start_checkin

Non-fatal. The bot logs the warning and proceeds without cardio context. Common causes: `STRAVA_REFRESH_TOKEN` invalid (re-run `scripts/strava_oauth.py`), Strava API rate-limited (100 req / 15 min, 1000 / day — we only call once per check-in so this should be impossible), or `STRAVA_CLIENT_*` env vars unset (the refresh request will 401).

### Vercel logs show old WeasyPrint errors

Vercel's Logs tab shows entries from all deployments, not just the latest. A `libpango-1.0-0: cannot open shared object file` error is from a pre-migration deployment. Filter by the current deployment or check the timestamp — anything before commit `30787e5` (2026-06-04) is obsolete.

---

## LLM + ASR design (System B)

**Planner — `core/llm_client.py`** calls **`llama-3.3-70b-versatile`** on Groq with `response_format={"type":"json_schema","json_schema":PLAN_JSON_SCHEMA}` (strict mode). The response is parsed and validated against a Pydantic `WeeklyPlan` model before being returned. Strict mode guarantees the response either matches the schema or the API errors — eliminates the `json.loads("")` class of failures that bit `gpt-oss-20b` (see Troubleshooting).

**System prompt** (`core/prompt.py`) carries the entire progression rule set: status inference, per-exercise-type load increments, deload triggers (6-week progression cap, fatigue keywords, Strava CNS-load signal). The LLM is both parser *and* executor — user voice-memo notes can naturally override the defaults ("shoulder felt off, going down 2.5" beats `as_planned` → `+2.5 kg`).

**Why not a pure rule engine?** A separate rule engine adds ~150 LOC, requires per-exercise type tagging in `config/schedule.json`, and can't read free-form voice notes — which is exactly the signal we want. The LLM is cheap enough (~$0.003 per Sunday run) that the determinism trade-off is acceptable.

**Transcription — `core/transcribe.py`** uses **`whisper-large-v3-turbo`** on Groq (~250× real-time, ~$0.04/hr). Telegram voice memos arrive as Ogg Opus; Whisper accepts them directly. Language is auto-detected (no hint required for English/German/Turkish/etc).

**Failure surface:**
- `RuntimeError("GROQ_API_KEY is not set")` — env var missing.
- `RuntimeError("LLM returned empty content. finish_reason=…")` — should be impossible with strict mode + non-reasoning model, but defended against just in case.
- `RuntimeError("LLM JSON failed schema validation: …")` — Pydantic caught a shape mismatch; surfaced verbatim in the Telegram error message.

## Strava integration

`core/strava.py` handles the cardio + heart-rate ingestion side. **Not** used as a source of truth for strength work (Strava has no concept of sets/reps/loads); used as a passive enrichment layer for the LLM prompt and the confirmation card.

**Flow each Sunday:**
1. `start_checkin` calls `refresh_access_token()` (cached for the 6-hour TTL Strava grants) → `fetch_recent_activities(days=7)`.
2. Activities are UPSERT'd into `strava_activities` (BIGINT primary key = Strava activity ID).
3. `summarize()` builds a digest: count, total km, total moving minutes, per-activity (type, distance, avg/max HR), and an `hr_flags` list flagging any activity with max HR ≥ 95% of `USER_MAX_HR`.
4. Digest is stored in `checkin_state.strava_summary`, shown in the Telegram preview, and threaded into the LLM prompt as additional context.

Strava call failures are **non-fatal** — the bot logs a warning and proceeds without cardio context. The check-in still works without Strava configured at all (leave `STRAVA_*` env vars unset).

**One-time auth:** run `python3 scripts/strava_oauth.py` locally after putting `STRAVA_CLIENT_ID` + `STRAVA_CLIENT_SECRET` in `.env`. The script opens your browser, catches the OAuth callback on `localhost:8765`, and prints the refresh token to paste into Vercel. Refresh tokens don't expire unless you revoke the app or change scopes — so this is genuinely once.

---

## Newsletter (Light Weight)

The Sunday email is the **Light Weight** weekly newsletter — a 600 px branded email rendered from `templates/newsletter.html`. Source design: `DESIGN-Weekly-Science-Newsletter/newsletter-hifi.jsx` (hi-fi variant).

**Brand:** "**LIGHT WEIGHT.**" — BVB black + volt-yellow (`#FDE100`), Bebas Neue display, Archivo body, JetBrains Mono spec. Same visual language as the printed PDF; different layout (rounded cards instead of cut-out stickers).

**Structure per issue:**
1. **Masthead** — issue number + date.
2. **Deload strip** (conditional) — when the LLM detects deload triggers.
3. **Hero photo** — copyright-free gym shot, rotated deterministically by `issue_number % len(pool)`.
4. **Science fact** — one curated fact + citation + "why it matters" copy.
5. **Last week recap** — 3 stat tiles (sessions, +kg added, skipped) + biggest-jump line.
6. **This week's plan** — 4 day rows with top set + load (deload markers when applicable).
7. **Download CTA** — signed URL to re-rendered PDF.
8. **Footer** — voice-memo reminder + unsubscribe + archive links.

**Code map:**
- `templates/newsletter.html` — Jinja2 email body. Inline CSS, `<table>` layout, Outlook-safe.
- `core/newsletter.py` — `build_context(this_week, next_week, transcript, issue_number, fact, hero, cta_href)` builds the template dict (recap math, top-set picker, subject, preheader).
- `core/email.py` — `send_newsletter(...)` picks the fact + hero, signs the CTA URL, renders the template, ships through Resend with PDF attachment + plain-text fallback. Returns the picked `fact_id` so `_on_confirm` can persist it.
- `core/facts.py` + `data/facts.json` — 25 curated facts (citation, "why it matters", deload-safe flag, tag list). `pick_fact()` filters deload-unsafe entries, prefers unused IDs, then tag-matches against the transcript. No LLM in the picker.
- `core/hero.py` + `assets/hero/01.jpg` … `12.jpg` — deterministic rotation by issue number. Photos are 2.5:1 (1200×480), ≤ 150 KB each.
- `core/signing.py` — `sign_week(n)` / `verify_week(n, t)`. HMAC-SHA256 with `CRON_SECRET`, 16-hex-char truncation.
- `bot/handlers.py:_on_confirm` — loads `this_week` *before* `save_schedule`, pulls `recent_fact_ids(limit=8)` for the picker's used-window, calls `send_newsletter`, persists `used_fact_id` + `schedule_snapshot = next_week`.
- `bot/state.py` — `checkin_history.used_fact_id` column, `recent_fact_ids()` helper, `get_history_by_week()` helper.
- `scripts/test_newsletter.py` — local dry-run renderer (browser preview) + optional `--send` for live Resend delivery.

**Endpoints:**
- `GET /plan/{week_number}.pdf?t=<hmac>` — re-renders the PDF from `checkin_history.schedule_snapshot` and streams it back. 403 on bad token, 404 on unknown week.
- `/static/hero/` — `StaticFiles` mount over `assets/hero/`. The newsletter `<img src>` tags resolve here.

**Env var:** `APP_BASE_URL` (e.g. `https://gym-research.vercel.app`). The hero URL and CTA URL are built by prepending this to the relative path. Falls back gracefully when unset, but emails will be missing pieces — set it in Vercel before the first real Sunday cron.

**Schema bumps:**
- `PLAN_JSON_SCHEMA` per-exercise `status` field (`as_planned` / `too_easy` / `struggled` / `skipped`) — recap math reads from it.
- `checkin_history.used_fact_id TEXT NULL` — repeat-avoidance window for the fact picker.

**Smoke-test:**
```bash
python3 scripts/test_newsletter.py                # render to /tmp + open in browser
python3 scripts/test_newsletter.py --deload       # deload variant
python3 scripts/test_newsletter.py --issue 22     # specific issue (controls hero rotation)
python3 scripts/test_newsletter.py --send         # real Resend send to YOUR_EMAIL
```

### Future vision — multi-tenant trajectory

This is single-tenant by design today (one Telegram bot, one chat ID, one inbox). The product is good enough that friends will ask to be on the list — here's how that grows without forcing them through the Telegram + API-key + Vercel onboarding the maintainer went through.

**Stage 0 — Manual onboarding (now).** A friend asks to subscribe. The maintainer:
- adds their email to a `users` table (Phase v1 work);
- types in their starting plan + weights;
- ferries their weekly voice memo via whatever channel they actually use (WhatsApp voice forward, audio file in iMessage, anything).

Trade-off: zero friction for the friend, all friction on the maintainer. Caps at maybe 3–5 friends before this becomes annoying. **Right answer until at least one friend says "I want this every week, no questions" — that's the signal to invest in self-serve.**

**Stage 1 — Self-serve web (v2).** Landing page + email signup + plan-template picker + magic-link verification. Engine stays the same; only the onboarding surface is new. Voice memos still need a delivery channel — this stage assumes the friend can email an attachment, type their notes, or DM them somewhere the maintainer reads.

**Stage 2 — Browser check-in (v3).** Sunday email carries a magic link → web page with their plan inline + a record button (browser `MediaRecorder` API) + a typed-text fallback. Upload → same Whisper → same LLM → same newsletter. No app to install, no Telegram, no friction on either side beyond an email click. Engine unchanged.

**Stage 3 — Mobile app (eventual pivot).** When the value proposition is clear and the audience is asking, fold the whole flow into a single app:
- Onboarding becomes a guided wizard (plan templates, body metrics, goals).
- Weekly check-in is a tap-to-record inside the app — no email, no browser, no signed link.
- The PDF goes away entirely — the plan lives in-app, with a printable export only if the user wants it. The 2×2 sticker-card layout becomes redundant once the app *is* the workout log.
- Telegram + email + PDFShift + Resend collapse into one product surface. Cheaper to run, cleaner mental model, easier to grow.

At this point the engine we just built — fact picker, newsletter template, LLM progression rules, PDF endpoint — is no longer the product, it's the back-end of a real consumer app. The hard work was getting the *content* right (the fact pool, the coach voice, the recap math). That carries forward whatever the shipping surface becomes.

**Don't pre-build for stage 3.** Each stage is only justified when the previous one breaks. Going straight to a mobile app before stages 1 and 2 means building the wrong product without ever seeing whether the newsletter format alone is enough.

### Future scaling — when "render on click" stops being free

The signed-PDF endpoint re-renders the PDF on every click via PDFShift. That's right-sized for v1 (one subscriber, ~4 clicks/month — well under PDFShift's 50/month free tier) and gives a permanent archive: every past issue's CTA stays alive forever at a stable URL.

If this ever ships to more subscribers, the per-click render becomes the bottleneck (cost + latency). The migration path at that point:

1. **Render once on Confirm**, immediately after the LLM rewrites the plan.
2. **Cache the PDF** to durable storage — Vercel Blob, Cloudflare R2, or any S3-compatible bucket — keyed by `(week_number, hash(schedule_snapshot))` so a re-issue of the same plan is a no-op.
3. **CTA points at the blob URL** with a long-lived signed URL or via the existing `/plan/{n}.pdf` endpoint switched to "fetch + stream from blob" instead of "render via PDFShift".
4. **Endpoint becomes a thin proxy** with caching headers (`Cache-Control: public, max-age=31536000, immutable`) so CDN edges hold the file and PDFShift is hit ~zero times.

The HMAC token logic doesn't change — it still gates which week_number the caller is allowed to fetch. Only the *source* of the PDF bytes flips from "render now" to "read from blob".

Trigger condition: noticeable PDFShift quota pressure, or any subscriber count > ~5 with > 1 click/week per user.

---

## System A (retired)

System A — the original Sunday-email tracker — was retired on 2026-06-03. The cloud routine `trig_01XUTpwZgjKkJw6VDq4HpZSh` is permanently disabled (its Bridge environment was lost) and renamed `Weekly Gym Progress Update (RETIRED 2026-06-03)`. Source code, the final `progress_log.json` snapshot, and the original routine prompt are preserved in `legacy_email/` for reference — see `legacy_email/README.md` for the rationale and `CLAUDE.md` for the original algorithm + research foundation.

Scripts in `legacy_email/` still run locally (paths were rewritten to be relative to the folder) — `python3 legacy_email/weekly_gym_update.py status`, etc. — but there's no automation behind them anymore.

---

## Deployment checklist (System B)

**Infra (done):**
1. ☑ `config/schedule.json` seeded with real Upper/Lower routine (Mon/Wed/Fri/Sat)
2. ☑ `core/pdf.py` — PDFShift API (no system libs)
3. ☑ `bot/state.py` — Neon Postgres (`psycopg` v3, `JSONB`, BIGINT chat_id, one execute() per CREATE TABLE)
4. ☑ `main.py` — no lifespan, `async with ptb_app:` per-invocation, GET `/trigger`, `CRON_SECRET`
5. ☑ `vercel.json` — cron `0 8 * * 0` → GET `/trigger`
6. ☑ Vercel project (`gym-research`), GitHub auto-deploy, Neon integration (`neon-cyan-nest`)
7. ☑ Telegram webhook registered against `gym-research.vercel.app`

**Refactor (2026-06-04 evening, commit `b8c8a05`):**
8. ☑ LLM swap: `gpt-oss-20b` → `llama-3.3-70b-versatile`, `json_object` + Pydantic validation
9. ☑ Whisper added: `core/transcribe.py` with `whisper-large-v3-turbo`
10. ☑ Button-tap UI deleted; replaced with voice + text `MessageHandler` + Confirm/Re-record card

**2026-06-08:**
11. ☑ Strava integration removed — voice/text only flow
12. ☑ `scripts/test_plan.py` — local smoke-test for plan generation
13. ☑ End-to-end verified from Telegram

**2026-06-09 — print layout for pocket-notebook glue-in:**
14. ☑ PDF switched to **A4 landscape** with all 4 workouts on page 1 in a 2×2 grid, page 2 = 8 run stickers in a 4×2 grid. Each workout card is ~134mm × 85mm — cut along the 6mm grid gap (one horizontal + one vertical cut) and glue into a notebook (max ~140mm wide).
15. ☑ Layout constants (`PAGE_WIDTH_MM`, `PAGE_HEIGHT_MM`, `PAGE_MARGIN_MM`, `GRID_GAP_MM`, `TABLE_WIDTH_MM`, `TABLE_HEIGHT_MM`) live at the top of `core/pdf.py` and are threaded into `templates/plan.html` via Jinja context — single source of truth.
16. ☑ PDFShift API call passes `"format": "A4", "landscape": True` explicitly — CSS `@page size` alone is unreliable for orientation (PDFShift silently defaults to A4 portrait without it).

(System A is already retired — no coexistence conflict.)

---

## Contributing

PRs are welcome. This is designed to be forkable — the entire bot is ~500 LOC across `bot/`, `core/`, and `main.py`.

### 1. Set your git identity before your first commit

Set your identity *per-repo* right after cloning so commits are attributed to your GitHub account:

```bash
git clone https://github.com/<you>/gym-progression-bot.git
cd gym-progression-bot
git config user.name  "<your GitHub username>"
git config user.email "<email verified on your GitHub account>"
```

### 2. Branching and PRs

- `main` is the deploy branch — every push to `main` triggers a production Vercel deploy.
- For non-trivial changes, open a PR from a feature branch (`feat/...`, `fix/...`, `docs/...`). Vercel creates a preview deployment per PR — check it before merging.
- Direct pushes to `main` are fine for docs-only or one-line config fixes.

### 3. Pre-push checklist

- `python -m py_compile $(git diff --name-only --cached | grep '\.py$')` — every committed `.py` file must compile.
- `.env` is in `.gitignore` and must stay there. Never commit secrets.
- If you change `bot/state.py` schema, remember psycopg v3 = **one statement per `execute()` call** (one `conn.execute(...)` per `CREATE TABLE`).
- If you change anything in `main.py`, do NOT name a variable `app` or `application` unless it's the FastAPI instance (see Troubleshooting → ASGI entrypoint).
- For UI/PDF changes, render locally with `python -m core.pdf /tmp/plan.pdf` before pushing.
- For LLM prompt changes, run `python3 scripts/test_plan.py` before pushing.

### 4. Services you need to set up (all free tiers are sufficient)

| Service | Purpose | Sign up |
|---|---|---|
| Vercel | Hosting + cron | vercel.com |
| Neon Postgres | State + history | neon.tech (connect via Vercel integration) |
| Groq | Llama 3.3 70B + Whisper | console.groq.com |
| PDFShift | PDF rendering (50/mo free) | pdfshift.io |
| Resend | Email delivery | resend.com — **requires a verified custom domain** |
| Telegram bot | Conversation channel | @BotFather on Telegram |

### 5. Email setup — custom domain required

`onboarding@resend.dev` (Resend's shared sandbox) is **not suitable for production**: it can only deliver to the Resend account owner's email and is silently dropped by iCloud. You need a verified custom domain:

1. Register any cheap domain (`.xyz` costs ~€0.57/yr on Namecheap).
2. Add it to Resend → Domains. Resend gives you DKIM, SPF, and DMARC DNS records to paste into your registrar.
3. Set `RESEND_FROM=you@yourdomain.com` in Vercel env vars.

### 6. Where to look next

- **Architecture and constraints** → `CLAUDE.md`
- **Why we made specific migration choices** (Railway → Vercel, WeasyPrint → PDFShift, SQLite → Neon) → `notes/system-b-history.md`
- **System A (retired rule engine)** → `legacy_email/README.md`
