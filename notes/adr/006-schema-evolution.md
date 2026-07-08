# ADR-006: Idempotent DDL in code, additive-only — never destroy progress

Date: 2026-07-07 · Status: accepted

## Context

Schema lives in `bot/state.py:init_db()` as `CREATE TABLE IF NOT EXISTS` +
idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, run on every cold
start. The discipline is manual and burned once (2026-06-11: an ALTER was
skipped and INSERTs failed silently for weeks). Past remediation advice
included "DROP TABLE checkin_state and redeploy" — acceptable for ephemeral
state, never for history.

## Decision

Keep the in-code idempotent-DDL pattern; no migration tool. Codified rules:

1. Every schema change ships, in the same commit: the `CREATE TABLE` update,
   the idempotent `ALTER` for existing deployments, and the ADR-004 boot
   assertion list update.
2. **Additive-only against data-bearing tables.** `checkin_history` and the
   ADR-002 `schedule` table hold the user's training progress — never DROP,
   TRUNCATE, or destructively retype them in a migration. Column renames =
   add new + backfill + leave old in place until verified.
3. `checkin_state` is ephemeral (deleted on Confirm) — DROP/recreate remains
   an acceptable last resort there, and only there.

## Alternatives rejected

- **Alembic/dbmate**: versioned and reviewable, but needs a migration-runner
  step Vercel's pipeline doesn't have; would end up bolted onto cold start
  anyway. Revisit at Stage 1–2 when schema churn and multiple environments
  appear.
