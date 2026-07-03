#!/usr/bin/env python3
"""
intake.py — Stage 1a: turn a pile of photos into one poem record per poem.

WHAT IT WILL DO (not yet implemented — stub):
  1. Scan images/hires/<source>/... for all photos.
  2. Show them to you grouped by source folder so you can say which images
     belong together (a multi-page poem = several images, in reading order).
  3. Create one poems/poem-NNN.yaml per poem with:
       - source  = the folder it came from (provenance)
       - images  = ordered list of that poem's photos
       - title/author left blank for you to fill (or lifted later from the photo)
       - verified: false
       - text: ""   (filled by transcribe.py)
  4. Never overwrite an existing poem YAML — this step is idempotent and safe
     to re-run as you add more photos.

This is the ONLY step that decides which images form which poem. Keeping it
separate means re-transcribing never re-groups, and re-grouping never edits text.
"""
import sys

def main():
    print(__doc__)
    print(">>> STUB: intake logic not implemented yet. Confirm the plan first.")
    sys.exit(1)

if __name__ == "__main__":
    main()
