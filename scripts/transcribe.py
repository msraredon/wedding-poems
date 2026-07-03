#!/usr/bin/env python3
"""
transcribe.py — Stage 1b: photos -> verified poem text (accuracy-critical).

WHAT IT WILL DO (not yet implemented — stub):
  For each poem YAML with text still empty (or --force):
    1. Load its HIGH-RES image(s), in order. Multi-page poems send all pages.
    2. Call the Claude vision model TWICE with a strict "change nothing" prompt:
         "Transcribe the poem exactly. Preserve line breaks, stanza breaks,
          capitalization, punctuation, spacing. Do not correct, modernize, or
          complete anything. Mark illegible words [??]. Then title and author
          on separate lines if visible."
    3. DIFF the two passes. If they disagree, print a line-by-line diff and
       leave the poem for human review — never silently pick one.
    4. When both passes agree, write the text into the poem YAML as a block
       scalar (line breaks preserved) with verified:false.
  A human then compares against the photo and flips verified:true by hand.

Idempotent: skips poems that already have text unless --force. Requires
ANTHROPIC_API_KEY in the environment.
"""
import sys

def main():
    print(__doc__)
    print(">>> STUB: transcription logic not implemented yet. Confirm the plan first.")
    sys.exit(1)

if __name__ == "__main__":
    main()
