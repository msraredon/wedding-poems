# Wedding Favor Poems

A reproducible pipeline that turns **photographed poems** + a **guest→poem
spreadsheet** into a **print-ready PDF** of scroll favors — each scroll has a
guest's name on the outside and their assigned poem on the inside.

Read `CLAUDE.md` for the full design brief. This README is the operating manual.

## The three layers (never entangle them)

| Layer | Lives in | Knows about |
|-------|----------|-------------|
| **Content** — one record per poem | `poems/*.yaml` | text, title, author, source. NOT guests. |
| **Assignments** — guest → poem | `guests.xlsx` | the only place a guest name lives. |
| **Layout** — joins the two, emits PDF | `scripts/` → `build/` | nothing permanent; fully regenerated. |

You can re-transcribe a poem, reassign a guest, or change paper size by editing
one layer and re-running — without touching the others.

## Decisions locked for this project

- **Layout = programmatic PDF** (not InDesign). Fully reproducible.
- **Scroll trim ≈ 4" × 6"** (adjustable in `config.yaml`).
- **The print shop imposes/gangs & cuts.** We deliver one favor per page,
  front + back, with bleed. No imposition stage on our side.
- **Scale:** ~120+ guests, ~70+ distinct poems.

## Layout of this repo

```
images/hires/<source>/   your high-res photos, one folder per book (INPUT)
images/lores/            low-res backups only (gitignored)
poems/                   one YAML per poem: text + title + author + source
guests.xlsx              guest_name, poem_id  (start from guests.template.csv)
config.yaml              every tunable parameter
scripts/                 intake -> transcribe -> render_faces -> build_pdf
build/                   generated PDFs + intermediates (gitignored, disposable)
```

## The pipeline (each stage independently testable)

```
photos ─▶ inventory.py ─▶ make_previews.py ─▶ transcribe ─▶ reconcile.py ─▶ [human ─▶ build_pdf.py ─▶ PDF
          (catalog +        (HEIC→JPG for      (in-session   (rebuild        verifies]  (join w/ guests.xlsx,
           manifest)         the model to read)  or OCR)      manifest)                  render faces)
```

1. **Inventory** — `inventory.py` catalogs raw photos and flags NEW/CHANGED/MISSING
   in `intake_manifest.csv`. Group photos into poems (a multi-page poem = several images;
   one image can also hold several poems).
2. **Preview** — `make_previews.py <book>` makes JPGs the model can read.
3. **Transcribe** — high-res photo → text. Two routes, both writing one poem at a time:
   - **In-session** (default): the model reads the photo and writes the YAML. Accuracy-
     critical — it must not "fix" line breaks or punctuation. Two-step durable write so a
     content-filter block never loses already-written work.
   - **Local OCR-to-disk** (`ocr_to_poem.py`): for **in-copyright** bodies the API's output
     content filter blocks. Text flows photo → Apple Vision (`ocr_vision.swift`) → file,
     never through the model; the model supplies only metadata. Written `verified: false`
     with a proofread note (OCR drops stanza breaks/indentation and grabs running heads).
4. **Reconcile** — `reconcile.py` rederives manifest status/poem_ids from the poem files,
   so renumbering can't desync it.
5. **Verify** — a human compares each poem to its photo and sets `verified: true`.
6. **Build** — join with `guests.xlsx`, auto-fit each poem to the page, emit PDF.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...        # only for the batch transcribe.py stub (unused in the current in-session workflow)
```

Rendering uses your installed Google Chrome (`--headless --print-to-pdf`);
the poem body font in `config.yaml` must be installed on this machine.

Local OCR (`ocr_to_poem.py`) uses Apple's Vision framework via `swift`, so it
requires **macOS with the Swift toolchain** (Xcode command-line tools). No API key.

## A note on images in git

High-res photos are inputs (source of truth). If they bloat the repo, move them
to [git-lfs](https://git-lfs.com) rather than deleting them. Low-res copies are
gitignored.

## Conventions

### The verification tag
Every poem YAML carries:
- `verified: false` — set to `true` ONLY after a human reads it against the photo.
- `verified_by:` / `verified_date:` — who checked it and when (audit trail).

The build stage refuses `verified: false` poems (config `build.block_on_unverified`),
so nothing unproofed can reach the printer.

### File naming during transcription
- `poem-NNN.yaml` — body captured; still `verified: false` until a human proofreads it.
- `poem-NNN.DRAFT.yaml` — needs a human decision: multi-poem page, untitled continuation,
  poem spanning images, duplicate to dedupe, or poor image. Rename to `poem-NNN.yaml`
  once resolved.
- `needs_manual_text: true` — a metadata-only stub whose body isn't in yet (content-filter
  block or non-Latin script). The human hand-enters the text and flips it to `false`.

### Per-folder source metadata
Each `images/hires/<book>/` folder has a `source.yaml` with the book's title,
author/editor, translator, etc. If a poem's own `author`/`title` is blank, layout
falls back to the folder's `source.yaml`. Fill these in once per book.

## Running the pipeline

```bash
source .venv/bin/activate          # deps: pyyaml, openpyxl, pypdf (+ system Chrome)

# (prep) regenerate the assignment template with titles/authors auto-filled,
# so you can recognize each poem and just type guest names into column 1
python3 scripts/make_guest_template.py

# Stage 2 — render one poem's faces (proof mode draws trim/safe guides)
python3 scripts/render_faces.py --poem poems/poem-005.yaml --name "Ada Lovelace" --proof

# Stage 3 — full delivery PDF from a guest sheet
python3 scripts/build_pdf.py --guests guests.xlsx
#   refuses unverified poems by default; add --allow-unverified for a PROOF only
```

Outputs land in `build/` (gitignored): `wedding-favors.pdf` + `manifest.csv`,
plus per-face PDFs/PNGs in `build/faces/`.

## Status

- **Stage 0 (scaffold):** done.
- **Stage 1 (transcribe):** intake swept across all books. **198 poems transcribed**
  (ids run to poem-205; some are DRAFT/dedupe stubs), **0 pending**, **18
  `needs_manual_text`** awaiting hand-entry (Rumi, Sappho, Shevchenko, Nezahualcóyotl,
  one Sharon Olds; plus a few empty dedupe stubs). In-copyright bodies were captured
  via local OCR-to-disk (`ocr_to_poem.py`); `transcribe.py` API script stays a stub.
  Manifest is rebuilt from the poem files by `reconcile.py`.
- **Stage 2 (render faces):** done — HTML/CSS → PDF via headless Chrome, JS
  auto-fit, EB Garamond, bleed + safe margins, configurable name corner.
- **Stage 3 (assemble):** done — guests.xlsx → one-favor-per-page delivery PDF,
  with the verified-poem safety gate.

Remaining before a real print run: **proofread OCR'd bodies** and flip poems to
`verified: true`, hand-enter the `needs_manual_text` poems, resolve the `DRAFT`
files (dedupe/split), fill any missing `source.yaml` metadata, build the real
`guests.xlsx`, and pick a printer (confirm bleed/format). Images are tracked in
git-lfs (see `.gitattributes`).
