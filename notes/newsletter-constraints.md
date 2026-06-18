# Newsletter constraints (do not break)

Extracted from `CLAUDE.md` on 2026-06-12 to keep the always-loaded file slim. These are the load-bearing design rules for the "Light Weight" weekly newsletter — change them only with eyes open.

- **Brand wordmark stays `LIGHT WEIGHT.`** with the yellow period accent. Alternates from the identity board (Overload / Tension / Volume) are explicit non-choices — see `DESIGN-Weekly-Science-Newsletter/identity-boards.jsx`.
- **Hi-fi is the chosen visual system** (rounded cards, Bebas Neue display). The elevated/stencil variant (`newsletter-elevated.jsx`) is documented but not used.
- **Facts come from `data/facts.json` only.** No LLM in the fact path — picker is deterministic tag-match against the transcript with repeat-avoidance via `checkin_history.used_fact_id`. When the pool ages out (~25 weeks), top it up by extending the JSON, not by switching to LLM generation.
- **Hero rotation is deterministic by `issue_number % len(pool)`.** Don't introduce randomness — the cycle is meant to be predictable for the maintainer.
- **CTA is HMAC-signed via `core/signing.py`.** Token derived from `CRON_SECRET`. Don't shorten below 16 hex chars; don't add expiry (archive use case needs old links to stay alive).
- **`APP_BASE_URL` must be set** for the hero `<img src>` and CTA `href` to resolve in production. Without it, both fall back gracefully but the email is missing pieces.
- **Per-exercise `status` field on the LLM is load-bearing** — the recap math (sessions-done, skipped-count) reads from it. The Pydantic model defaults to `as_planned` so legacy plans still validate, but new prompts should always request the field.
- **Email-safe template rules** (in `templates/newsletter.html`): all CSS inline, tables for layout, `bgcolor=` alongside `style:background` for Outlook, numeric width/height attrs on `<img>` + `<td>`, hidden preheader span first thing in `<body>`. Don't switch to flex/grid — Outlook desktop will fall back to block.
