# Hero photos

Source photos for the weekly Light Weight newsletter. Each issue's hero is picked deterministically by `core.hero.pick_hero(issue_number)` — `issue_number % len(pool)` — so the cycle wraps with no "recently used" tracking.

## Spec

- **Aspect ratio:** 2.5:1 (1200 × 480 px). Renders into a 600 × 240 letterbox in the email at 2× retina density.
- **File size budget:** ≤ 150 KB each, ≤ 1.5 MB total for the bundle. The full pool ships inside the Vercel deployment.
- **Format:** progressive JPEG, sRGB, quality ~80. No EXIF.
- **Naming:** zero-padded ordinal — `01.jpg`, `02.jpg`, … — so `glob("*.jpg")` sorts the same as the human eye.

## Source + licensing

All 12 current photos are from [Unsplash](https://unsplash.com/). The [Unsplash License](https://unsplash.com/license) allows use for any purpose, free of charge, without attribution required — but a link back is appreciated. Originals were downloaded into `~/Downloads/unsplash-gym-hero-image*.jpg` and then center-cropped + compressed via Pillow before landing here. Originals are not committed.

If you want to attribute individual photographers per-issue (footer credit on the rendered email), the Unsplash URL of each original can be recorded here once known:

| File | Photographer | Unsplash URL |
|---|---|---|
| `01.jpg` | — | — |
| `02.jpg` | — | — |
| `03.jpg` | — | — |
| `04.jpg` | — | — |
| `05.jpg` | — | — |
| `06.jpg` | — | — |
| `07.jpg` | — | — |
| `08.jpg` | — | — |
| `09.jpg` | — | — |
| `10.jpg` | — | — |
| `11.jpg` | — | — |
| `12.jpg` | — | — |

## Replacing or extending the pool

To swap a photo or add more, drop new 1200×480 JPEGs in this folder using the next ordinal. Re-run the cropping helper (inlined in the Phase 3 commit) if you have an originals folder:

```bash
python3 - <<'PY'
from PIL import Image, ImageOps
from pathlib import Path
src = Path.home() / "Downloads" / "new-shot.jpg"
dst = Path(__file__).parent / "13.jpg"   # next ordinal
im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
im = ImageOps.fit(im, (1200, 480), method=Image.LANCZOS, centering=(0.5, 0.4))
im.save(dst, "JPEG", quality=80, optimize=True, progressive=True)
PY
```

Don't break the numeric sequence — gaps cause the rotation to skip cleanly but make ordering confusing.
