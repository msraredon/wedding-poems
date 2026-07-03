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

## Status

Stage 0 (scaffold) complete. Scripts are stubs — implementation proceeds one
stage at a time, checking outputs together before moving on.
