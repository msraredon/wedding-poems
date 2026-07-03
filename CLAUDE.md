# Wedding Favor Poems — Project Brief

## What we're building

Physical party favors for a wedding: tiny paper scrolls, one per guest, rolled and
tied with ribbon. Each scroll has the **guest's name** on the outside face and a
**specific poem** (with title + author attribution) on the inside face. We will take
the final print-ready file(s) to a print shop.

You (Claude Code) are building the pipeline that turns photographed poems + a
guest→poem spreadsheet into that print-ready output.

## Core mental model — keep these THREE layers separate

1. **Content store** — one canonical record per poem (text, title, author, source).
   Independent of who receives it.
2. **Assignment table** — an Excel sheet mapping guest → poem. The *only* place a
   guest name lives.
3. **Layout stage** — joins content + assignments and emits print-ready PDF pages.

Never entangle these. We must be able to re-transcribe a poem, reassign a guest, or
change paper size without touching the other two layers.

## Tooling decision (already made)

**Programmatic PDF generation, not InDesign.** Rationale: it's fully reproducible
(edit inputs, re-run, get a new PDF), config-driven (paper size is a parameter), and
you can build and run it end to end. Do NOT scaffold an InDesign/Illustrator workflow
unless explicitly asked to switch.

Recommended stack (propose alternatives if you see a reason):
- **Transcription:** Anthropic API with vision (Claude), called from a Python script.
- **Face rendering:** HTML/CSS → PDF via headless Chrome (preferred, for per-poem
  auto-fit) or WeasyPrint. CSS handles centering, margins, and fonts cleanly.
- **Imposition (only if we impose — see open question):** Python with `reportlab` /
  `pypdf` to place N faces per sheet with duplex mirroring and crop marks.

## Build order (each stage independently testable)

### Stage 0 — Scaffold
Create the folder structure, `config.yaml`, a README, and stub scripts. Then STOP and
confirm the open questions below before writing real logic.

Proposed layout:
```
images/hires/        # canonical high-res photo per poem, named by poem id
images/lores/        # low-res backups only
poems/               # one YAML per poem (or one combined poems.yaml)
guests.xlsx          # guest_name, poem_id
config.yaml          # all tunable parameters
scripts/             # transcribe.py, render_faces.py, impose.py
build/               # generated intermediates + final PDFs (gitignored)
```

### Stage 1 — Photos → verified text
This is the accuracy-critical stage. A poem is unforgiving about line breaks and
punctuation, and this is a permanent keepsake. The main risk is the model silently
"correcting" or smoothing a line, NOT classic OCR garble.

- Always transcribe from the **high-res** image.
- Use a strict transcription prompt. Baseline:
  > Transcribe the poem in this image exactly. Preserve line breaks, stanza breaks,
  > capitalization, and punctuation. Do not correct, modernize, or complete anything.
  > Mark any illegible word as [??]. Output the poem text, then title and author on
  > separate lines if visible.
- **Two-pass verification:** run each image twice, diff the outputs, and surface every
  difference for human review. Do not silently pick one.
- Write results as YAML with a block scalar so line breaks survive (CSV mangles them):
  ```yaml
  - id: poem-014
    title: "The Peace of Wild Things"
    author: "Wendell Berry"
    source: "The Selected Poems of Wendell Berry"
    verified: false   # human flips to true after eyeballing against the image
    text: |
      When despair for the world...
      ...
  ```
- Leave `verified: false` until a human confirms. Later stages should warn (or refuse,
  per config) on unverified poems.

### Stage 2 — Render faces
For each favor: one **poem face** and one **name face**, sized to the favor trim from
`config.yaml`, with bleed.

- **Auto-fit font size per poem.** A 4-line and a 40-line poem cannot share one fixed
  size on identical paper. Measure and shrink to fit within a configured
  `font_min_pt`/`font_max_pt` band. This is the single most important layout feature
  and the main reason we chose code over a GUI.
- Poem centered; attribution (title/author) styled distinctly below.
- Name face: place the name well inside the trim (generous safe margin) so duplex drift
  + rolling never clips it. Corner/position is configurable.

### Stage 3 — Assemble delivery PDF (imposition DROPPED)
The print shop imposes/gangs and cuts (decided — see below), so we do NOT build
imposition, duplex mirroring, or crop marks. Stage 3 is just: join `guests.xlsx`
with the poems, render each face, and assemble a clean **one-favor-per-page,
front + back, with bleed** PDF for delivery. (`scripts/build_pdf.py`.)

## config.yaml — tunables to expose
- favor trim size (w × h) and units
- bleed and safe margin
- favors per sheet (if imposing)
- fonts (poem body, attribution, name), font min/max pt for auto-fit
- whether unverified poems block the build

## Decisions (RESOLVED 2026-07-03)

1. **Imposition:** the **print shop** imposes/gangs/cuts. We deliver one favor per
   page, front + back, with bleed. Stage 3 is assembly only (no mirroring/crop marks).
2. **Printer specs:** not yet chosen. Building to the standard clean deliverable
   above; revisit exact bleed/format when a shop is picked.
3. **Scale:** ~120+ guests, ~70+ distinct poems.
4. **The "4–6":** it was the **scroll trim size in inches** (~4×6). Default trim is
   4"×6" in `config.yaml`.
5. **Variable length policy:** **auto-fit font within a band** (default). One trim
   size for all; the renderer shrinks each poem to fit.
6. **Transcription route:** **in-session** — Claude reads the images directly and
   writes the poem YAML. The API script (`scripts/transcribe.py`) remains a stub for
   later batch use; no `ANTHROPIC_API_KEY` needed for the current workflow.

## Conventions

- **Verification tag:** every poem YAML has `verified: false` + `verified_by:` +
  `verified_date:`. A human sets these after proofreading against the photo. The
  build refuses `verified: false` (config `build.block_on_unverified`).
- **Two-pass transcription:** each image is transcribed twice, independently
  (in-session via parallel subagents), and the outputs are diffed. Agreements are
  strong; disagreements are surfaced, never silently resolved.
- **DRAFT naming:** `poem-NNN.DRAFT.yaml` = needs human attention (passes disagreed,
  poor image, or hand-entry). Rename to `poem-NNN.yaml` once corrected.
- **Per-folder metadata:** each `images/hires/<book>/` has a `source.yaml` (book
  title, author/editor, translator). Poem `author`/`title` blank → fall back to it.
- **One image can hold multiple poems** (e.g. a book spread). Intake must let the
  human say *which* poem in an image is wanted — do not assume one image = one poem.

## Constraints
- Poems are transcribed from books we own, in small quantity, for a private event —
  ordinary personal use. No action needed unless the user asks to be conservative.
- Keep everything reproducible and re-runnable. Inputs are source of truth; `build/`
  is disposable.
