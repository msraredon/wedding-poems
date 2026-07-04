#!/usr/bin/env python3
"""
make_previews.py — convert a book's high-res HEIC/JPG photos into readable preview
JPGs under build/preview/<book>/, so they can be transcribed.

HEIC can't be viewed directly, so Stage 1 works off these previews. Originals in
images/hires/ remain the source of truth; build/preview/ is disposable.

USAGE
  python scripts/make_previews.py "<book-folder-name>"   # one book
  python scripts/make_previews.py --all                  # every book
  python scripts/make_previews.py --list                 # list book folders

Skips files whose preview already exists (unless --force). Uses macOS `sips`.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
IMG_ROOT = REPO / "images" / "hires"
PREVIEW_ROOT = REPO / "build" / "preview"
IMG_EXTS = {".heic", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}
LONG_EDGE = 2400  # px; enough to read small type, small enough to stay light


def books() -> list[str]:
    return sorted(p.name for p in IMG_ROOT.iterdir() if p.is_dir())


def convert_book(book: str, force: bool) -> tuple[int, int]:
    src_dir = IMG_ROOT / book
    if not src_dir.is_dir():
        raise SystemExit(f"no such book folder: {src_dir}")
    out_dir = PREVIEW_ROOT / book
    out_dir.mkdir(parents=True, exist_ok=True)
    made = skipped = 0
    for src in sorted(src_dir.iterdir()):
        if src.suffix.lower() not in IMG_EXTS:
            continue
        out = out_dir / (src.stem + ".jpg")
        if out.exists() and not force:
            skipped += 1
            continue
        subprocess.run(
            ["sips", "-s", "format", "jpeg", "-Z", str(LONG_EDGE), str(src), "--out", str(out)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        made += 1
    return made, skipped


def main() -> None:
    args = sys.argv[1:]
    force = "--force" in args
    args = [a for a in args if a != "--force"]
    if not args or args[0] == "--list":
        print("book folders:")
        for b in books():
            print(f"  {b}")
        return
    targets = books() if args[0] == "--all" else [args[0]]
    for b in targets:
        made, skipped = convert_book(b, force)
        print(f"{b}: {made} converted, {skipped} already present -> build/preview/{b}/")


if __name__ == "__main__":
    main()
