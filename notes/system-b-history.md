# System B — Session history & architecture decisions

Archived from `CLAUDE.md` on 2026-06-08 to keep the project file lean.

## Session history

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
  1. **WeasyPrint incompatible** — replaced `core/pdf.py` with PDFShift API.
  2. **SQLite ephemeral on serverless** — replaced `bot/state.py` with Neon Postgres via `psycopg` v3.
- `main.py` refactored for serverless: removed FastAPI `lifespan=`; replaced with `async with ptb_app:` per-invocation (PTB's official serverless pattern). PTB object renamed from `application` → `ptb_app` to avoid Vercel ASGI entrypoint collision.
- `vercel.json` created: cron `0 8 * * 0` → GET `/trigger`.
- Vercel project `gym-research` created (Hobby, `MamiMrl/gym-research`, FastAPI preset). All secrets set via dashboard. Neon integration `neon-cyan-nest` connected.
- First deploy failed: entrypoint collision (`main:application` was PTB object, not ASGI). Fixed by renaming to `ptb_app` (commit `b1b3ac0`).

## Deployment bugs (2026-06-04)

1. **Vercel ASGI entrypoint collision** (commit `b1b3ac0`): Vercel's Python runtime scans `main.py` for a variable named `app` or `application` to use as the ASGI entrypoint. The PTB `Application` instance was named `application`, so Vercel picked it up instead of the FastAPI `app` and crashed with `Could not determine the application interface`. Fix: rename PTB object to `ptb_app` throughout. **Rule: never name anything `app` or `application` in `main.py` unless it's the FastAPI instance.**

2. **Telegram chat IDs require BIGINT** (commit `b9299ac`): `checkin_state.chat_id` was defined as `INTEGER` (32-bit Postgres, max ~2.1B). Telegram chat IDs are 64-bit and overflow it, causing `psycopg.errors.NumericValueOutOfRange` on the first INSERT. Fix: `INTEGER` → `BIGINT`. **Rule: always use `BIGINT` for any column storing Telegram user, chat, or message IDs.**

3. **psycopg v3 single-statement execute + connection leak** (commit `4c94a30`):
   - `conn.execute(SCHEMA)` where SCHEMA contained two `CREATE TABLE` statements — psycopg v3's `execute()` only runs **one** statement per call. The second table (`checkin_history`) was silently never created. Fix: split into two separate `conn.execute()` calls inside the same `with` block.
   - `_conn()` returned a bare `Connection` object; `with _conn() as conn:` managed the transaction (commit/rollback) but never closed the connection, leaking it to PgBouncer. Fix: `_conn()` is now a `@contextmanager` wrapping `psycopg.connect()` as the outer context manager, which closes the connection on exit.
   **Rule: in psycopg v3, one `execute()` = one statement. For schema setup, call `execute()` once per table.**

## 2026-06-04 (afternoon) — First live run, LLM failure

The full conversation flow worked end-to-end through Telegram, then crashed at the final step in `core/llm_client.py:59`:

> `Plan generation failed: Expecting value: line 1 column 1 (char 0)`

Root cause: `json.loads("")` — `resp.choices[0].message.content` came back empty.

Known failure mode of `gpt-oss-20b` (and `gpt-oss-120b`):
- [vLLM #30498](https://github.com/vllm-project/vllm/issues/30498)
- [HF gpt-oss-120b discussion #67](https://huggingface.co/openai/gpt-oss-120b/discussions/67)
- [Groq community #516](https://community.groq.com/t/gpt-oss-browser-response-empty-assistant-content/516)
- [Groq community #687](https://community.groq.com/t/structured-outputs-ignored-by-openai-gpt-oss-120b/687)

**Cause:** `gpt-oss-*` are *reasoning* models. They spend output tokens on internal reasoning *before* producing user-visible `content`. With `max_tokens=2048` and a long prompt, reasoning can consume the entire budget and `content` comes back empty. Architecture, not bug.

## 2026-06-04 (evening) — Path B+C hybrid landed (commit `b8c8a05`)

User chose a hybrid of Paths B and C, plus a Strava add-on:
- **Model swap** (Path B): `openai/gpt-oss-20b` → `llama-3.3-70b-versatile` with strict `response_format={"type":"json_schema",...}` and Pydantic `WeeklyPlan` validation.
- **Voice memo** (Path C): button-tap state machine deleted; replaced with a single `MessageHandler(filters.VOICE | filters.AUDIO)`. New `core/transcribe.py` wraps Groq `whisper-large-v3-turbo`. Rationale: each button tap had a 2–3 s Telegram round-trip — 12 taps × 3 s was unacceptable.
- **Rules in the prompt, not in code**: scientific progression rules (barbell ±2.5 kg, dumbbell ±1 kg, cable/machine ±2.5 kg, bw_weighted ±1.25 kg, bw_only never changes; deload triggers on 6 progression weeks / fatigue keywords / Strava CNS load) are embedded in `SYSTEM_PROMPT`. The LLM is both parser and executor. Trade-off: less deterministic than pure rules, but eliminates ~150 LOC.
- **Strava**: `core/strava.py` does OAuth-refresh → fetch last 7 days → UPSERT into `strava_activities` → summary digest into the LLM prompt and the confirmation card. `scripts/strava_oauth.py` is a one-time local CLI to mint the refresh token.
- **Schema rewrite** (breaking): `checkin_state` dropped `results`/`session_idx`/`exercise_idx`/`awaiting_note`; added `voice_file_id`/`transcript`/`proposed_changes`/`strava_summary`. `strava_activities` table added. `CREATE TABLE IF NOT EXISTS` won't migrate the existing table, so prod table must be dropped manually in Neon before first deploy.

## Architecture paths originally on the table

### Path A — Remove the LLM entirely (rule-based engine)
Port System A's rule-based weight adjuster. Status buttons carry the signal; LLM does arithmetic. Notes get stored and displayed rather than interpreted.
- Pros: deterministic, free, deletes ~150 LOC + 3 env vars.
- Cons: notes read by human only. Requires `weight_type` per exercise.

### Path B — Switch model + strict JSON schema
Stay on Groq, move from `openai/gpt-oss-20b` to `llama-3.3-70b-versatile` (not a reasoning model — no token-budget footgun). Strict `response_format={"type": "json_schema", ...}` + Pydantic.
- Pros: production-proven in similar bots. Same env vars; ~$0.20/M tokens; ~275 tok/s.
- Cons: still subject to API outages and prompt drift.

### Path C — Voice memo check-in (LLM as parser, rules as executor)
Replace per-exercise button taps with a single voice memo. Whisper → Llama → structured JSON → rule engine.
- Pros: large UX win. LLM has non-replaceable role.
- Cons: largest code change.

## Research references (2026-06-04)

- **Real-world fitness/coaching bots — all use Llama 3.x, none use gpt-oss:**
  - [ai-runner-coach](https://github.com/oleksandr-g-rock/ai-runner-coach) — Llama 3.3 via OpenRouter, Telegram + Strava
  - [cycling-coach](https://github.com/yerzhansa/cycling-coach) — BYO OpenAI-compatible key, Llama default
  - [Daily-20-Minute-Workout-Planner-Telegram-n8n](https://github.com/Ruzyuki/Daily-20-Minute-Workout-Planner-Telegram-n8n) — Llama via n8n
  - [voice-transcribe-summarize-telegram-bot](https://github.com/aviaryan/voice-transcribe-summarize-telegram-bot) — Llama 3 70B + Whisper on Groq

- **Best open-weight JSON model by benchmark** is Qwen 2.5 32B/72B (~94% structured-extraction accuracy vs Llama 3.3 ~87% per [Humai benchmark](https://www.humai.blog/qwen-2-5-vs-llama-3-3-best-open-source-llms-for-2026/)), but not hosted on Groq. Would require a provider switch. Not worth it for a 1-call-per-week job.

- **Strava reconsidered** — original 2026-06-04 conclusion rejected Strava because it can't track sets/reps. User clarified: *not* a source of truth for strength work, but a passive ingestion layer for cardio + HR. Use cases: HR safety flagging; data accumulation for future visualizations.

## 2026-06-11 — Newsletter CTA returned 500 ("transcript column does not exist")

**Symptom:** Clicking the week-14 CTA in the email landed on a blank Vercel "Internal Server Error" page (HTTP 500, 21-byte `text/plain` body — the FUNCTION_INVOCATION_FAILED signature).

**Root cause:** Two compounding bugs.

1. The `transcript` column on `checkin_history` was added in commit `b8c8a05` (2026-06-04 voice-memo refactor) only inside `CREATE TABLE IF NOT EXISTS`. Against the pre-existing prod table, that statement is a no-op, so the column was never created in production.
2. As a result, every `end_checkin` INSERT since 2026-06-04 silently failed — `checkin_history` was empty for every week. The user-visible Sunday flow (newsletter + PDF) had already succeeded by that point, so the failure was invisible until the new newsletter CTA endpoint queried the table.

The CTA endpoint (`main.py:download_plan`) ran a SELECT listing the missing `transcript` column. Postgres raised `psycopg.errors.UndefinedColumn`, which escaped the handler's try/except (only the PDF-render path was wrapped) and surfaced as Vercel's generic 500.

**Fix (2026-06-11):**
- Manual one-liner in Neon SQL editor: `ALTER TABLE checkin_history ADD COLUMN IF NOT EXISTS transcript TEXT;`
- Idempotent ALTER added to `bot/state.py:init_db` next to the existing `used_fact_id` ALTER, so fresh deploys self-heal.
- Test rows from weeks 1–13 were deliberately not recovered (they were testing artifacts, not real history).

**Lesson — codified in CLAUDE.md don'ts:** `CREATE TABLE IF NOT EXISTS` does not migrate columns. For every new column, also ship an idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` in the same commit. The 2026-06-12 protective plan adds a boot-time schema-drift assertion (T4) to catch the next instance loudly instead of silently.
