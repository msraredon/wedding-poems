#!/usr/bin/env python3
"""Structural cleanup for OCR'd poem YAML — operate on the `text: |` block by
POSITION (line number) or by known non-poem label, so an in-copyright body can be
restructured without the poem text ever passing through the caller's output.

The body is the run of lines after `text: |` (which ocr_to_poem.py writes last).
Body lines are 1-indexed, blank lines included. Prints ONLY line-number actions
and a final line count — never the body content.

Ops (apply one kind per call so indices stay predictable):
  --strip-labels        drop body lines that are just a running head / page number
                        (rupi kaur | home body | a bare number)
  --remove N [N ...]    drop body line(s) N
  --blank-before N ...  insert one blank line before body line(s) N (stanza break)
  --blank-after N ...   insert one blank line after body line(s) N
  --swap A B            swap body lines A and B (fix OCR line-order transposition)

Example:
  python3 scripts/fix_structure.py poems/poem-187.yaml --strip-labels
  python3 scripts/fix_structure.py poems/poem-187.yaml --blank-before 3 9
"""
import argparse, re, sys, pathlib

LABELS = {"rupi kaur", "home body"}
PAGENUM = re.compile(r"^\d{1,3}$")
INDENT = "  "


def split(path):
    lines = pathlib.Path(path).read_text(encoding="utf-8").split("\n")
    # find `text: |`
    for i, ln in enumerate(lines):
        if ln.rstrip() == "text: |" or ln.rstrip() == "text: |-":
            return lines[: i + 1], lines[i + 1 :]
    sys.exit(f"{path}: no `text: |` block found")


def body_content(raw_body):
    # raw_body may have a trailing '' from the final newline; keep real body lines
    b = list(raw_body)
    while b and b[-1] == "":
        b.pop()
    return b


def write(path, head, body):
    text = "\n".join(head + [(INDENT + l).rstrip() if l.strip() else "" for l in body]) + "\n"
    pathlib.Path(path).write_text(text, encoding="utf-8")


def unindent(body):
    out = []
    for l in body:
        out.append(l[2:] if l.startswith(INDENT) else l.lstrip() if l.strip() else "")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--strip-labels", action="store_true")
    ap.add_argument("--remove", nargs="+", type=int, default=[])
    ap.add_argument("--blank-before", nargs="+", type=int, default=[])
    ap.add_argument("--blank-after", nargs="+", type=int, default=[])
    ap.add_argument("--swap", nargs=2, type=int, default=None, metavar=("A", "B"))
    a = ap.parse_args()

    head, raw_body = split(a.path)
    body = unindent(body_content(raw_body))
    n0 = len(body)
    actions = []

    if a.swap:
        i, j = a.swap[0] - 1, a.swap[1] - 1
        if not (0 <= i < len(body) and 0 <= j < len(body)):
            sys.exit(f"{a.path}: swap index out of range (body has {len(body)} lines)")
        body[i], body[j] = body[j], body[i]
        actions.append(f"swapped lines {a.swap[0]} and {a.swap[1]}")

    if a.strip_labels:
        kept, dropped = [], 0
        for l in body:
            s = l.strip().lower()
            if s in LABELS or PAGENUM.match(l.strip()):
                dropped += 1
            else:
                kept.append(l)
        body = kept
        actions.append(f"stripped {dropped} label line(s)")

    if a.remove:
        drop = set(a.remove)
        body = [l for i, l in enumerate(body, 1) if i not in drop]
        actions.append(f"removed line(s) {sorted(drop)}")

    if a.blank_before or a.blank_after:
        before = set(a.blank_before)
        after = set(a.blank_after)
        out = []
        for i, l in enumerate(body, 1):
            if i in before:
                out.append("")
            out.append(l)
            if i in after:
                out.append("")
        body = out
        if before:
            actions.append(f"blank before {sorted(before)}")
        if after:
            actions.append(f"blank after {sorted(after)}")

    write(a.path, head, body)
    print(f"{a.path}: {n0} -> {len(body)} body lines" + ("  [" + "; ".join(actions) + "]" if actions else ""))


if __name__ == "__main__":
    main()
