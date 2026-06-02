# Workout tracker

Sunday Telegram check-in → Claude-generated plan → PDF emailed to you. Single user, minimal infra.

## Status (2026-06-02)

🟡 **Code complete, not yet deployed.** Picking up here tomorrow.

**Done** — steps 6–10 of the original plan are all in the repo:
- PDF renderer (`templates/plan.html`, `core/pdf.py`) — compiles; local render needs `brew install pango cairo gdk-pixbuf libffi`
- Email via Resend (`core/email.py`)
- FastAPI webhook + trigger server (`main.py`), bot conversation loop (`bot/`), Claude integration (`core/`)
- Dockerfile + `railway.json` for Railway deploy
- GitHub Actions cron (`.github/workflows/checkin.yml`)

**Left** — pure config and deploy work, no more code:
1. Add to `.env`: `ANTHROPIC_API_KEY`, `RESEND_API_KEY`, `RESEND_FROM`, `YOUR_EMAIL`, `TRIGGER_SECRET`
2. (Optional) `brew install pango cairo gdk-pixbuf libffi` and run `python3 -m core.pdf /tmp/plan.pdf` to smoke-test the PDF locally
3. Decide whether to migrate the real Upper/Lower routine from `progress_log.json` into `config/schedule.json` before first deploy (currently seeded with the plan's example Push/Pull/Legs)
4. Commit and push to GitHub
5. Deploy to Railway with the env vars from step 1
6. Register the Telegram webhook (`setWebhook`) against the Railway URL
7. Add `BOT_TRIGGER_URL` + `TRIGGER_SECRET` to GitHub Actions secrets
8. Fire the workflow manually (`workflow_dispatch`) and verify end-to-end

**Coexistence note:** the old email-based system (`weekly_gym_update.py` + cloud routine `trig_01XUTpwZgjKkJw6VDq4HpZSh`) is still live and will fire on Sunday. Disable it before deploying this one, or accept two emails for one week. See `CLAUDE.md` for the old system's full docs.

## Repo layout

```
.
├── main.py                  FastAPI app: /webhook + /trigger
├── bot/
│   ├── handlers.py          Telegram conversation flow
│   ├── keyboards.py         Inline keyboards
│   └── state.py             SQLite check-in + history
├── core/
│   ├── schedule.py          Load/save config/schedule.json
│   ├── prompt.py            System prompt + builder
│   ├── claude_client.py     Anthropic SDK call
│   ├── pdf.py               WeasyPrint render
│   └── email.py             Resend send
├── config/schedule.json     The weekly plan (Claude rewrites this on submit)
├── templates/plan.html      Jinja2 template for the PDF
├── Dockerfile               Includes Pango/Cairo for WeasyPrint
├── Procfile                 Fallback for Buildpack hosts
├── railway.json             Railway service config
└── .github/workflows/checkin.yml   Sunday cron
```

## Environment variables

Set these locally in `.env` and in Railway's service variables:

```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5     # optional override
RESEND_API_KEY=re_...
RESEND_FROM=workout@yourdomain.com   # must be a verified domain in Resend
YOUR_EMAIL=you@example.com
TRIGGER_SECRET=<random-string>
```

GitHub Actions also needs:

```
BOT_TRIGGER_URL=https://your-app.up.railway.app/trigger
TRIGGER_SECRET=<same as above>
```

## Local development

```bash
pip install -r requirements.txt

# WeasyPrint needs system libs on macOS:
brew install pango cairo gdk-pixbuf libffi

# Render a PDF from the current schedule:
python3 -m core.pdf /tmp/plan.pdf
open /tmp/plan.pdf

# Run the web app:
uvicorn main:app --reload --port 8000
```

To test the bot locally with Telegram, expose port 8000 via ngrok and set the webhook:

```bash
ngrok http 8000
curl -F "url=https://<ngrok-id>.ngrok.app/webhook" \
     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"
```

## Deploy to Railway

1. Push this repo to GitHub.
2. New Railway project → Deploy from GitHub → pick this repo. Railway will detect the Dockerfile.
3. Add all the env vars from above to the service.
4. After the first deploy, copy the public URL (e.g. `https://workout.up.railway.app`).
5. Register the Telegram webhook:
   ```bash
   curl -F "url=https://workout.up.railway.app/webhook" \
        "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"
   ```
6. In GitHub repo settings → Secrets and variables → Actions, add:
   - `BOT_TRIGGER_URL` = `https://workout.up.railway.app/trigger`
   - `TRIGGER_SECRET` = the same value you set on Railway

## End-to-end test

```bash
# Smoke-test the trigger endpoint manually (kicks off the check-in conversation in Telegram):
curl -X POST https://workout.up.railway.app/trigger \
     -H "Authorization: Bearer ${TRIGGER_SECRET}"
```

You should receive a Telegram message starting the weekly check-in. Tap through each exercise, hit **Submit**, and within ~10 seconds you should:

1. See "Generating next week's plan…" in Telegram
2. Receive an email from `RESEND_FROM` with `plan-<week>.pdf` attached
3. Find `config/schedule.json` rewritten with the new plan (on the Railway container)

GitHub Actions also exposes the workflow under the Actions tab — you can fire it manually via **Run workflow** to verify the cron path without waiting until Sunday.

## Conversation flow

```
/checkin (or Sunday cron via /trigger)
  → session header: "Monday — Push"
  → for each exercise: [As planned] [Too easy] [Struggled] [Skipped]
  → "Any note? (or Skip)"  ← optional free-text reply
  → next exercise, next session
  → [Submit] → Claude → PDF → Resend → confirmation in Telegram
```

State lives in `state.db` (SQLite, single file). One row per active check-in keyed by `chat_id`, deleted on submit. History is appended to `checkin_history` and never cleared — Claude can use it for context in future iterations.

## Schedule config

`config/schedule.json` is the source of truth between weeks. Edit it manually whenever you want to restructure (add a session, drop an exercise). Claude rewrites it on every Submit to bump loads / reps based on your check-in.

Rules:
- `load_kg: null` = bodyweight or load irrelevant
- `note` is pre-populated context Claude can read
- Add/remove sessions and exercises freely — the bot reads at runtime
