#!/usr/bin/env python3
"""
render_faces.py — Stage 2: one poem YAML -> two PDF faces (poem + name).

WHAT IT WILL DO (not yet implemented — stub):
  Given a poem (and, for the name face, a guest name), build an HTML page sized
  to the favor trim + bleed from config.yaml, then print it to PDF with:
      Google Chrome --headless --print-to-pdf
  The HTML/CSS handles centering, margins, fonts, and bleed cleanly.

  KEY FEATURE — auto-fit: a small JS snippet in the page binary-searches the
  body font size between font_min_pt and font_max_pt until the poem exactly
  fills the safe area. This is why a 4-line and a 40-line poem both look right
  on identical paper — the single biggest reason we chose code over a GUI.

  - Poem face: poem centered; title/author styled distinctly below.
  - Name face: guest name at name_face.position, inside the safe margin so
    duplex drift + rolling never clip it.

Rendered faces land in build/faces/. build_pdf.py assembles them.
"""
import sys

def main():
    print(__doc__)
    print(">>> STUB: rendering logic not implemented yet. Confirm the plan first.")
    sys.exit(1)

if __name__ == "__main__":
    main()
