#!/usr/bin/env python3
"""
reconcile.py — make the manifest a derived view of the poem files.

The manifest (intake_manifest.csv) should never be hand-maintained: it is ground
truth ONLY for "which raw images exist" (that part comes from inventory.py). Which
image became which poem, and whether that poem still needs text, is ground truth in
the poems/*.yaml files. This script reads the poem files and writes those facts back
into the manifest, so renumbering or editing poems by hand can never desync it.

STATUS it writes (into the manifest 'status' + 'poem_ids' columns):
  transcribed        a poem YAML references this image AND has non-empty text
  needs_manual_text  a poem stub references this image but text is empty or the poem
                     has 'needs_manual_text: true' (usually a content-filter block)
  pending            no poem references this image yet
Images already marked 'skipped' are left as skipped. CHANGED/MISSING are preserved.

Run it any time after transcribing or after editing/renumbering poems:
  python scripts/reconcile.py
"""
import csv
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
POEMS = REPO / "poems"
MANIFEST = REPO / "intake_manifest.csv"


def poem_state():
    """Return {image_rel_path: (poem_ids, status)} from every poem YAML.

    One image can hold several poems (a book spread), so poem_ids accumulate as a
    ';'-joined list. status is 'transcribed' only if EVERY poem on the image has text.
    """
    ids, statuses = {}, {}
    for f in sorted(POEMS.glob("poem-*.yaml")):
        try:
            doc = yaml.safe_load(f.read_text())
        except yaml.YAMLError as e:
            print(f"  WARN: cannot parse {f.name}: {e}", file=sys.stderr)
            continue
        if not isinstance(doc, dict):
            continue
        pid = str(doc.get("id") or f.stem.replace(".DRAFT", ""))
        text = (doc.get("text") or "").strip()
        needs_manual = bool(doc.get("needs_manual_text", False))
        status = "transcribed" if (text and not needs_manual) else "needs_manual_text"
        for img in doc.get("images") or []:
            img = str(img)
            ids.setdefault(img, []).append(pid)
            statuses.setdefault(img, []).append(status)
    return {
        img: (";".join(sorted(set(pids))),
              "transcribed" if all(s == "transcribed" for s in statuses[img]) else "needs_manual_text")
        for img, pids in ids.items()
    }


def main():
    if not MANIFEST.exists():
        sys.exit("no manifest yet — run scripts/inventory.py first")
    states = poem_state()
    rows = list(csv.DictReader(MANIFEST.open(newline="")))
    cols = rows[0].keys() if rows else []

    counts = {"transcribed": 0, "needs_manual_text": 0, "pending": 0, "skipped": 0}
    for r in rows:
        rel = r["relative_path"]
        if r.get("status") == "skipped":
            counts["skipped"] += 1
            continue
        if rel in states:
            pid, status = states[rel]
            r["status"], r["poem_ids"] = status, pid
            counts[status] += 1
        elif r.get("status") in ("MISSING", "missing", "CHANGED"):
            pass
        else:
            r["status"], r["poem_ids"] = "pending", ""
            counts["pending"] += 1

    with MANIFEST.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    print("manifest reconciled from poems/:")
    for k in ("transcribed", "needs_manual_text", "pending", "skipped"):
        print(f"  {k:18} {counts[k]}")
    if counts["needs_manual_text"]:
        print("\n  images awaiting hand-entered text:")
        for r in rows:
            if r.get("status") == "needs_manual_text":
                print(f"    {r['relative_path']}  ({r['poem_ids']})")


if __name__ == "__main__":
    main()
