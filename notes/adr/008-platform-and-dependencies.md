# ADR-008: Stay on Vercel; accept single-provider risk until it bites

Date: 2026-07-07 · Status: accepted

## Context

The stack runs on Vercel Hobby with three external SaaS dependencies (Groq,
PDFShift, Resend), each single-provider with no fallback. Legacy deploy
configs (`Dockerfile`, `Procfile`, `railway.json`) linger from the abandoned
Railway attempt and are documented as unused.

## Decision

1. **Stay on Vercel.** ADR-002 removed the last writable-disk need; nothing
   else requires long-running processes. Delete `Dockerfile`, `Procfile`,
   `railway.json` — stale deploy configs are a trap.
2. **No LLM/PDF/email fallback providers.** Failure mode is acceptable by
   design: the bot reports the error in-chat, the user retries later, and
   ADR-005 makes delayed check-ins harmless.

## Revisit trigger

The moment Groq (or PDFShift/Resend) actually costs a Sunday check-in,
reopen this ADR and evaluate a fallback (e.g. OpenRouter for the planner).
Until then, a second provider is an env-var matrix and a prompt-compat
surface paid weekly for a hypothetical.
