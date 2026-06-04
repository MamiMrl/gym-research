# gym-research

Automated weekly gym progression tracker. The active system is **System B** (Telegram bot, gpt-oss-20b on Groq, PDF emailed weekly). System A — the original email-based tracker — was **retired on 2026-06-03** and lives in `legacy_email/` for reference only.

| | System A (retired) | System B (current) |
|---|---|---|
| **Channel** | Email reply | Telegram conversation |
| **LLM** | None (rule-based) | `openai/gpt-oss-20b` on Groq (with optional primary fallback) |
| **Output** | HTML email + printable plan | PDF attached to email (via Resend) |
| **Trigger** | Cloud routine `trig_01XUTpwZgjKkJw6VDq4HpZSh`, Sundays 08:00 Berlin | Vercel cron (via `vercel.json`), Sundays 08:00 UTC → GET `/trigger` |
| **Code** | `legacy_email/` | `main.py`, `bot/`, `core/`, `config/`, `templates/`, `vercel.json` |
| **Status** | ☠ Retired 2026-06-03 (routine permanently disabled, env lost) | 🟡 Deployed on Vercel, webhook registration pending (as of 2026-06-04) |
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
│   ├── keyboards.py           Inline keyboards (status + submit)
│   └── state.py               Neon Postgres per-chat check-in state + history
├── core/
│   ├── schedule.py            Load/save config/schedule.json
│   ├── prompt.py              System prompt + per-week prompt builder
│   ├── llm_client.py          gpt-oss-20b (primary) → Groq (fallback)
│   ├── pdf.py                 Jinja2 render → PDFShift API → PDF bytes
│   └── email.py               Resend send w/ base64 PDF attachment
├── config/schedule.json       The weekly plan (LLM rewrites this on submit)
├── templates/plan.html        Jinja2 A4 PDF template
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

# LLM — Groq is the current sole provider (gpt-oss-20b at $0.10/$0.50 per M tokens, ~1000 tok/s).
# Sign up at console.groq.com and paste the key here.
GROQ_API_KEY=gsk_...
GROQ_MODEL=openai/gpt-oss-20b                # optional override, verified against Groq docs

# LLM — optional primary (any other OpenAI-compatible host serving gpt-oss-20b).
# Leave these unset to call Groq directly. If set, the code calls the primary first
# and falls back to Groq on error or timeout.
# OSS_BASE_URL=https://openrouter.ai/api/v1   # e.g. OpenRouter, Fireworks, vLLM, local Ollama
# OSS_API_KEY=...
# OSS_MODEL=openai/gpt-oss-20b
# OSS_TIMEOUT_S=60

# PDF generation — PDFShift managed API (50 free conversions/month, no system libs needed)
# Sign up at pdfshift.io, copy the sk_... key.
PDFSHIFT_API_KEY=sk_...

# Database — Neon Postgres (injected automatically by the Vercel–Neon integration)
# For local dev: copy the DATABASE_URL from your Neon dashboard or run `vercel env pull`.
DATABASE_URL=postgresql://...

# Email
RESEND_API_KEY=re_...
RESEND_FROM=onboarding@resend.dev            # Resend sandbox sender (no custom domain needed)
YOUR_EMAIL=mami.maral@icloud.com

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

The project is deployed at **`https://gym-research.vercel.app`** via the `MamiMrl/gym-research` GitHub repo (auto-deploys on every push to `main`). Platform: Vercel Hobby (free tier), Python ASGI, Git-connected.

To redeploy manually or set up a fork:

```bash
npm i -g vercel      # or: brew install vercel
vercel login
vercel link          # connect local repo to the Vercel project
vercel deploy --prod
```

Secrets are managed in the Vercel dashboard (Settings → Environment Variables). Required keys: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GROQ_API_KEY`, `GROQ_MODEL`, `CRON_SECRET`, `RESEND_API_KEY`, `RESEND_FROM`, `YOUR_EMAIL`, `PDFSHIFT_API_KEY`. `DATABASE_URL` is injected automatically by the Neon Postgres integration (Storage tab → neon-cyan-nest).

After a fresh deploy, register the Telegram webhook:

```bash
curl -F "url=https://gym-research.vercel.app/webhook" \
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
1. Telegram DM starts the check-in conversation.

2. Tap through each exercise → **Submit**.
3. "Generating next week's plan…" message in Telegram.
4. Email from `RESEND_FROM` with `plan-<week>.pdf` attached.
5. `config/schedule.json` is rewritten with the LLM's adjusted plan (on the server).

### Conversation flow

```
/checkin (or Sunday cron → /trigger)
  → session header: "Monday — Push"
  → for each exercise: [As planned] [Too easy] [Struggled] [Skipped]
  → "Any note? (or Skip)"  ← optional free-text reply
  → next exercise, next session
  → [Submit] → LLM → PDF → Resend → confirmation in Telegram
```

State lives in **Neon Postgres** (two tables: `checkin_state` for the active session, `checkin_history` for all completed check-ins). One row per active check-in keyed by `chat_id`, deleted on submit. History is never cleared — the LLM can use it for future context.

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

### Vercel logs show old WeasyPrint errors

Vercel's Logs tab shows entries from all deployments, not just the latest. A `libpango-1.0-0: cannot open shared object file` error is from a pre-migration deployment. Filter by the current deployment or check the timestamp — anything before commit `30787e5` (2026-06-04) is obsolete.

---

## LLM design (System B)

`core/llm_client.py` calls **`openai/gpt-oss-20b`** (OpenAI's open-weight 21B-param model) via any OpenAI-compatible endpoint. The current deployment uses **Groq** as the sole provider — fast (~1000 tok/s), cheap ($0.10/$0.50 per M tokens), and reliable enough that a fallback isn't needed for once-a-week traffic.

The code still supports a primary/fallback split (set `OSS_BASE_URL` + `OSS_API_KEY` to add a primary in front of Groq); the fallback kicks in on any `OpenAIError`, `json.JSONDecodeError`, or `ValueError` from the primary, with a default 60s timeout. Useful if you later self-host on Ollama / vLLM and want Groq as the safety net.

**Model ID on Groq:** `openai/gpt-oss-20b` (verified against [Groq docs](https://console.groq.com/docs/model/openai/gpt-oss-20b), 2026-06-03). Same ID works on most other hosts.

**Failure surface:** any `openai.OpenAIError`, `json.JSONDecodeError`, or `ValueError` from the primary trips the fallback. If `GROQ_API_KEY` isn't set, the call raises `RuntimeError` and the bot tells you "Plan generation failed".

**JSON parsing:** `response_format` was removed after Groq's `json_object` mode returned empty responses in production. The system prompt instructs JSON-only output; the client strips markdown fences defensively. If you see malformed JSON, Groq's strict `json_schema` mode is the next step — see [Groq Structured Outputs](https://console.groq.com/docs/structured-outputs) (incompatible with streaming/tool use; requires `additionalProperties: false` and all keys in `required`).

---

## System A (retired)

System A — the original Sunday-email tracker — was retired on 2026-06-03. The cloud routine `trig_01XUTpwZgjKkJw6VDq4HpZSh` is permanently disabled (its Bridge environment was lost) and renamed `Weekly Gym Progress Update (RETIRED 2026-06-03)`. Source code, the final `progress_log.json` snapshot, and the original routine prompt are preserved in `legacy_email/` for reference — see `legacy_email/README.md` for the rationale and `CLAUDE.md` for the original algorithm + research foundation.

Scripts in `legacy_email/` still run locally (paths were rewritten to be relative to the folder) — `python3 legacy_email/weekly_gym_update.py status`, etc. — but there's no automation behind them anymore.

---

## Deployment checklist (System B)

1. ☑ `config/schedule.json` seeded with real Upper/Lower routine (Mon/Wed/Fri/Sat)
2. ☑ LLM JSON fix: removed `response_format=json_object`; client strips markdown fences
3. ☑ `core/pdf.py` — WeasyPrint replaced with PDFShift API (`httpx` POST, `X-API-Key` header)
4. ☑ `bot/state.py` — SQLite replaced with Neon Postgres (`psycopg` v3, `JSONB` columns)
5. ☑ `main.py` — no lifespan, `async with ptb_app:` per-invocation, GET `/trigger`, `CRON_SECRET`
6. ☑ `vercel.json` — cron `0 8 * * 0` → GET `/trigger`
7. ☑ Vercel project created (`gym-research`), GitHub auto-deploy connected, all secrets set
8. ☑ Neon Postgres integration connected (`neon-cyan-nest`) — `DATABASE_URL` auto-injected
9. ☑ Vercel entrypoint fix: PTB `Application` renamed to `ptb_app` (was colliding with Vercel's `application` ASGI detection)
10. ☑ `chat_id` column type fixed: `INTEGER` → `BIGINT` (Telegram IDs are 64-bit)
11. ☑ `init_db()` fixed: split multi-statement schema into two separate `execute()` calls; `_conn()` now a proper context manager that closes the connection
12. ☑ Telegram webhook registered against `gym-research.vercel.app`
13. ☐ End-to-end test: `curl https://gym-research.vercel.app/trigger -H "Authorization: Bearer ${CRON_SECRET}"`

(System A is already retired — no coexistence conflict.)
