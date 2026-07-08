# ADRs — index & glossary

Decision records from the 2026-07-06/07 production-readiness grilling.
Read top-down; later ADRs assume earlier ones.

## Index

| # | Decision |
|---|---|
| [001](001-target-operating-point.md) | Production-ready = Stage 0 hardened: the single-tenant weekly loop survives months of maintainer neglect |
| [002](002-schedule-source-of-truth.md) | Live plan moves from `config/schedule.json` to a one-row Postgres `schedule` table; file demoted to seed |
| [003](003-bot-surface-auth.md) | Webhook `secret_token` + silent chat-id allowlist |
| [004](004-failure-visibility.md) | Dead-man's switch (healthchecks.io) + bot-as-alert-channel + boot-time schema assertion |
| [005](005-week-semantics.md) | Week = check-in counter; gaps pause the program; no nudges; prompt handles returning-after-gap |
| [006](006-schema-evolution.md) | Idempotent DDL in code, additive-only against data-bearing tables |
| [007](007-testing-and-ci.md) | Pure-logic pytest + GitHub Actions CI; no mocked infra |
| [008](008-platform-and-dependencies.md) | Stay on Vercel; single-provider risk accepted until a Sunday actually fails |

## Glossary

- **Weekly loop** — the product: Sunday trigger → planned-schedule DM → voice
  memo → transcript → proposed plan → Confirm → PDF + newsletter + archive.
- **Live plan** — the schedule the next check-in starts from. Owned by the
  Postgres `schedule` table (ADR-002). Exactly one exists.
- **Seed** — `config/schedule.json`: bootstrap/template for the live plan,
  pushed manually via script on restructures. Not runtime state.
- **Check-in** — one completed pass through the loop, ending in Confirm.
  Ephemeral working state lives in `checkin_state` (deleted on Confirm).
- **Week N** — the Nth *completed* check-in (counter, not calendar — ADR-005).
- **Archive** — `checkin_history`: one row per completed check-in
  (snapshot, transcript, used_fact_id). Append-only; never destroyed
  (ADR-006).
- **Gap** — Sundays with no completed check-in. Invisible in history; the
  live plan freezes; progression and the 6-week deload counter pause.
- **Data-bearing tables** — `checkin_history`, `schedule`: additive-only
  migrations. `checkin_state` is ephemeral and exempt.
- **Dead-man's switch** — external ping expected from `/trigger` each Sunday;
  its *absence* is the alert (ADR-004).
