# IMPLEMENTATION — Light Weight weekly newsletter

> **This file is scratch. Delete it after the newsletter ships.** Permanent docs live in `CLAUDE.md` and `README.md`.

## Locked decisions

| Q | Decision |
|---|---|
| Visual system | **Hi-fi** — `DESIGN-Weekly-Science-Newsletter/newsletter-hifi.jsx` (rounded cards, Bebas Neue, BVB warm). |
| Brand wordmark | **LIGHT WEIGHT.** — yellow period accent. Keep across all surfaces (email + PDF). |
| Science-fact source | **Curated `data/facts.json`** — hand-seeded from `docs/golden-encyklopedia-building-muscle.md` + `docs/Gym-planning.md`. ~25 entries. Picker rotates + tag-matches transcript. No LLM in the fact path. |
| Hero photo | **Curated copyright-free folder** — `assets/hero/` with ~15–20 B&W gym shots from Unsplash/Pexels. Deterministic rotation by issue number. Attribution in `assets/hero/README.md`. |
| CTA download | **Functional signed URL** — `GET /plan/{week_number}.pdf?t=<hmac>` re-renders from `checkin_history.schedule_snapshot`. PDF stays attached for offline. |

## Scope at a glance

- **Goal:** the Sunday email goes from "one line + PDF attached" → a full newsletter that looks like the design canvas, *without* changing the conversational flow or the printed PDF template.
- **What stays the same:** Telegram check-in flow, `config/schedule.json`, `templates/plan.html` (the printed PDF), Resend/PDFShift/Groq plumbing.
- **What's new:** newsletter template, fact pool, hero pool, signed-download endpoint, per-exercise `status` field on the LLM output, data-layer that turns raw plan + transcript into newsletter context.
- **Budget:** ~400–500 LOC; ~1 day's focused work.

---

## File inventory

### New
- `templates/newsletter.html` — Jinja2 port of `newsletter-hifi.jsx`. Email-safe (inline CSS, table grids).
- `core/newsletter.py` — `build_context(this_week, next_week, transcript, week_number) -> dict`.
- `core/facts.py` — `pick_fact(transcript: str, deload: bool, used_ids: list[str]) -> dict`.
- `data/facts.json` — curated science-fact pool (~25 entries).
- `assets/hero/` — `01.jpg` … `20.jpg` + `README.md` (attribution).
- `scripts/test_newsletter.py` — local renderer that opens `/tmp/newsletter.html` in browser.

### Modified
- `core/email.py` — accepts rich context, renders Jinja2 body, sets subject + preheader, keeps PDF attachment.
- `core/prompt.py` — extend `PLAN_JSON_SCHEMA` with optional `status` per exercise; update `SYSTEM_PROMPT` to emit it.
- `bot/handlers.py:_on_confirm` — load this-week schedule *before* `save_schedule()`, thread it into the email call.
- `bot/state.py` — `checkin_history` gains `used_fact_id TEXT NULL`; `last_used_fact_ids(limit=8) -> list[str]` helper.
- `main.py` — `GET /plan/{week_number}.pdf?t=<hmac>` endpoint with HMAC validation.
- `CLAUDE.md`, `README.md` — newsletter architecture section.

### Untouched
- `templates/plan.html` (printed PDF), `core/pdf.py`, `core/llm_client.py`, `core/transcribe.py`, `core/schedule.py`, `config/schedule.json`.

---

## Data shapes

### Newsletter context (`build_context` output)

```python
{
    "issue_number": 14,
    "date_str": "SUN · JUN 14",
    "week_label": "Week 14 — Upper/Lower",
    "deload": False,
    "deload_reason": None,
    "accent": "#FDE100",
    "name": "LIGHT WEIGHT",

    "show_hero": True,
    "hero_image_url": "https://<vercel>.app/static/hero/07.jpg",  # or cid:hero
    "hero_alt": "Athlete mid-squat, black-and-white",

    "fact": {
        "headline_prefix": "Hitting a muscle ",
        "highlight": "twice a week",
        "headline_suffix": " builds ~15% more of it than once — at the same weekly volume.",
        "citation": "Schoenfeld, Ogborn & Krieger (2016) · meta-analysis, 25 studies",
        "why_it_matters": "Don't cram chest into one brutal Monday. Split the same sets across two days and you grow faster for free — which is exactly how your plan below is built.",
    },

    "recap": {
        "sessions_done": 4,
        "sessions_planned": 4,
        "kg_added": 7.5,
        "skipped_count": 0,
        "highlight_line": "Biggest jump: Squat → 90 kg.",  # or deload-flavored copy
    },

    "plan_rows": [
        {"day": "MON", "session": "Upper · Push + Pull",      "top_set_name": "Bench Press",   "top_set_load": "70 kg", "deload_note": None},
        {"day": "WED", "session": "Lower · All-in",           "top_set_name": "Barbell Squat", "top_set_load": "90 kg", "deload_note": None},
        {"day": "FRI", "session": "Cali · Shoulders + Chest", "top_set_name": "Machine Press", "top_set_load": "55 kg", "deload_note": None},
        {"day": "SAT", "session": "Deadlift · Back + Quads",  "top_set_name": "Deadlift",      "top_set_load": "100 kg","deload_note": None},
    ],

    "cta": {
        "href": "https://<vercel>.app/plan/14.pdf?t=<hmac>",
        "label_main": "DOWNLOAD THIS WEEK'S PLAN",
        "label_sub": "PDF · A4 · print & glue into your notebook",
    },

    "footer": {
        "tagline": "Reply with a voice memo telling me how each session went — next Sunday's plan adjusts your loads automatically.",
    },
}
```

### `data/facts.json` entry

```json
{
  "id": "freq-2x-schoenfeld-2016",
  "tags": ["frequency", "hypertrophy", "volume"],
  "headline_prefix": "Hitting a muscle ",
  "highlight": "twice a week",
  "headline_suffix": " builds ~15% more of it than once — at the same weekly volume.",
  "citation": "Schoenfeld, Ogborn & Krieger (2016) · meta-analysis, 25 studies",
  "why_it_matters": "Don't cram chest into one brutal Monday. Split the same sets across two days and you grow faster for free — which is exactly how your plan below is built.",
  "deload_safe": true
}
```

`deload_safe = false` means "don't pick this one during a deload week" (e.g. anything pushing harder/heavier).

### `PLAN_JSON_SCHEMA` extension

Add to each exercise:

```json
"status": {"type": "string", "enum": ["as_planned", "too_easy", "struggled", "skipped"]}
```

System-prompt addition: *"For each exercise, also emit a `status` field reflecting what the user reported in the transcript: `as_planned` (no mention or 'as planned'), `too_easy` (user said too light / easy / nothing left in the tank), `struggled` (form broke / RIR 0 / had to rack early), or `skipped` (user said they skipped or missed)."*

### `checkin_history` schema bump

```sql
ALTER TABLE checkin_history ADD COLUMN IF NOT EXISTS used_fact_id TEXT NULL;
```

Backfill not needed (`NULL` = unknown).

---

## Picker algorithms (v1, deterministic)

### Fact picker

```python
def pick_fact(transcript: str, deload: bool, used_ids: list[str]) -> dict:
    pool = load_facts()
    if deload:
        pool = [f for f in pool if f.get("deload_safe", True)]

    # Score by tag-keyword presence in transcript (case-insensitive substring).
    def score(fact):
        t = transcript.lower()
        return sum(1 for tag in fact["tags"] if tag in t)

    scored = sorted(pool, key=lambda f: (-score(f), used_ids.index(f["id"]) if f["id"] in used_ids else -1))
    # Prefer unused, then highest-score. Fallback to first if all used.
    unused = [f for f in scored if f["id"] not in used_ids]
    return (unused or scored)[0]
```

### Hero photo picker

```python
def pick_hero(issue_number: int) -> str:
    pool = sorted(Path("assets/hero").glob("*.jpg"))
    return pool[issue_number % len(pool)].name
```

Static deterministic rotation. No need for "used" tracking — wraps cleanly.

### Top-set picker (per day row)

```python
def top_set(exercises: list[dict]) -> tuple[str, str]:
    weighted = [e for e in exercises if e.get("load_kg") is not None]
    if not weighted:
        e = exercises[0]
        return e["name"], "BW"
    e = max(weighted, key=lambda x: x["load_kg"])
    return e["name"], f"{int(e['load_kg']) if e['load_kg'] == int(e['load_kg']) else e['load_kg']} kg"
```

### Recap stats

```python
def recap(this_week, next_week, status_map):
    sessions_planned = len(this_week["sessions"])
    sessions_done    = sessions_planned - count_status(status_map, "skipped", scope="session")
    skipped_count    = count_status(status_map, "skipped", scope="exercise")
    kg_added         = sum_positive_deltas(this_week, next_week)
    biggest_jump     = argmax_delta(this_week, next_week)
    return {...}
```

---

## Signed PDF endpoint

`GET /plan/{week_number}.pdf?t=<hex>` — `main.py` adds:

```python
import hmac, hashlib, os

def _sign(week_number: int) -> str:
    key = os.environ["CRON_SECRET"].encode()
    return hmac.new(key, str(week_number).encode(), hashlib.sha256).hexdigest()[:16]

@app.get("/plan/{week_number}.pdf")
async def get_plan(week_number: int, t: str):
    if not hmac.compare_digest(t, _sign(week_number)):
        raise HTTPException(status_code=403)
    snapshot = st.get_history(week_number)  # returns schedule dict
    if snapshot is None:
        raise HTTPException(status_code=404)
    pdf_path = pdf.render_pdf(snapshot, output_path=f"/tmp/plan-{week_number}.pdf")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"plan-week-{week_number}.pdf")
```

Token is short (16 hex chars) but unguessable because `CRON_SECRET` is already 32+ hex chars of entropy. No expiry — older weeks stay readable, which is a feature for the archive.

Newsletter context builder computes `cta.href` via the same `_sign` helper imported from `main`.

---

## Hero photo curation checklist

1. Hit Unsplash (https://unsplash.com/s/photos/barbell-black-and-white) and Pexels.
2. Pick 15–20 shots that share a vibe: **B&W or low-saturation, athletic, low-text, landscape-oriented, ~1200px wide**. Avoid logos/faces unless explicitly model-released.
3. Save as `assets/hero/01.jpg` … `20.jpg` (zero-padded so glob sort is stable).
4. Add each to `assets/hero/README.md` with: filename · photographer · source URL · license.
5. Files served via FastAPI `StaticFiles` mount at `/static/hero/`. Email references them by absolute URL (`https://<vercel>.app/static/hero/07.jpg`) so they render in inbox previews.

---

## Email-safe HTML notes (Jinja2 port gotchas)

- **CSS:** everything inline. No `<style>` block — Gmail strips it from the body, Outlook ignores half of it.
- **Layout:** flex/grid renders in Apple Mail and Gmail web, but Outlook desktop falls back to block. Use `<table role="presentation" cellpadding="0" cellspacing="0">` for the 3-up recap tiles and the 4-row plan list.
- **Fonts:** keep the Google Fonts `<link>` in `<head>` — Apple Mail and ~60% of clients honor it. Font stacks already fall back gracefully (`'Bebas Neue', 'Arial Narrow', Impact, sans-serif`).
- **Background colors:** set on the `<td>` not the `<div>` for Outlook.
- **Hero image:** absolute `https://` URL, `max-width: 100%`, explicit `width` + `height` attributes (Outlook), `display: block`.
- **CTA button:** wrap the colored block in `<a>` so the whole tile is clickable. Use `bgcolor` attribute as well as inline `background` for Outlook.
- **Preheader:** hidden span at top: `<div style="display:none;font-size:1px;color:#fff;line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;">{teaser}</div>`.
- **Plain-text fallback:** Resend supports `"text": "..."`. Build a minimal stripped version so spam filters don't downgrade us.

---

## Phased plan (mirrors task list)

1. **Data layer** — `core/newsletter.py` + status field on LLM. Validate with hand-built fixtures. Verify `build_context` output shape.
2. **Facts** — seed `data/facts.json` (~25), `core/facts.py`, schema bump for `used_fact_id`. Pick at least 3 deload-safe entries.
3. **Hero pool** — collect, attribute, commit. (Can run in parallel with 4.)
4. **Template** — port `newsletter-hifi.jsx` → `templates/newsletter.html`. Render with mock context, eyeball in browser.
5. **Signed endpoint** — `/plan/{n}.pdf` + helper. Tested by hitting `/plan/14.pdf?t=<sign(14)>` locally.
6. **Wire it up** — `core/email.py` renders + sends; `_on_confirm` threads everything. Local end-to-end with `scripts/test_newsletter.py`.
7. **Verify** — open in Apple Mail desktop + iOS Mail. One real `/trigger` cycle on staging if available; otherwise straight to prod.
8. **Finalize** — fold permanent docs into `CLAUDE.md`/`README.md`; delete this file.

---

## Open questions / risks

- **`status` field on the LLM:** prompt change is small but adds 4 enum values per exercise. Watch for the model omitting it on exercises the user didn't mention — default to `as_planned` if missing in `build_context`.
- **Fact pool freshness:** the curated list is static. If you ship it, run for ~25 weeks (one per fact), then you'll need to top it up. Set a calendar reminder.
- **Hero URL via static mount:** Vercel's serverless Python doesn't serve from disk by default for big folders — confirm `assets/hero/` is bundled into the deployment, or move to Vercel Blob if it isn't.
- **Print-card CTA target:** the printed PDF is the *same* file the email attaches. The signed-URL CTA is mostly for the archive use case (open past weeks from your phone). That's fine — just don't expect new analytics value.
- **Resend HTML size cap:** ~2MB per email. Hero photo could push us close — compress to <200 KB JPEGs (1200×620, quality 75).

---

*Created: 2026-06-10. Delete when CLAUDE.md is updated and the newsletter ships.*
