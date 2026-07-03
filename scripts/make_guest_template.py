#!/usr/bin/env python3
"""
make_guest_template.py — build a human-readable assignment template.

Scans poems/ and writes one row per poem with its id, title, and author already
filled in (author falls back to the folder's source.yaml), so you can recognize
each poem at a glance and just type guest names into the first column.

  guest_name , poem_id , title , author , source , verified , note
  ^^ you edit   ^^ used by build_pdf.py    ^^ reference only (ignored by build) ^^

Repeat / add rows freely (several guests can share a poem). Save as guests.xlsx
(or keep .csv — build_pdf.py reads both).

Usage:
  python3 scripts/make_guest_template.py                 # -> guests.template.csv
  python3 scripts/make_guest_template.py --out guests.csv
"""
import argparse
import csv
import glob
import os

import render_faces as rf

ROOT = rf.ROOT


def source_author(source):
    """Fall back to images/hires/<source>/source.yaml for author/editor."""
    if not source:
        return ""
    sp = os.path.join(ROOT, "images", "hires", source, "source.yaml")
    if not os.path.exists(sp):
        return ""
    s = rf.load_yaml(sp) or {}
    return (s.get("author") or s.get("editor") or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "guests.template.csv"))
    args = ap.parse_args()

    rows = []
    seen = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "poems", "*.yaml"))):
        base = os.path.basename(path)
        if base.startswith("EXAMPLE"):
            continue
        data = rf.load_yaml(path) or {}
        pid = data.get("id")
        if not pid:
            continue
        is_draft = ".DRAFT." in base
        # prefer a non-draft file if both exist for the same id
        if pid in seen and not is_draft:
            seen[pid] = None  # will be overwritten below
        elif pid in seen:
            continue
        title = (data.get("title") or "").strip()
        author = (data.get("author") or "").strip() or source_author(data.get("source"))
        note = "DRAFT — needs human fix/verify" if is_draft else ""
        seen[pid] = len(rows)
        rows.append(["", pid, title, author, data.get("source", ""),
                     str(bool(data.get("verified"))).lower(), note])

    rows.sort(key=lambda r: r[1])
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["guest_name", "poem_id", "title", "author",
                    "source", "verified", "note"])
        w.writerows(rows)
    print(f"Wrote {args.out}  ({len(rows)} poems)")


if __name__ == "__main__":
    main()
