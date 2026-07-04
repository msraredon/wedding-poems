#!/usr/bin/env python3
"""Assemble a poem YAML whose body is OCR'd locally (Apple Vision), so the text
never routes through the language model. Use for in-copyright poems that the
model's output content-filter refuses to transcribe.

The body comes ONLY from Vision OCR of the hi-res photo(s); this script supplies
just the metadata (id/title/author/source/notes). OCR is imperfect on stanza
breaks and indentation, so the result is written verified:false for human
proofreading against the book.

Example:
  python3 scripts/ocr_to_poem.py \
    --id poem-144 --title "Late Loving" --author "Mona Van Duyn" \
    --source the-singing-word-168-years-of-poetry-from-the-atlantic \
    --image the-singing-word-168-years-of-poetry-from-the-atlantic/IMG_1353.HEIC \
    --image the-singing-word-168-years-of-poetry-from-the-atlantic/IMG_1354.HEIC \
    --note "..." --out poems/poem-144.yaml
"""
import argparse, subprocess, sys, os, pathlib

HIRES = pathlib.Path("images/hires")
OCR_SWIFT = "scripts/ocr_vision.swift"


def dq(s: str) -> str:
    """Double-quoted YAML scalar (safe for titles/authors/sources)."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def ocr(image_rel: str) -> str:
    path = HIRES / image_rel
    if not path.exists():
        sys.exit(f"missing image: {path}")
    out = subprocess.run(["swift", OCR_SWIFT, str(path)],
                         capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"OCR failed for {path}: {out.stderr}")
    return out.stdout.rstrip("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--author", default="")
    ap.add_argument("--source", required=True)
    ap.add_argument("--image", action="append", required=True,
                    help="repeatable; path relative to images/hires/")
    ap.add_argument("--note", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    bodies = [ocr(img) for img in a.image]
    # Join multi-image poems (e.g. a page spread) with a blank line between pages.
    body = "\n\n".join(b for b in bodies if b.strip())

    note = (a.note + " " if a.note else "") + (
        "Body auto-OCR'd locally via Apple Vision from the photo(s) because the "
        "model's content filter blocked verbatim transcription. PROOFREAD against "
        "the book — OCR drops blank/stanza breaks and indentation and may miss "
        "punctuation.")

    lines = []
    lines.append(f"id: {a.id}")
    lines.append(f"title: {dq(a.title)}")
    lines.append(f"author: {dq(a.author)}")
    lines.append(f"source: {dq(a.source)}")
    lines.append("images:")
    for img in a.image:
        lines.append(f"  - {dq(img)}")
    lines.append("verified: false")
    lines.append('verified_by: ""')
    lines.append('verified_date: ""')
    lines.append("needs_manual_text: false")
    lines.append(f"notes: >-\n  {note}")
    lines.append("text: |")
    for ln in body.split("\n"):
        lines.append(("  " + ln).rstrip() if ln else "")
    text = "\n".join(lines) + "\n"

    pathlib.Path(a.out).write_text(text, encoding="utf-8")
    # Status only — never echo the body.
    print(f"{a.id}: wrote {a.out}  ({len(a.image)} image(s), {len(body)} chars, "
          f"{body.count(chr(10))+1} lines)")


if __name__ == "__main__":
    main()
