# Email delivery — operational notes

Extracted from `CLAUDE.md` on 2026-06-12 to keep the always-loaded file slim. Apple Mail + Resend deliverability lessons learned the hard way during single-tenant launch.

- **Resend requires a verified custom domain** to deliver reliably to iCloud (and other providers). `onboarding@resend.dev` is silently dropped by Apple Mail. Set `RESEND_FROM` to an address on a domain you've verified in Resend → Domains.
- Run `python3 scripts/test_email.py` locally to confirm delivery before deploying.
- **Apple Mail "Your network blocks remote content" is not your network** — it's Mail Privacy Protection, a per-recipient default since iOS 15 / macOS Monterey. Triggered by any `<img src="https://…">` in the body. Recipient clicks "Load remote content" once; subsequent issues from the same `RESEND_FROM` usually auto-load (especially once that address is in the recipient's Contacts). **Don't try to "fix" this for single-tenant** — accept the one-time click. If/when shipping to friends and the warning friction becomes the bottleneck, swap the hero `<img>` to an inline base64 data URI (~10 LOC in `core/email.py`, email size goes 17 KB → ~85 KB; PDF attachment already dominates the payload). The CTA URL stays remote — it's a click target, not auto-loaded, so the privacy filter doesn't apply.
- Add `gym@mami-gym-bot-update.xyz` to iCloud contacts to keep messages out of junk.
