# gym-research

Automated weekly gym progression tracker. The active system is **System B** (Telegram bot, gpt-oss-20b on Groq, PDF emailed weekly). System A — the original email-based tracker — was **retired on 2026-06-03** and lives in `legacy_email/` for reference only.

| | System A (retired) | System B (current) |
|---|---|---|
| **Channel** | Email reply | Telegram conversation |
| **LLM** | None (rule-based) | `openai/gpt-oss-20b` on Groq (with optional primary fallback) |
| **Output** | HTML email + printable plan | PDF attached to email (via Resend) |
| **Trigger** | Cloud routine `trig_01XUTpwZgjKkJw6VDq4HpZSh`, Sundays 08:00 Berlin | GitHub Actions cron, Sundays 08:00 UTC → Railway `/trigger` |
| **Code** | `legacy_email/` | `main.py`, `bot/`, `core/`, `config/`, `templates/`, `Dockerfile`, `.github/` |
| **Status** | ☠ Retired 2026-06-03 (routine permanently disabled, env lost) | 🟡 Code complete, not yet deployed (as of 2026-06-03) |
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

Set locally in `.env` and in Railway's service variables:

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
BOT_TRIGGER_URL=https://your-app.up.railway.app/trigger
TRIGGER_SECRET=<same value as on Railway>
```

### Local dev

```bash
pip install -r requirements.txt

# WeasyPrint needs system libs on macOS:
brew install pango cairo gdk-pixbuf libffi

# Smoke-test the PDF renderer:
python3 -m core.pdf /tmp/plan.pdf && open /tmp/plan.pdf

# Run the web app:
uvicorn main:app --reload --port 8000
```

Expose port 8000 to Telegram via ngrok:

```bash
ngrok http 8000
curl -F "url=https://<ngrok-id>.ngrok.app/webhook" \
     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"
```

### Deploy to Railway

1. Push to GitHub.
2. New Railway project → Deploy from GitHub → pick this repo. Railway detects the Dockerfile.
3. Add every env var from the block above to the Railway service.
4. After first deploy, copy the public URL (e.g. `https://workout.up.railway.app`).
5. Register the Telegram webhook against that URL:
   ```bash
   curl -F "url=https://workout.up.railway.app/webhook" \
        "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"
   ```
6. Add `BOT_TRIGGER_URL` and `TRIGGER_SECRET` to GitHub Actions secrets.
7. Trigger the workflow manually from the Actions tab to verify the cron path end-to-end.

### End-to-end test

```bash
curl -X POST https://workout.up.railway.app/trigger \
     -H "Authorization: Bearer ${TRIGGER_SECRET}"
```

Expected within ~10 seconds:
1. Telegram DM starts the check-in conversation.
2. Tap through each exercise → **Submit**.
3. "Generating next week's plan…" message in Telegram.
4. Email from `RESEND_FROM` with `plan-<week>.pdf` attached.
5. `config/schedule.json` is rewritten with the LLM's adjusted plan (on the Railway container).

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

### Schedule config

`config/schedule.json` is the source of truth between weeks. Edit it manually whenever you want to restructure (add a session, drop an exercise). The LLM rewrites it on every Submit to bump loads / reps based on your check-in.

Rules:
- `load_kg: null` = bodyweight or load irrelevant
- `note` is pre-populated context the LLM can read
- Add / remove sessions and exercises freely — the bot reads it at runtime

---

## LLM design (System B)

`core/llm_client.py` calls **`openai/gpt-oss-20b`** (OpenAI's open-weight 21B-param model) via any OpenAI-compatible endpoint. The current deployment uses **Groq** as the sole provider — fast (~1000 tok/s), cheap ($0.10/$0.50 per M tokens), and reliable enough that a fallback isn't needed for once-a-week traffic.

The code still supports a primary/fallback split (set `OSS_BASE_URL` + `OSS_API_KEY` to add a primary in front of Groq); the fallback kicks in on any `OpenAIError`, `json.JSONDecodeError`, or `ValueError` from the primary, with a default 60s timeout. Useful if you later self-host on Ollama / vLLM and want Groq as the safety net.

**Model ID on Groq:** `openai/gpt-oss-20b` (verified against [Groq docs](https://console.groq.com/docs/model/openai/gpt-oss-20b), 2026-06-03). Same ID works on most other hosts.

**Failure surface:** any `openai.OpenAIError`, `json.JSONDecodeError`, or `ValueError` from the primary trips the fallback. If `GROQ_API_KEY` isn't set, the call raises `RuntimeError` and the bot tells you "Plan generation failed".

**Upgrade path:** Groq supports strict `json_schema` mode (`response_format={"type": "json_schema", "json_schema": {...}}`) on this model, which is more reliable than the current `json_object`. Worth migrating if you start seeing malformed JSON in production. See [Groq Structured Outputs](https://console.groq.com/docs/structured-outputs) — note that strict mode is incompatible with streaming and tool use, requires `additionalProperties: false`, and all keys in `required`.

---

## System A (retired)

System A — the original Sunday-email tracker — was retired on 2026-06-03. The cloud routine `trig_01XUTpwZgjKkJw6VDq4HpZSh` is permanently disabled (its Bridge environment was lost) and renamed `Weekly Gym Progress Update (RETIRED 2026-06-03)`. Source code, the final `progress_log.json` snapshot, and the original routine prompt are preserved in `legacy_email/` for reference — see `legacy_email/README.md` for the rationale and `CLAUDE.md` for the original algorithm + research foundation.

Scripts in `legacy_email/` still run locally (paths were rewritten to be relative to the folder) — `python3 legacy_email/weekly_gym_update.py status`, etc. — but there's no automation behind them anymore.

---

## Deployment checklist (System B, picking up where we left off)

1. ☐ Add `OSS_BASE_URL` / `OSS_API_KEY` / `GROQ_API_KEY` / `RESEND_API_KEY` / `RESEND_FROM` / `YOUR_EMAIL` / `TRIGGER_SECRET` to `.env`
2. ☐ (Optional) Local PDF smoke-test: `brew install pango cairo gdk-pixbuf libffi && python3 -m core.pdf /tmp/plan.pdf`
3. ☐ Decide: migrate the real Upper/Lower routine from `progress_log.json` into `config/schedule.json`, or let the LLM rewrite it from the seeded Push/Pull/Legs example on first check-in
4. ☐ Push to GitHub
5. ☐ Deploy to Railway, set env vars
6. ☐ Register Telegram webhook against the Railway URL
7. ☐ Add GitHub Actions secrets (`BOT_TRIGGER_URL`, `TRIGGER_SECRET`)
8. ☐ Fire `workflow_dispatch` manually and verify end-to-end

(System A is already retired, so there's no coexistence conflict to worry about.)
