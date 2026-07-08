# ADR-007: Pure-logic pytest suite + GitHub Actions CI; no mocked infra

Date: 2026-07-07 · Status: accepted

## Context

Verification was three manual smoke scripts (live Groq/Resend calls), a
manual `py_compile` checklist, and no CI — while every push to `main`
auto-deploys to production via Vercel.

## Decision

- **pytest suite for deterministic logic only**: newsletter recap math
  (`core/newsletter.py`), HMAC signing (`core/signing.py`),
  `_format_diff`/`_format_schedule`, fact picker (`core/facts.py`), Pydantic
  `WeeklyPlan` validation against fixture JSONs.
- **GitHub Actions on every push/PR**: `py_compile` all `.py` files +
  `pytest`. No network, no secrets in CI.
- Smoke scripts (`scripts/test_plan.py`, `test_email.py`,
  `test_newsletter.py`) remain the manual pre-push step for LLM-prompt and
  email changes, per the existing CLAUDE.md rule.

## Alternatives rejected

- **Mocked Telegram/PTB/DB handler-flow tests**: brittle, and the risky
  seams are external services that mocks wouldn't exercise honestly.
  Runtime failures there are covered by ADR-004 alerting instead.
- **Status quo**: red X should arrive before Vercel ships a broken `main`,
  not after.
