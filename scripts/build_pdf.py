#!/usr/bin/env python3
"""
build_pdf.py — Stage 3: join assignments + content -> final print-ready PDF.

Reads guests.xlsx (guest_name, poem_id), validates, renders each favor's poem
face and name face (Stage 2), and assembles a delivery PDF: one favor per page,
poem + name, WITH BLEED. We do NOT impose — the print shop gangs/cuts.

Safety: refuses any poem still `verified: false` (config build.block_on_unverified)
or any *.DRAFT.yaml, unless --allow-unverified is passed (proofing only).

Usage:
  python3 scripts/build_pdf.py
  python3 scripts/build_pdf.py --guests build/demo-guests.xlsx --allow-unverified
"""
import argparse
import csv
import glob
import os
import sys

import render_faces as rf
from pypdf import PdfWriter

ROOT = rf.ROOT


def load_poem_index():
    """Map poem id -> (path, is_draft, data). Prefer non-DRAFT when both exist."""
    idx = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "poems", "*.yaml"))):
        base = os.path.basename(path)
        if base.startswith("EXAMPLE"):
            continue
        data = rf.load_yaml(path) or {}
        pid = data.get("id")
        if not pid:
            continue
        is_draft = ".DRAFT." in base
        if pid not in idx or (idx[pid][1] and not is_draft):
            idx[pid] = (path, is_draft, data)
    return idx


def read_guests(path):
    rows = []
    if path.lower().endswith((".xlsx", ".xlsm")):
        import openpyxl
        ws = openpyxl.load_workbook(path, read_only=True, data_only=True).active
        header = None
        for r in ws.iter_rows(values_only=True):
            if r is None or all(c is None for c in r):
                continue
            if header is None:
                header = [str(c).strip().lower() if c is not None else "" for c in r]
                continue
            rows.append({header[i]: (r[i] if i < len(r) else None)
                         for i in range(len(header))})
    else:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows.append({(k or "").strip().lower(): v for k, v in row.items()})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guests", default=os.path.join(ROOT, "guests.xlsx"))
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "wedding-favors.pdf"))
    ap.add_argument("--allow-unverified", action="store_true",
                    help="DANGER: include unverified/DRAFT poems (proofing only)")
    args = ap.parse_args()

    cfg = rf.load_config()
    g = rf.geometry(cfg)
    block = bool(cfg.get("build", {}).get("block_on_unverified", True))
    order = cfg.get("render", {}).get("page_order", "interleave")

    if not os.path.exists(args.guests):
        sys.exit(f"guests file not found: {args.guests}")
    guests = read_guests(args.guests)
    if not guests:
        sys.exit("no guest rows found")
    idx = load_poem_index()

    # ---- validate ----
    blocking, warnings = [], []
    for i, row in enumerate(guests, 1):
        name = str(row.get("guest_name") or "").strip()
        pid = str(row.get("poem_id") or "").strip()
        if not name:
            blocking.append(f"row {i}: missing guest_name")
        if not pid:
            blocking.append(f"row {i}: missing poem_id"); continue
        if pid not in idx:
            blocking.append(f"row {i}: poem_id '{pid}' not found in poems/"); continue
        _, is_draft, data = idx[pid]
        if not bool(data.get("verified")) and block:
            (warnings if args.allow_unverified else blocking).append(
                f"row {i}: poem '{pid}' is not verified (verified: false)")
        if is_draft:
            (warnings if args.allow_unverified else blocking).append(
                f"row {i}: poem '{pid}' is a DRAFT (needs human correction)")

    if blocking:
        print("BUILD REFUSED — fix these first:")
        for p in blocking:
            print("   -", p)
        print("\n(Or pass --allow-unverified to render a PROOF anyway.)")
        sys.exit(1)
    for w in warnings:
        print("WARNING:", w)
    if warnings:
        print("--> proceeding because --allow-unverified was set (PROOF, not final)\n")

    # ---- render + assemble ----
    facedir = os.path.join(ROOT, "build", "faces")
    writer = PdfWriter()
    manifest = []

    def render_favor(name, pid):
        data = idx[pid][2]
        poem_pdf = os.path.join(facedir, f"{pid}.poem.pdf")
        rf.render_pdf(rf.poem_html(data, cfg, g, False), poem_pdf)
        name_pdf = os.path.join(facedir, f"{pid}.name.{rf.slug(name)}.pdf")
        rf.render_pdf(rf.name_html(name, cfg, g, False), name_pdf)
        return poem_pdf, name_pdf, data

    rendered = []
    for row in guests:
        name = str(row["guest_name"]).strip()
        pid = str(row["poem_id"]).strip()
        rendered.append((name, pid) + render_favor(name, pid))

    if order == "separate":         # all poem pages, then all name pages
        for name, pid, poem_pdf, name_pdf, data in rendered:
            writer.append(poem_pdf)
        for name, pid, poem_pdf, name_pdf, data in rendered:
            writer.append(name_pdf)
    else:                            # interleave: poem (front) + name (back) per favor
        for name, pid, poem_pdf, name_pdf, data in rendered:
            writer.append(poem_pdf)
            writer.append(name_pdf)

    for name, pid, poem_pdf, name_pdf, data in rendered:
        manifest.append((name, pid, data.get("title", ""), data.get("author", "")))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "wb") as f:
        writer.write(f)

    mpath = os.path.join(os.path.dirname(args.out), "manifest.csv")
    with open(mpath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["guest_name", "poem_id", "title", "author"])
        for name, pid, title, author in manifest:
            w.writerow([name, pid, title, author])

    print(f"Wrote {args.out}  ({len(guests)} favors, {2 * len(guests)} pages, order={order})")
    print(f"Manifest: {mpath}")


if __name__ == "__main__":
    main()
