# render_structure.py
# Usage:
#   python render_structure.py
#   python render_structure.py docs/repo-structure.json docs/repo-structure.svg

import json, sys
from pathlib import Path
from xml.sax.saxutils import escape

# ------- Defaults (adjust if you prefer .JSON vs .json) -------
DEFAULT_IN  = Path("docs/repo-structure.json")
DEFAULT_OUT = Path("docs/repo-structure.svg")
# If you kept upper-case extension, set DEFAULT_IN = Path("docs/repo-structure.JSON")

# ------- Layout & styles -------
NODE_W   = 220
NODE_H   = 44
V_SP     = 16
INDENT   = 28
LEFT     = 40
TOP      = 100
RIGHT_PAD= 40
TITLE_H  = 60
NOTES_W  = 280  # room on the right for notes

COLORS = {
    "bg": "#ffffff",
    "stroke": "#0f172a",
    "text": "#0f172a",
    "muted": "#64748b",
    "folder": "#eef2ff",
    "file": "#f8fafc",
    "ignored": "#e2e8f0",
    "badge": "#1f2937",   # IGN badge
    "badgeText": "#ffffff"
}

def t(txt): return escape(str(txt))

def svg_rect(x,y,w,h,*,fill,stroke,rx=10,dash=None):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"{dash_attr}/>'


def svg_text(x,y,txt,*,size=14,weight=400,fill=None,anchor="start"):
    fill = fill or COLORS["text"]
    return (f'<text x="{x}" y="{y}" font-family="ui-sans-serif,system-ui,Segoe UI,Roboto,Arial" '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" '
            f'dominant-baseline="middle">{t(txt)}</text>')


def render_node(node, depth, x, y):
    """Return [elements], height_consumed"""
    typ  = node.get("type","folder")
    name = node.get("name","")
    note = node.get("note")

    if typ == "ignored":
        fill = COLORS["ignored"]; dash = "4 3"
    elif typ == "file":
        fill = COLORS["file"];    dash = None
    else:
        fill = COLORS["folder"];  dash = None

    nx = x + depth*INDENT
    el = [svg_rect(nx, y, NODE_W, NODE_H, fill=fill, stroke=COLORS["stroke"], rx=10, dash=dash),
          svg_text(nx+12, y+NODE_H/2, name, size=14, weight=600)]

    # Note text aligned in a separate right column
    if note:
        el.append(svg_text(nx + NODE_W + 12, y+NODE_H/2, note, size=12, fill=COLORS["muted"]))

    # Badge for ignored
    if typ == "ignored":
        bx = nx + NODE_W - 50
        by = y + 10
        el.append(f'<rect x="{bx}" y="{by}" width="44" height="18" rx="9" fill="{COLORS["badge"]}"/>')
        el.append(svg_text(bx+22, by+9, "IGN", size=11, weight=700, fill=COLORS["badgeText"], anchor="middle"))

    return el, NODE_H + V_SP


def measure(node):
    h = NODE_H + V_SP
    for ch in node.get("children", []):
        h += measure(ch)
    return h


def main():
    # Args
    in_path  = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT

    if not in_path.exists():
        # Help users who kept .JSON uppercase
        alt = in_path.with_suffix(".JSON")
        if alt.exists():
            in_path = alt
        else:
            raise FileNotFoundError(f"Input JSON not found: {in_path}")

    with in_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    total_h = TITLE_H + measure({"children": data.get("children", [])}) + 80
    total_w = LEFT + NODE_W + RIGHT_PAD + NOTES_W

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}" role="img">',
        f'<style>text{{dominant-baseline:middle}}</style>',
        f'<rect width="100%" height="100%" fill="{COLORS["bg"]}"/>',
        svg_text(total_w/2, 28, f'{data.get("name","")}: repository structure', size=20, weight=700, anchor="middle"),
        svg_text(total_w/2, 52, 'Folders, files, and ignored dirs', size=12, fill=COLORS["muted"], anchor="middle"),
    ]

    # Root label
    parts.append(svg_text(LEFT, TOP-28, f'{data.get("name","")}/', size=16, weight=700))

    # Rows
    y = TOP
    for ch in data.get("children", []):
        el, h = render_node(ch, 1, LEFT, y)
        parts.extend(el)
        y += h

    parts.append("</svg>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
