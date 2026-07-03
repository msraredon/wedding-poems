#!/usr/bin/env python3
"""
build_pdf.py — Stage 3: join assignments + content -> final print-ready PDF.

WHAT IT WILL DO (not yet implemented — stub):
  1. Read guests.xlsx (columns: guest_name, poem_id) — the ONLY place names live.
  2. Validate: every poem_id exists, and (if config build.block_on_unverified)
     every referenced poem is verified:true. Refuse and list problems otherwise.
  3. For each guest row, render the name face and the poem face (Stage 2).
  4. Assemble into the delivery PDF(s) for the print shop:
       one favor per page, name page + poem page, WITH BLEED.
     Page order (interleaved vs separate) comes from config render.page_order.
     We do NOT impose/gang — the print shop does that.

  Output: build/wedding-favors.pdf  (+ a build/manifest.csv listing what got
  printed for which guest, so you can proof it).

Re-runnable: regenerates everything from inputs. build/ is disposable.
"""
import sys

def main():
    print(__doc__)
    print(">>> STUB: assembly logic not implemented yet. Confirm the plan first.")
    sys.exit(1)

if __name__ == "__main__":
    main()
