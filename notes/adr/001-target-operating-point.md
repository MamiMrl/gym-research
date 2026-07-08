# ADR-001: Target operating point is "Stage 0, hardened"

Date: 2026-07-06 · Status: accepted

## Context

README sketches stages 0–3 (manual → self-serve → browser check-in → app). The
repo went idle for ~2 weeks (late June 2026) and the maintainer trained
unstructured — the system failed its core purpose not by crashing but by
being abandonable.

## Decision

Production-ready means: the single-tenant weekly loop (Sunday trigger → voice
memo → plan → newsletter) works without the maintainer touching the codebase,
for months. No multi-tenant features. Data-model choices should not *block* a
future `users` table, but nothing is built for it.

## Consequences

- Hardening work is judged by one metric: does it keep the weekly loop alive
  unattended?
- Multi-tenant tickets (signup, per-user schedules) are out of scope until a
  concrete second user asks weekly (README Stage-1 trigger).
