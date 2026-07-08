# ADR-003: Webhook secret_token + chat-id allowlist

Date: 2026-07-07 · Status: accepted

## Context

`POST /webhook` accepted any JSON payload from anyone (no Telegram
`secret_token` verification), and handlers never checked the sender — any
Telegram user who found the bot could run check-ins, burn Groq/PDFShift quota,
and Confirm → email the maintainer a garbage plan while overwriting the live
schedule.

## Decision

Two layers, both cheap:

1. **Transport auth**: re-register the webhook with a `secret_token`
   (new env var `TELEGRAM_WEBHOOK_SECRET`, generated separately from
   `CRON_SECRET` — different rotation lifecycles). `main.py:webhook` verifies
   the `X-Telegram-Bot-Api-Secret-Token` header, 403 on mismatch.
2. **Identity gate**: at the top of update processing, if
   `chat_id != TELEGRAM_CHAT_ID`, drop the update silently — no reply, so
   strangers get no confirmation the bot is alive.

## Consequences

- One-time re-registration: `setWebhook` call with `secret_token` param.
- New env var in Vercel + `.env.example` + secrets runbook.
- No rate limiting or user tables — out of scope for Stage 0 (ADR-001).
