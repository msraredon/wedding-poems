#!/usr/bin/env python3
"""
render_faces.py — Stage 2: one poem YAML -> print-ready PDF faces (poem + name).

Builds an HTML page sized to the favor trim + bleed from config.yaml, then prints
it to PDF with headless Google Chrome. Auto-fit is done in JS in the page: it
binary-searches the body font size between font_min_pt and font_max_pt until the
whole poem (title + text + author) exactly fills the safe area.

Usage:
  python3 scripts/render_faces.py --poem poems/poem-005.yaml
  python3 scripts/render_faces.py --poem poems/poem-005.yaml --name "Eleanor Whitfield"
  python3 scripts/render_faces.py --poem poems/poem-005.yaml --proof   # draw guides

Outputs (build/faces/):
  <id>.poem.pdf / .png                 clean poem face
  <id>.name.<slug>.pdf / .png          name face (when --name given)
  *.proof.png                          with trim (red) + safe (blue) guides (--proof)

For each PDF we also emit a 300-dpi PNG preview via pdftoppm for easy eyeballing.
"""
import argparse
import html
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


# ---------------------------------------------------------------- config / yaml
def _strip_quotes(v):
    v = v.strip()
    if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
        return v[1:-1]
    return v.split("  #")[0].split(" #")[0].strip()


def load_yaml(path):
    """Prefer PyYAML; fall back to a minimal parser for our simple schema."""
    try:
        import yaml  # type: ignore
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        pass
    data, lines, i = {}, open(path, encoding="utf-8").read().split("\n"), 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^text:\s*\|", line):
            block, i = [], i + 1
            while i < len(lines):
                l = lines[i]
                if l.strip() == "":
                    block.append(""); i += 1; continue
                if l.startswith("  "):
                    block.append(l[2:]); i += 1; continue
                break
            data["text"] = "\n".join(block).rstrip("\n")
            continue
        m = re.match(r"^([A-Za-z_][\w]*):\s*(.*)$", line)
        if m and m.group(2) != "" and not m.group(2).startswith((">", "|")):
            data[m.group(1)] = _strip_quotes(m.group(2))
        i += 1
    return data


def load_config():
    cfg = load_yaml(os.path.join(ROOT, "config.yaml"))
    if not isinstance(cfg, dict):
        sys.exit("Could not parse config.yaml (install PyYAML: pip install pyyaml)")
    return cfg


# ---------------------------------------------------------------- geometry
def geometry(cfg):
    fav = cfg["favor"]
    w, h = float(fav["width"]), float(fav["height"])
    bleed, safe = float(fav["bleed"]), float(fav["safe_margin"])
    return {
        "page_w": w + 2 * bleed, "page_h": h + 2 * bleed,
        "trim_w": w, "trim_h": h, "bleed": bleed, "safe": safe,
        "inset": bleed + safe,                 # page edge -> safe box
        "safe_w": w - 2 * safe, "safe_h": h - 2 * safe,
    }


def guides_html(g, proof):
    if not proof:
        return ""
    return f"""
    <div style="position:absolute;left:{g['bleed']}in;top:{g['bleed']}in;
      width:{g['trim_w']}in;height:{g['trim_h']}in;
      outline:0.5pt solid rgba(220,0,0,.7);"></div>
    <div style="position:absolute;left:{g['inset']}in;top:{g['inset']}in;
      width:{g['safe_w']}in;height:{g['safe_h']}in;
      outline:0.5pt dashed rgba(0,80,220,.7);"></div>"""


# ---------------------------------------------------------------- HTML builders
def page_shell(g, body, font, extra_css=""):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size:{g['page_w']}in {g['page_h']}in; margin:0; }}
html,body {{ margin:0; padding:0; }}
body {{ width:{g['page_w']}in; height:{g['page_h']}in; }}
.page {{ position:relative; width:{g['page_w']}in; height:{g['page_h']}in;
        overflow:hidden; background:#fff; }}
.safe {{ position:absolute; left:{g['inset']}in; top:{g['inset']}in;
        width:{g['safe_w']}in; height:{g['safe_h']}in; overflow:hidden;
        display:flex; align-items:center; justify-content:center; }}
#content {{ font-family:{font}; -webkit-font-smoothing:antialiased; }}
{extra_css}
</style></head><body>{body}</body></html>"""


def poem_html(poem, cfg, g, proof=False):
    pf = cfg["poem_face"]
    font = pf["body_font"]
    lh = pf.get("line_height", 1.35)
    align = pf.get("align", "center")
    title = (poem.get("title") or "").strip()
    author = (poem.get("author") or "").strip()
    text = poem.get("text") or ""
    parts = []
    if title:
        parts.append(f'<div class="title">{html.escape(title)}</div>')
    parts.append(f'<div class="poem">{html.escape(text.rstrip(chr(10)))}</div>')
    if author:
        parts.append(f'<div class="author">{html.escape(author)}</div>')
    content = f'<div id="content">{"".join(parts)}</div>'
    body = f'<div class="page"><div class="safe">{content}</div>{guides_html(g, proof)}</div>'
    extra = f"""
#content {{ text-align:{align}; line-height:{lh}; color:#111; }}
.title {{ font-size:0.92em; letter-spacing:0.06em; margin-bottom:0.20in; }}
.poem  {{ white-space:pre; }}
.author {{ font-style:italic; font-size:0.78em; margin-top:0.24in; }}
<!--fit-->"""
    js = f"""
<script>
(function(){{
  var MIN={pf['font_min_pt']}, MAX={pf['font_max_pt']};
  var safe=document.querySelector('.safe'), c=document.getElementById('content');
  var availH=safe.clientHeight, availW=safe.clientWidth, lo=MIN, hi=MAX;
  for(var i=0;i<32;i++){{
    var mid=(lo+hi)/2; c.style.fontSize=mid+'pt';
    if(c.scrollHeight<=availH && c.scrollWidth<=availW) lo=mid; else hi=mid;
  }}
  c.style.fontSize=lo+'pt';
  document.title='fit '+lo.toFixed(1)+'pt';
}})();
</script>"""
    return page_shell(g, body, font, extra) + js


def name_html(name, cfg, g, proof=False):
    """Place the guest name at a configurable corner, inset from the TRIM edge."""
    nf = cfg["name_face"]
    font = nf["font"]
    pt = nf.get("font_pt", 24)
    pos = str(nf.get("position", "bottom-left")).lower().strip()
    margin = float(nf.get("margin", nf.get("margin_from_top", 0.4)))
    inset = g["bleed"] + margin  # page edge -> name (trim edge + margin)

    if pos == "center":
        vert, horiz = "center", "center"
    else:
        parts = (pos.split("-") + ["", ""])[:2]
        vert = parts[0] if parts[0] in ("top", "center", "bottom") else "bottom"
        horiz = parts[1] if parts[1] in ("left", "center", "right") else "left"

    s = ["position:absolute"]
    if vert == "top":
        s.append(f"top:{inset}in")
    elif vert == "bottom":
        s.append(f"bottom:{inset}in")
    else:
        s.append("top:50%")
    if horiz == "left":
        s.append(f"left:{inset}in"); text_align = "left"
    elif horiz == "right":
        s.append(f"right:{inset}in"); text_align = "right"
    else:
        s.append("left:50%"); text_align = "center"
    tx = "-50%" if horiz == "center" else "0"
    ty = "-50%" if vert == "center" else "0"
    if (tx, ty) != ("0", "0"):
        s.append(f"transform:translate({tx},{ty})")
    s += [f"font-family:{font}", f"font-size:{pt}pt", "color:#111",
          f"text-align:{text_align}",
          "max-width:%.4fin" % (g["trim_w"] - 2 * margin)]

    body = (f'<div class="page">'
            f'<div class="name" style="{";".join(s)}">{html.escape(name)}</div>'
            f'{guides_html(g, proof)}</div>')
    return page_shell(g, body, font, "")


# ---------------------------------------------------------------- rendering
def render_pdf(html_str, out_pdf):
    os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
    tmp = out_pdf + ".html"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html_str)
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
           "--run-all-compositor-stages-before-draw", "--virtual-time-budget=3000",
           f"--print-to-pdf={out_pdf}", "file://" + os.path.abspath(tmp)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(out_pdf):
        sys.exit(f"Chrome failed to render {out_pdf}\n{r.stderr}")
    return tmp


def pdf_to_png(pdf, png_prefix, dpi=300):
    if not shutil.which("pdftoppm"):
        return None
    subprocess.run(["pdftoppm", "-png", "-r", str(dpi), "-singlefile",
                    pdf, png_prefix], capture_output=True)
    return png_prefix + ".png"


def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--poem", required=True)
    ap.add_argument("--name", default=None)
    ap.add_argument("--proof", action="store_true")
    ap.add_argument("--outdir", default=os.path.join(ROOT, "build", "faces"))
    args = ap.parse_args()

    cfg = load_config()
    g = geometry(cfg)
    poem = load_yaml(args.poem)
    pid = poem.get("id") or os.path.splitext(os.path.basename(args.poem))[0]

    # poem face
    pdf = os.path.join(args.outdir, f"{pid}.poem.pdf")
    render_pdf(poem_html(poem, cfg, g, proof=False), pdf)
    pdf_to_png(pdf, os.path.join(args.outdir, f"{pid}.poem"))
    print(f"poem face  -> {pdf}")
    if args.proof:
        proof_pdf = os.path.join(args.outdir, f"{pid}.poem.proof.pdf")
        render_pdf(poem_html(poem, cfg, g, proof=True), proof_pdf)
        pdf_to_png(proof_pdf, os.path.join(args.outdir, f"{pid}.poem.proof"))
        print(f"poem proof -> {proof_pdf}")

    # name face (optional)
    if args.name:
        s = slug(args.name)
        npdf = os.path.join(args.outdir, f"{pid}.name.{s}.pdf")
        render_pdf(name_html(args.name, cfg, g, proof=False), npdf)
        pdf_to_png(npdf, os.path.join(args.outdir, f"{pid}.name.{s}"))
        print(f"name face  -> {npdf}")
        if args.proof:
            nproof = os.path.join(args.outdir, f"{pid}.name.{s}.proof.pdf")
            render_pdf(name_html(args.name, cfg, g, proof=True), nproof)
            pdf_to_png(nproof, os.path.join(args.outdir, f"{pid}.name.{s}.proof"))
            print(f"name proof -> {nproof}")


if __name__ == "__main__":
    main()
