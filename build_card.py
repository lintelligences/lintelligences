"""Builds the images for the GitHub profile README:

  panel-*.svg   the info panel (one accent colour, plain text)
  links/*.svg   one clickable button per link
  (each image comes in -light and -dark versions)
  README.md     the page that stacks them

Edit profile.toml, then run:  python3 build_card.py
(It also writes README.md, so edit profile.toml rather than the README.)
The binary portrait is separate now: see build_portrait.py.
"""
import html
import re

PANEL_FILE, LINK_DIR = "panel", "links"   # + "-light.svg" / "-dark.svg"

W = 985                       # every image shares this width so they stack cleanly
ART_X = 15                    # left margin

# ---- the info panel: the words live in profile.toml
PROFILE_FILE = "profile.toml"
README_FILE = "README.md"
# Each image is built twice; the README shows the one matching the visitor's GitHub theme.
# ink = text, outlines and the 0s/1s; the accent colours come from profile.toml.
THEMES = {
    "light": dict(ink="#1f2328", accent_key="accent", accent_default="#1a7f37"),
    "dark":  dict(ink="#e6edf3", accent_key="accent_dark", accent_default="#3fb950"),
}
INK = THEMES["light"]["ink"]  # current theme's ink (set by use_theme)
SUFFIX = "light"


def use_theme(name, p):
    """Point the builders at one theme's colours and file names."""
    global INK, SUFFIX
    t = THEMES[name]
    INK, SUFFIX = t["ink"], name
    p["accent"] = p.get(t["accent_key"], t["accent_default"])


def out_name(stem):
    return f"{stem}-{SUFFIX}.svg"

# ---- build ----------------------------------------------------------------------
FONT_FACE = """@font-face {
src: local('Consolas'), local('Consolas Bold');
font-family: 'ConsolasFallback';
font-display: swap;
-webkit-size-adjust: 109%;
size-adjust: 109%;
}"""
FONTS = "ConsolasFallback,Consolas,Menlo,'DejaVu Sans Mono',monospace"


def svg_doc(width, height, style, body):
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="{FONTS}" width="{width}px" height="{height}px">
<style>
{FONT_FACE}
text, tspan {{white-space: pre;}}
{style}
</style>
{body}
</svg>
"""


# ---- info panel -------------------------------------------------------------------
def load_profile():
    import tomllib
    try:
        with open(PROFILE_FILE, "rb") as f:
            p = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise SystemExit(f"\n{PROFILE_FILE} has a formatting problem: {e}\n"
                         "Common causes: a missing quote or comma, or a top-level line "
                         "(name, role, ...) placed below a [[column]] or [[link]] block.")
    p.setdefault("column", [])
    p.setdefault("link", [])
    return p


def wrap(text, width):
    """textwrap that also honours explicit \n line breaks."""
    import textwrap
    out = []
    for para in str(text).split("\n"):
        out += textwrap.wrap(para, width) or [""]
    return out


def build_panel(p):
    x = ART_X + 2
    P_SIZE, P_LH, P_CHAR = 15, 22, 9.05
    full_chars = int((W - 2 * x) / P_CHAR)
    esc = lambda t: html.escape(t, quote=False)
    accent = p["accent"]

    out, y = [], 46
    if p.get("name"):
        out.append(f'<text x="{x}" y="{y}" class="name">{esc(p["name"])}</text>')
        y += 32
    for key in ("role", "degrees"):
        if p.get(key):
            for line in wrap(p[key], full_chars):
                out.append(f'<text x="{x}" y="{y}" class="body">{esc(line)}</text>')
                y += P_LH
    if p.get("intro"):
        y += 14
        for line in wrap(p["intro"], full_chars):
            out.append(f'<text x="{x}" y="{y}" class="body">{esc(line)}</text>')
            y += P_LH

    cols = p["column"]
    if cols:
        y += 14
        out.append(f'<rect x="{x}" y="{y}" width="56" height="3" class="accent"/>')
        y += 40
        col_w = (W - 2 * x) / len(cols)
        wrap_chars = int((col_w - 30) / P_CHAR)
        col_bottom = y
        for i, col in enumerate(cols):
            cx, cy = x + i * col_w, y
            if col.get("title"):
                out.append(f'<text x="{cx}" y="{cy}" class="label">{esc(col["title"].upper())}</text>')
                cy += 30
            for item in col.get("items", []):
                for j, line in enumerate(wrap(item, wrap_chars)):
                    mark = '<tspan class="accent">› </tspan>' if j == 0 else "  "
                    out.append(f'<text x="{cx}" y="{cy}" class="body">{mark}{esc(line)}</text>')
                    cy += P_LH
                cy += 8
            col_bottom = max(col_bottom, cy)
        y = col_bottom - 8

    if p.get("invite"):
        # Bold, accent-coloured, typed out on page load: a clip window widens one
        # character at a time with a cursor riding its edge, then the cursor blinks.
        I_SIZE = P_SIZE + 5                        # invite font size (px)
        I_CHAR = I_SIZE * 0.6033                   # monospace glyph width at that size
        I_LH = I_SIZE + 9                          # line height if the invite wraps
        y += 20 + I_SIZE // 2
        t, TYPE = 0.8, 0.045                       # start delay, seconds per character
        lines = wrap(p["invite"], int((W - 2 * x) / I_CHAR) - 2)
        for j, line in enumerate(lines):
            text = ("→ " if j == 0 else "  ") + line
            xs = [x + k * I_CHAR for k in range(len(text) + 1)]
            steps = ";".join(f"{v - x:.1f}" for v in xs)
            dur = len(text) * TYPE
            out.append(
                f'<clipPath id="type{j}"><rect x="{x}" y="{y - I_SIZE * 1.2:.0f}" width="0" height="{I_SIZE * 1.6:.0f}">'
                f'<animate attributeName="width" values="{steps}" calcMode="discrete" '
                f'begin="{t:.2f}s" dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>'
                f'<text x="{x}" y="{y}" class="invite" clip-path="url(#type{j})">{esc(text)}</text>')
            last = j == len(lines) - 1
            cursor_x = ";".join(f"{v:.1f}" for v in xs)
            out.append(
                f'<rect x="{x}" y="{y - I_SIZE * 0.9:.0f}" width="{I_CHAR * 0.9:.1f}" height="{I_SIZE * 1.1:.0f}" class="accent" opacity="0">'
                f'<set attributeName="opacity" to="1" begin="{t:.2f}s"'
                f'{"" if last else f" end={chr(34)}{t + dur:.2f}s{chr(34)}"}/>'
                f'<animate attributeName="x" values="{cursor_x}" calcMode="discrete" '
                f'begin="{t:.2f}s" dur="{dur:.2f}s" fill="freeze"/>'
                + (f'<animate attributeName="fill-opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" '
                   f'dur="1.06s" begin="{t + dur:.2f}s" repeatCount="indefinite"/>' if last else "")
                + '</rect>')
            t += dur + 0.15
            y += I_LH
    height = y + 4

    style = f""".name {{fill: {INK}; font-size: 30px; font-weight: bold;}}
.body {{fill: {INK}; font-size: {P_SIZE}px;}}
.label {{fill: {accent}; font-size: 13px; font-weight: bold; letter-spacing: 2px;}}
.accent {{fill: {accent};}}
.invite {{fill: {accent}; font-size: {P_SIZE + 5}px; font-weight: bold;}}"""
    open(out_name(PANEL_FILE), "w").write(svg_doc(W, height, style, "\n".join(out)))
    print(f"wrote {out_name(PANEL_FILE)}: {W}x{height}")


def build_links(p):
    import os, glob
    os.makedirs(LINK_DIR, exist_ok=True)
    files = []
    # Original size and weight; all buttons share one width (a quarter of the page
    # with gaps), so a row of four spans the panel edge to edge and scales with it.
    B_SIZE, B_H, GAP = 15, 40, 16
    b_char = B_SIZE * 0.6033
    n = max(len(p["link"]), 1)
    per_row = 4 if n <= 4 else n
    btn_w = int((W - GAP * (per_row - 1)) / per_row)
    for link in p["link"]:
        text = f'{link["label"]} ↗'
        w = max(btn_w, int(len(text) * b_char + 36))
        body = (f'<rect x="1" y="1" width="{w - 2}" height="{B_H - 2}" rx="{(B_H - 2) / 2}" fill="none" '
                f'stroke="{INK}" stroke-width="1.5"/>'
                f'<text x="{w / 2}" y="{B_H / 2 + B_SIZE * 0.36:.1f}" text-anchor="middle" font-size="{B_SIZE}px" '
                f'fill="{INK}" font-weight="bold">{html.escape(text, quote=False)}</text>')
        name = f"{LINK_DIR}/" + out_name(re.sub(r'[^a-z0-9]+', '-', link['label'].lower()).strip('-'))
        open(name, "w").write(svg_doc(w, B_H, "", body))
        files.append((name, link["url"], link["label"]))
    print("wrote", ", ".join(f[0] for f in files) or "no link buttons")
    return files


def picture(stem, alt, size_attr):
    """<picture> that swaps light/dark with the visitor's GitHub theme."""
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{stem}-dark.svg">'
            f'<img src="{stem}-light.svg" {size_attr} alt="{alt}"></picture>')


STUB_DIR = "stubs"


def build_stubs(p):
    """Links with an empty url get a small page in stubs/ instead of a 404.
    Also warns about urls that GitHub would treat as files in this repo."""
    import os, glob
    os.makedirs(STUB_DIR, exist_ok=True)
    for old in glob.glob(f"{STUB_DIR}/*.md"):
        os.remove(old)
    for link in p["link"]:
        url = link.get("url", "").strip()
        if not url:
            slug = re.sub(r"[^a-z0-9]+", "-", link["label"].lower()).strip("-")
            message = link.get("stub", "This page is on its way. Check back soon.")
            name = p.get("name", "")
            back = f"Back to {name}'s profile" if name else "Back to the profile"
            open(f"{STUB_DIR}/{slug}.md", "w").write(
                f"## {link['label']}\n\n{message}\n\n[← {back}](../README.md)\n")
            link["url"] = f"{STUB_DIR}/{slug}.md"
            print(f"stub page for {link['label']!r}: {link['url']}")
        elif not re.match(r"^(https?://|mailto:)", url):
            print(f"WARNING: the {link['label']!r} url ({url}) doesn't start with https:// "
                  "or mailto:, so GitHub will look for it as a file in this repo.")


def build_readme(p, links):
    """README.md is generated too, so the alt text and link URLs always match profile.toml."""
    a = lambda t: html.escape(str(t).replace("\n", " "), quote=True)
    summary = ". ".join(v for v in (p.get("name"), p.get("role"), p.get("degrees"), p.get("intro")) if v)
    for col in p["column"]:
        summary += f' {col.get("title", "")}: ' + "; ".join(i.replace("\n", " ") for i in col.get("items", [])) + "."
    lines = [
        "<!-- Generated by build_card.py from profile.toml: edit that file, not this one. -->",
        '<p align="center">',
        "  " + picture(PANEL_FILE, a(summary), 'width="100%"'),
        "</p>",
    ]
    if links:
        lines += ["", "<p>"]
        pct = 100 / max(len(links), 4) - 1          # each button's share of the row
        lines += [f'  <a href="{a(url)}">' + picture(name.rsplit("-light.svg", 1)[0], a(label), f'width="{pct:.0f}%"') + "</a>"
                  for name, url, label in links]
        lines += ["</p>"]
    open(README_FILE, "w").write("\n".join(lines) + "\n")
    print(f"wrote {README_FILE}")


if __name__ == "__main__":
    import glob, os
    profile = load_profile()
    # clear old builds (leaves the portrait-*.svg files from build_portrait.py alone)
    for old in glob.glob(f"{PANEL_FILE}-*.svg") + glob.glob("header-*.svg") + glob.glob(f"{LINK_DIR}/*.svg"):
        os.remove(old)
    build_stubs(profile)
    links = {}
    for theme in THEMES:
        use_theme(theme, profile)
        build_panel(profile)
        links[theme] = build_links(profile)
    build_readme(profile, links["light"])