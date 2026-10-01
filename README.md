# The Bars of Lynn

A 1986 field study of forty bars in Lynn, Massachusetts, reproduced in full.

**Live site: https://octocog.github.io/bars-of-lynn/**

In the summer of 1986 two engineers at the General Electric plant in Lynn set out to
visit every bar in the city. They managed forty across eleven nights between 2 August
and 12 September, photographed most of them, and typed the whole thing up as a mock
academic paper. It was never published. A photocopy surfaced in a desk drawer thirty
years later.

## How this repository works

Nothing in `docs/` is written by hand. It is generated.

| File | What it is |
|---|---|
| `LYNN BARS.PDF` | The source. 45 scanned pages, no text layer. |
| `transcript.md` | Full transcription, typed exactly as typed. The authority for all body text. |
| `bars.json` | Structured data per bar: dates, addresses, fate, confidence, notes. |
| `build.py` | Generates the whole site. |
| `assets_style.css` | The stylesheet, copied into the build. |
| `research/` | Address and current-status research, with sources and confidence levels. |
| `docs/` | **The built site. Do not edit.** |

```bash
python3 build.py          # rebuilds docs/ from transcript.md + bars.json
```

To regenerate the page images from the PDF (they are gitignored):

```bash
python3 - <<'PY'
import fitz, os
os.makedirs("scans_web", exist_ok=True)
d = fitz.open("LYNN BARS.PDF")
for i, p in enumerate(d):
    p.get_pixmap(dpi=200).save(f"/tmp/p.png")
    from PIL import Image
    im = Image.open("/tmp/p.png").convert("L")
    w, h = im.size; s = min(1.0, 1500/h)
    im.resize((round(w*s), round(h*s))).save(
        f"scans_web/page-{i+1:02d}.jpg", quality=74, optimize=True, progressive=True)
PY
```

## Adding an address

Edit `bars.json`, set `address`, `addr_conf` (`high` / `medium` / `low`) and `addr_why`,
then rerun `build.py`. Guesses go in `addr_guess` and render differently, in grey
italic, so a reader can always tell what is known from what is supposed.

## Before you make this repository private

Don't. On a free plan a private repository cannot publish GitHub Pages, and switching
to private does not hide the site, it **deletes the Pages configuration**. Switching
back to public does not restore it; Pages has to be switched on again separately under
Settings, then Pages, source `main` and folder `/docs`.

## The text

Everything is reproduced as typed in 1986. Spelling, punctuation and typing errors are
left alone. So is the language, some of which belongs to its moment. Nothing has been
corrected, softened or cut. An archive that quietly edits its own source is worth less
than no archive at all.

## Still missing

- Most of the addresses. The 1986 Lynn city directory is not digitised anywhere
  reachable; the remaining ones need the physical volume at Lynn Public Library.
- **Number 27, The Arena.** It is in the index and has no entry. Either it was never
  written or a page is missing from the photocopy.

---

*A Field Study*, by James Francis Murnane II and Grant Arthur Albert.
Typed by Fran. Lynn, Massachusetts, August to December 1986.
