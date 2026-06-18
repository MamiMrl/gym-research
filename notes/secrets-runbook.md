# Secrets — where each key lives

Extracted from `CLAUDE.md` on 2026-06-12 to keep the always-loaded file slim. Where each secret comes from, how it's used, and what to do when it's lost.

- **`RESEND_API_KEY`** — generate at `resend.com/api-keys`, scope to the verified domain (`mami-gym-bot-update.xyz`). Shown once on creation; if lost, rotate by generating a new one and revoking the old. Used at runtime in `core/email.py` and `scripts/test_*.py`.
- **`CRON_SECRET`** — generate locally with `openssl rand -hex 32`. Vercel injects it as `Authorization: Bearer …` on every `/trigger` invocation; also the HMAC key for signed PDF download URLs (`core/signing.py`). **In the Vercel dashboard, you can mark it Sensitive or not** — single-tenant trade-off: marking Sensitive hides the value after creation (more hygienic, but you can't read it back, so save to a password manager *immediately* or you'll need to rotate to recover). At stage 0/1 the practical risk delta is small; at stage 2+ (multi-tenant) treat Sensitive as required.
- **`GROQ_API_KEY`, `PDFSHIFT_API_KEY`, `TELEGRAM_BOT_TOKEN`** — issued by each provider's dashboard. Same "save on creation or rotate to recover" pattern.
- **`DATABASE_URL`** — injected automatically by the Vercel ↔ Neon integration. Don't set manually in production; pull locally with `vercel env pull .env` if you need to debug against the live DB.
