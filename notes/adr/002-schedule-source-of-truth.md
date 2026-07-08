# ADR-002: Live plan moves to a one-row Postgres `schedule` table

Date: 2026-07-07 · Status: accepted

## Context

`core/schedule.py:save_schedule()` rewrites `config/schedule.json` inside the
deployed bundle on every Confirm. Vercel's filesystem is ephemeral: the write
is lost on the next cold start/redeploy, silently reverting the plan to the
git-committed version (last committed 2026-06-03). The real progression only
survived in `checkin_history.schedule_snapshot`. Two sources of truth, one
lying — a direct violation of the existing "SQLite is ephemeral on serverless;
all persistent state → Neon Postgres" rule, with the file as the last holdout.

## Decision

- New one-row table `schedule (id smallint primary key default 1, plan jsonb,
  updated_at timestamptz)` in Neon.
- `load_schedule()` reads the row; if missing, seeds it from
  `config/schedule.json` (bootstrap path).
- `save_schedule()` UPSERTs the row.
- `config/schedule.json` is demoted to seed/template. Manual restructures
  (add/drop session or exercise) happen by editing the file and pushing it via
  a small `scripts/push_schedule.py`.

## Alternatives rejected

- **Live plan = latest `checkin_history.schedule_snapshot`**: conflates
  archive with live state; manual restructures would need fake history rows.
- **Commit the file back to git via GitHub API on Confirm**: adds an API
  dependency, one deploy per week, race conditions.

## Consequences

- CLAUDE.md "live source of truth" line must be updated once implemented.
- `bot/state.py:init_db` gains the new table (one `execute()` per statement,
  idempotent ALTERs rule applies).
- Archive (`checkin_history`) and live state stay distinct.
