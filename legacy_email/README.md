# System A — Retired (2026-06-03)

This is the **legacy email-based gym tracker**, retired in favour of [System B](../README.md) (the Telegram bot).

## Status

- **Cloud routine `trig_01XUTpwZgjKkJw6VDq4HpZSh`** is permanently disabled (`ended_reason: auto_disabled_env_not_found` — the Mac Bridge environment it ran on no longer exists). It will not fire again.
- **Last successful run:** week of 2026-05-29 (see `progress_log.json` `week_history`).
- **Source code preserved** in this directory for historical reference. All hardcoded `/Users/neu/Downloads/gym-research/` paths were rewritten to be relative to this folder, so the scripts will still run locally if invoked from here (e.g. `python3 legacy_email/weekly_gym_update.py status`).

## What it did

Weekly email loop: Gmail reply (`MON: + / WED: stay / ...`) → script parses → updates weights in `progress_log.json` → generates BVB-themed HTML/PDF → emails next week's plan. Full algorithm, deload logic, and research foundation are documented in `../CLAUDE.md` under "System A — Full design docs".

## Files

```
legacy_email/
├── README.md                    This file
├── weekly_gym_update.py         Main script (CLI: init / status / process)
├── generate_workout_html.py     BVB-themed HTML renderer
├── generate_workout_pdf.py      PDF renderer
├── progress_log.json            Training database (last updated 2026-05-29)
├── routine_agent.md             Original cloud-routine agent prompt
└── outputs/                     Generated HTMLs and PDFs (gitignored)
```

## To resurrect (don't, but if you must)

1. Create a new Anthropic environment (Bridge to a machine, or a cloud env with this repo checked out).
2. Update routine `trig_01XUTpwZgjKkJw6VDq4HpZSh`'s `environment_id` and rewrite the prompt's "Work directory" line to `legacy_email/`.
3. Re-enable it.

Or just use System B. That's what it's for.
