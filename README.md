# gym-research

Automated weekly gym progression tracker. The active system is **System B** (Telegram bot, gpt-oss-20b on Groq, PDF emailed weekly). System A — the original email-based tracker — was **retired on 2026-06-03** and lives in `legacy_email/` for reference only.

| | System A (retired) | System B (current) |
|---|---|---|
| **Channel** | Email reply | Telegram conversation |
| **LLM** | None (rule-based) | `openai/gpt-oss-20b` on Groq (with optional primary fallback) |
| **Output** | HTML email + printable plan | PDF attached to email (via Resend) |
| **Trigger** | Cloud routine `trig_01XUTpwZgjKkJw6VDq4HpZSh`, Sundays 08:00 Berlin | Vercel cron (via `vercel.json`), Sundays 08:00 UTC → `/trigger` |
| **Code** | `legacy_email/` | `main.py`, `bot/`, `core/`, `config/`, `templates/`, `vercel.json`, `.github/` |
| **Status** | ☠ Retired 2026-06-03 (routine permanently disabled, env lost) | 🟡 Code complete, pending Vercel deploy (Railway → Fly.io → Vercel migration, as of 2026-06-04) |
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
├── # ── System B (Telegram bot, deploys to Railway) ──
├── main.py                    FastAPI app: GET /, POST /webhook, POST /trigger
├── requirements.txt
├── Dockerfile                 Python 3.12 slim + Pango/Cairo for WeasyPrint
├── Procfile                   Buildpack-host fallback
├── railway.json               Railway service config
├── bot/
│   ├── handlers.py            Telegram conversation flow (check-in → submit)
│   ├── keyboards.py           Inline keyboards (status + submit)
│   └── state.py               SQLite per-chat check-in state + history
├── core/
│   ├── schedule.py            Load/save config/schedule.json
│   ├── prompt.py              System prompt + per-week prompt builder
│   ├── llm_client.py          gpt-oss-20b (primary) → Groq (fallback)
│   ├── pdf.py                 Jinja2 + WeasyPrint render
│   └── email.py               Resend send w/ base64 PDF attachment
├── config/schedule.json       The weekly plan (LLM rewrites this on submit)
├── templates/plan.html        Jinja2 A4 PDF template
├── .github/workflows/checkin.yml   Sunday 08:00 UTC → POST /trigger
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

# Email
RESEND_API_KEY=re_...
RESEND_FROM=workout@yourdomain.com           # must be on a verified Resend domain
YOUR_EMAIL=you@example.com

# Trigger auth
TRIGGER_SECRET=<random; openssl rand -hex 16>
```

GitHub Actions secrets (for the cron):

```bash
BOT_TRIGGER_URL=https://<your-app>.fly.dev/trigger   # or whatever host you deploy to
TRIGGER_SECRET=<same value as in .env>
```

### Local dev

#### macOS — WeasyPrint system libs

WeasyPrint (the PDF renderer) requires native system libraries. If you use the
Python.org installer (`/Library/Frameworks/Python.framework/...`), macOS SIP
strips `DYLD_*` env vars and Pango/Cairo can never be found regardless of
whether brew has them. **Use Homebrew's Python instead:**

```bash
brew install python@3.13 pango   # pango pulls in cairo, glib, gobject

# Create a project venv backed by the Homebrew Python
/opt/homebrew/bin/python3.13 -m venv .venv
source .venv/bin/activate        # run this every time you open a new terminal
pip install -r requirements.txt
```

Verify WeasyPrint works before going further:

```bash
python -m core.pdf /tmp/plan.pdf && open /tmp/plan.pdf
```

If you prefer not to change your global Python setup, run the app in Docker
instead — the Dockerfile installs the right system libs via apt and matches
the production environment exactly:

```bash
docker build -t gym-research .
docker run --rm -p 8000:8000 --env-file .env gym-research
```

#### Running the web app locally

```bash
source .venv/bin/activate        # if not already active
uvicorn main:app --reload --port 8000
```

`main.py` reads all env vars from `.env` at startup via `load_dotenv()`. The
minimum required keys to boot are `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`,
and `TRIGGER_SECRET` — the app will crash with a `KeyError` at startup for any
of these that are missing.

Expose port 8000 to Telegram via ngrok for full bot testing:

```bash
ngrok http 8000
curl -F "url=https://<ngrok-id>.ngrok.app/webhook" \
     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"
```

### Deploy to Vercel

Railway (credits exhausted) and Fly.io were both attempted or considered before settling on **Vercel** — serverless, zero-ops, free tier, Git-connected.

**Before deploying, two code changes are required** (see "Required changes" below):

```bash
npm i -g vercel      # or: brew install vercel
vercel login
vercel link          # connects local repo to Vercel project

# Set all secrets (use vercel env add NAME production < file to avoid shell history)
vercel env add TELEGRAM_BOT_TOKEN production
vercel env add TELEGRAM_CHAT_ID production
vercel env add GROQ_API_KEY production
vercel env add GROQ_MODEL production      # openai/gpt-oss-20b
vercel env add CRON_SECRET production     # replaces TRIGGER_SECRET; Vercel injects this on cron calls
vercel env add RESEND_API_KEY production
vercel env add RESEND_FROM production     # onboarding@resend.dev
vercel env add YOUR_EMAIL production      # mami.maral@icloud.com

vercel deploy --prod
```

After deploy, copy the production URL (e.g. `https://<app>.vercel.app`) and register the Telegram webhook:

```bash
curl -F "url=https://<app>.vercel.app/webhook" \
     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"
```

The Sunday 08:00 UTC cron is configured in `vercel.json` (see below) — no GitHub Actions secret needed.

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

State lives in `state.db` (SQLite, single file). One row per active check-in keyed by `chat_id`, deleted on submit. History is appended to `checkin_history` and never cleared — the LLM can use it for future context.

> **Vercel note:** SQLite file writes do not persist between serverless function invocations. Before deploying, migrate `state.db` to a hosted database — Neon (Postgres) is the recommended choice (free tier, SQL-compatible, auto-provisioned via `vercel install neon`). Upstash (Redis) is a lighter alternative if you prefer a key-value model.

### Schedule config

`config/schedule.json` is the source of truth between weeks. Edit it manually whenever you want to restructure (add a session, drop an exercise). The LLM rewrites it on every Submit to bump loads / reps based on your check-in.

Rules:
- `load_kg: null` = bodyweight or load irrelevant
- `note` is pre-populated context the LLM can read
- Add / remove sessions and exercises freely — the bot reads it at runtime

### Required changes before deploying to Vercel

Vercel's serverless runtime has two hard constraints that require code changes:

**1. PDF generation — WeasyPrint is not viable**

Vercel Python functions have no mechanism to install system packages (`apt-get`). WeasyPrint depends on Pango, Cairo, HarfBuzz, and ~15 other native `.so` libraries that cannot be bundled practically. Replace `core/pdf.py` with one of:

| Option | Effort | Fidelity |
|--------|--------|----------|
| **PDFShift** (managed API) | Low — swap `core/pdf.py` to HTTP POST | High — renders the existing Jinja2 HTML template unchanged |
| **Gotenberg** (self-hosted Docker) | Medium — run Gotenberg as a sidecar or on Fly.io | High — same HTML/CSS |
| **reportlab / fpdf2** (pure Python) | Medium — rewrite template as code | Lower — loses CSS styling |

PDFShift is the fastest path: send the rendered HTML string to `https://api.pdfshift.io/v3/convert/pdf`, receive bytes back, attach to Resend email. Free tier: 50 conversions/month.

**2. State persistence — SQLite does not survive between invocations**

`bot/state.py` writes to `state.db` on disk. On Vercel each request may land on a fresh container. Migrate to:

- **Neon (Postgres)** — closest to SQLite semantics, free tier (~0.5 GB), provisioned via `vercel install neon` (injects `DATABASE_URL` automatically). Swap `sqlite3` calls to `psycopg2` or `asyncpg`.
- **Upstash (Redis)** — simpler if you flatten check-in state to JSON blobs per `chat_id`. Free tier: 10,000 commands/day.

**3. `/trigger` endpoint — must accept GET and verify `CRON_SECRET`**

Vercel cron makes a **GET** request (not POST) and sends `Authorization: Bearer <CRON_SECRET>`. Update `main.py`:

```python
@app.get("/trigger")
async def trigger(request: Request):
    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {os.environ['CRON_SECRET']}":
        raise HTTPException(status_code=401)
    ...
```

**4. GitHub Actions cron — no longer needed**

`vercel.json` replaces `.github/workflows/checkin.yml` for the weekly trigger. The workflow file can be removed or kept as a manual-dispatch fallback.

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

## Deployment checklist (System B, picking up where we left off)

1. ☑ All env vars set in `.env` — `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GROQ_API_KEY`, `GROQ_MODEL`, `TRIGGER_SECRET`, `RESEND_API_KEY`, `RESEND_FROM` (`onboarding@resend.dev`), `YOUR_EMAIL` (`mami.maral@icloud.com`)
2. ☑ Local PDF smoke-test passed (2026-06-03)
3. ☑ `config/schedule.json` seeded with real Upper/Lower routine (Mon/Wed/Fri/Sat) — see `CLAUDE.md` session history for current weights
4. ☑ Pushed to GitHub
5. ☑ Railway attempted — exhausted credits during initial deploy loops
6. ☑ LLM JSON fix: removed `response_format=json_object` (caused empty responses on Groq); client now strips markdown fences instead
7. ☑ Platform decision: Vercel (2026-06-04) — replaces Fly.io; serverless Python ASGI, built-in cron, free tier
8. ☐ Replace WeasyPrint in `core/pdf.py` with a managed PDF API (PDFShift recommended) — native system libs unavailable on Vercel
9. ☐ Migrate `bot/state.py` from SQLite to Neon Postgres (or Upstash Redis) — file writes don't persist across invocations
10. ☐ Update `/trigger` in `main.py` to accept GET and verify `Authorization: Bearer <CRON_SECRET>`
11. ☐ Add `vercel.json` with cron config (`0 8 * * 0` → `/trigger`)
12. ☐ Deploy: `vercel deploy --prod`, set secrets via `vercel env add ... production`
13. ☐ Register Telegram webhook against the Vercel deployment URL
14. ☐ Fire cron manually (`curl <url>/trigger -H "Authorization: Bearer <CRON_SECRET>"`) and verify end-to-end

(System A is already retired, so there's no coexistence conflict to worry about.)
