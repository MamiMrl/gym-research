# ADR-004: Three-layer failure visibility

Date: 2026-07-07 · Status: accepted

## Context

The 2026-06-11 incident: `checkin_history` INSERTs silently failed for ~5
weeks behind a green-looking Sunday flow. Separately, nothing detects the
Sunday cron simply not firing (Vercel Hobby cron is ±59 min best-effort;
failed deploys or an expired webhook registration would also fail silently).

## Decision

1. **Dead-man's switch**: free healthchecks.io check; `/trigger` pings it on
   success. No ping by Sunday noon → push/email alert. Catches "cron never
   fired" and "trigger crashed" — the two modes the bot cannot self-report.
   New env var `HEALTHCHECK_PING_URL` (optional; skip ping when unset).
2. **Bot as alert channel**: handlers already DM exceptions to the Telegram
   chat; extend the same wrapping to `/trigger` internals so any failure in
   the weekly loop lands in the chat the maintainer already reads.
3. **Boot-time schema assertion**: `init_db` verifies expected
   tables/columns exist and raises loudly at deploy/cold-start if not
   (the "T4" protective plan sketched 2026-06-12, never landed). Kills the
   June-11 class: drift fails at deploy time, not weeks later.

## Alternatives rejected

- Sentry / Vercel log drains: overkill for a single-tenant weekly loop
  (ADR-001).
