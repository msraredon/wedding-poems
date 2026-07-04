#!/usr/bin/env python3
"""
inventory.py — Stage 0/1a helper: catalog every raw input photo and track its
processing state, so adding more photos later is a trivial diff.

WHAT IT DOES
  1. Scans images/hires/<book>/ for every image file (heic/jpg/jpeg/png/tif).
  2. Computes a sha256 for each so identical content is recognized even if the
     file is renamed or re-added.
  3. Reads the existing manifest (intake_manifest.csv) if present and CARRIES
     FORWARD the human/pipeline columns (status, poem_ids, notes) for files
     whose content is unchanged.
  4. Writes the updated manifest and prints a summary:
       NEW      = files not seen before (status -> "pending")
       CHANGED  = same path, different sha256 (content replaced) -> "CHANGED"
       MISSING  = in manifest but no longer on disk (kept, status -> "missing")
  This is idempotent and safe to re-run any time you drop in more photos.

STATUS VALUES (the column you/the pipeline maintain)
  pending      newly seen, not yet transcribed
  transcribed  turned into one or more poems/poem-NNN.yaml (see poem_ids)
  skipped      intentionally not used (cover, blurry dup, non-poem page, ...)
  CHANGED      file content replaced since last run — re-check
  missing      previously catalogued file is gone from disk

USAGE
  python scripts/inventory.py            # update manifest, print summary
  python scripts/inventory.py --new      # also list every NEW file path
"""
import csv
import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
IMG_ROOT = REPO / "images" / "hires"
MANIFEST = REPO / "intake_manifest.csv"
IMG_EXTS = {".heic", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}
COLUMNS = ["relative_path", "book", "ext", "bytes", "sha256", "status", "poem_ids", "notes"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_disk() -> dict:
    found = {}
    for p in sorted(IMG_ROOT.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in IMG_EXTS:
            continue
        rel = p.relative_to(IMG_ROOT).as_posix()
        found[rel] = {
            "relative_path": rel,
            "book": p.relative_to(IMG_ROOT).parts[0] if len(p.relative_to(IMG_ROOT).parts) > 1 else "",
            "ext": p.suffix.lower().lstrip("."),
            "bytes": p.stat().st_size,
            "sha256": sha256(p),
        }
    return found


def load_manifest() -> dict:
    if not MANIFEST.exists():
        return {}
    with MANIFEST.open(newline="") as f:
        return {row["relative_path"]: row for row in csv.DictReader(f)}


def main() -> None:
    if not IMG_ROOT.exists():
        sys.exit(f"no image root at {IMG_ROOT}")
    found = scan_disk()
    prev = load_manifest()

    rows, new, changed = [], [], []
    for rel, info in found.items():
        old = prev.get(rel)
        if old is None:
            info.update(status="pending", poem_ids="", notes="")
            new.append(rel)
        elif old.get("sha256") != info["sha256"]:
            info.update(status="CHANGED",
                        poem_ids=old.get("poem_ids", ""),
                        notes=(old.get("notes", "") + " [content changed]").strip())
            changed.append(rel)
        else:
            info.update(status=old.get("status", "pending") or "pending",
                        poem_ids=old.get("poem_ids", ""),
                        notes=old.get("notes", ""))
        rows.append(info)

    missing = [rel for rel in prev if rel not in found]
    for rel in missing:
        old = dict(prev[rel])
        old["status"] = "missing"
        rows.append(old)

    rows.sort(key=lambda r: r["relative_path"])
    with MANIFEST.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLUMNS})

    on_disk = len(found)
    pending = sum(1 for r in rows if r["status"] == "pending")
    done = sum(1 for r in rows if r["status"] == "transcribed")
    print(f"manifest: {MANIFEST.relative_to(REPO)}")
    print(f"  on disk : {on_disk} images across {len({r['book'] for r in rows if r['book']})} books")
    print(f"  NEW     : {len(new)}")
    print(f"  CHANGED : {len(changed)}")
    print(f"  MISSING : {len(missing)}")
    print(f"  pending : {pending}   transcribed: {done}")
    if changed:
        print("\nCHANGED files (content replaced — re-check):")
        for r in changed:
            print(f"  {r}")
    if missing:
        print("\nMISSING files (were catalogued, now gone):")
        for r in missing:
            print(f"  {r}")
    if "--new" in sys.argv and new:
        print("\nNEW files:")
        for r in new:
            print(f"  {r}")


if __name__ == "__main__":
    main()
