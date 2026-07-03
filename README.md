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
photos ─▶ intake.py ─▶ transcribe.py ─▶ [human verifies] ─▶ build_pdf.py ─▶ PDF
          (group into    (2-pass diff,      (flip            (join w/ guests.xlsx,
           poems)         no silent fixes)   verified:true)    render faces)
```

1. **Intake** — group photos into poems (multi-page poem = several images).
2. **Transcribe** — high-res photo → text, run twice and diff, human confirms.
   Accuracy-critical: the model must not "fix" line breaks or punctuation.
3. **Verify** — a human compares each poem to its photo and sets `verified:true`.
4. **Build** — join with `guests.xlsx`, auto-fit each poem to the page, emit PDF.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...        # for transcription
```

Rendering uses your installed Google Chrome (`--headless --print-to-pdf`);
the poem body font in `config.yaml` must be installed on this machine.

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
- `poem-NNN.yaml` — clean draft (both passes agreed).
- `poem-NNN.DRAFT.yaml` — needs human attention (passes disagreed / low confidence /
  hand-entry required). Rename to `poem-NNN.yaml` once corrected.

### Per-folder source metadata
Each `images/hires/<book>/` folder has a `source.yaml` with the book's title,
author/editor, translator, etc. If a poem's own `author`/`title` is blank, layout
falls back to the folder's `source.yaml`. Fill these in once per book.

## Running the pipeline

```bash
source .venv/bin/activate          # deps: pyyaml, openpyxl, pypdf (+ system Chrome)

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
- **Stage 1 (transcribe):** proven on a 7-poem test batch (5/7 clean on two-pass
  agreement; 2 flagged for hand-correction). In-session for now; `transcribe.py`
  API script still a stub.
- **Stage 2 (render faces):** done — HTML/CSS → PDF via headless Chrome, JS
  auto-fit, EB Garamond, bleed + safe margins, configurable name corner.
- **Stage 3 (assemble):** done — guests.xlsx → one-favor-per-page delivery PDF,
  with the verified-poem safety gate.

Remaining before a real print run: fill `source.yaml` metadata, hand-fix
poems 004 & 007, verify poems (`verified: true`), build the real `guests.xlsx`,
move `images/hires/` to git-lfs, and pick a printer (confirm bleed/format).
