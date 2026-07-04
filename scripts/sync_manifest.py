#!/usr/bin/env python3
"""
sync_manifest.py — derive the intake manifest's processing state from poems/.

The poem YAMLs are the SOURCE OF TRUTH for which image became which poem. This
script reads every poems/poem-*.yaml (including *.DRAFT.yaml), maps each image it
references back to intake_manifest.csv, and sets:
    status   = transcribed   (poem has real text)
             | flagged       (DRAFT file, or needs_text: true, or empty text —
                              e.g. a poem whose text tripped a content filter and
                              must be hand-entered)
    poem_ids = the poem id(s) that use that image

Images not referenced by any poem keep whatever status inventory.py gave them
(usually "pending"). Re-run any time after adding/renumbering/editing poems —
it is idempotent and never touches the image files.

Because state is DERIVED, renumbering or re-transcribing poems can never desync
the manifest: just re-run this.

USAGE
  python scripts/sync_manifest.py
"""
import csv
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
POEMS = REPO / "poems"
MANIFEST = REPO / "intake_manifest.csv"


def poem_state(path: Path) -> tuple[str, bool, str]:
    """Return (poem_id, is_flagged, reason) for one poem YAML."""
    data = yaml.safe_load(path.read_text()) or {}
    pid = str(data.get("id") or path.stem.replace(".DRAFT", ""))
    text = (data.get("text") or "").strip()
    is_draft = ".DRAFT" in path.name
    needs_text = bool(data.get("needs_text"))
    if needs_text or not text:
        return pid, True, "needs_text: hand-enter (content-filtered or blank)"
    if is_draft:
        return pid, True, "DRAFT: needs human decision"
    return pid, False, ""


def main() -> None:
    if not MANIFEST.exists():
        raise SystemExit("no intake_manifest.csv — run scripts/inventory.py first")

    # image relpath -> (poem_id, flagged, reason)
    img_map: dict[str, tuple[str, bool, str]] = {}
    for path in sorted(POEMS.glob("poem-*.yaml")):
        data = yaml.safe_load(path.read_text()) or {}
        pid, flagged, reason = poem_state(path)
        for img in data.get("images") or []:
            img_map[str(img)] = (pid, flagged, reason)

    rows = list(csv.DictReader(MANIFEST.open()))
    cols = rows[0].keys()
    changed = 0
    for r in rows:
        hit = img_map.get(r["relative_path"])
        if not hit:
            continue
        pid, flagged, reason = hit
        new_status = "flagged" if flagged else "transcribed"
        new_notes = reason if flagged else r.get("notes", "")
        if (r["status"], r["poem_ids"], r.get("notes", "")) != (new_status, pid, new_notes):
            r["status"], r["poem_ids"], r["notes"] = new_status, pid, new_notes
            changed += 1

    with MANIFEST.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    tally: dict[str, int] = {}
    for r in rows:
        tally[r["status"]] = tally.get(r["status"], 0) + 1
    print(f"synced manifest from {len(img_map)} image references; {changed} rows updated")
    for k in sorted(tally):
        print(f"  {k:12} {tally[k]}")


if __name__ == "__main__":
    main()
