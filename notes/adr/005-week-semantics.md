# ADR-005: A week is a check-in counter, not a calendar week

Date: 2026-07-07 · Status: accepted

## Context

`week_number` only advances on Confirm. Skipped Sundays leave no trace in
`checkin_history`, and the plan freezes until the next completed check-in.
The maintainer's June–July 2026 gap (two unstructured weeks) surfaced the
question of whether missed weeks should be modeled.

## Decision

Keep and bless counter semantics:

- Week N = the Nth *completed* check-in. Gaps pause the program; the plan
  freezes; training resumes where it left off. No skipped-week rows, no
  catch-up machinery, no reminder nudges.
- One prompt addition: the system prompt must handle a returning-after-gap
  memo ("was away two weeks, did random stuff") — hold or slightly reduce
  loads rather than blindly applying progression, and don't count the gap
  toward the 6-week deload counter.

## Alternatives rejected

- **Calendar weeks with skipped rows**: more honest history, but needs a
  mid-week sweeper job (Vercel Hobby ≈ one cron) and adds no training value
  at Stage 0.
- **Monday reminder nudge**: the observed failure was "tool felt stale so I
  stopped" (fixed by ADR-002), not "forgot" — a nudge would be ignorable
  noise and costs the cron slot.
