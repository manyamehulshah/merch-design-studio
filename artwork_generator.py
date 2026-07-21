"""
Stage 4: Designer
------------------
Turns a concept (palette + typography + motif) into actual vector artwork.
Fully procedural - svgwrite builds the SVG, cairosvg rasterizes it.
No diffusion model, no external API, unlimited free runs.
"""
import math
import os
import random

import cairosvg
import svgwrite
from PIL import ImageFont

SIZE = 1600
# Each font maps to a LIST of candidate paths, tried in order - font package
# layouts differ across distros/versions (e.g. Ubuntu ships
# fonts-roboto-hinted at .../roboto/hinted/..., Debian trixie only has
# fonts-roboto-unhinted at .../roboto/unhinted/RobotoTTF/...), so a single
# hardcoded path breaks portability. First existing path wins.
FONT_FILES = {
    "Bebas Neue": ["/usr/share/fonts/opentype/bebas-neue/BebasNeue-Bold.otf"],
    "Inter": ["/usr/share/fonts/opentype/inter/Inter-Regular.otf"],
    "GFS Baskerville": ["/usr/share/fonts/truetype/baskerville/GFSBaskerville.otf"],
    "Lora": ["/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf",
             "/usr/share/fonts/truetype/lora/Lora-Regular.ttf"],
    "Montserrat": ["/usr/share/fonts/truetype/montserrat/Montserrat-SemiBold.ttf",
                   "/usr/share/fonts/opentype/montserrat/Montserrat-SemiBold.otf"],
    "Open Sans": ["/usr/share/fonts/truetype/open-sans/OpenSans-Regular.ttf"],
    "Dancing Script": ["/usr/share/fonts/opentype/dancingscript/DancingScript-Bold.otf"],
    "Quicksand": ["/usr/share/fonts/truetype/quicksand/Quicksand-Regular.ttf"],
    "Roboto Slab": ["/usr/share/fonts/opentype/roboto/slab/RobotoSlab-Bold.otf",
                     "/usr/share/fonts/truetype/roboto/slab/RobotoSlab-Bold.ttf"],
    "Roboto": ["/usr/share/fonts/truetype/roboto/hinted/Roboto-Regular.ttf",
               "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Regular.ttf",
               "/usr/share/fonts/truetype/roboto-unhinted/Roboto-Regular.ttf"],
    "Poppins": ["/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
                "/usr/share/fonts/truetype/poppins/Poppins-Bold.ttf"],
}


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    r, g, b = rgb
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(c1, c2):
    l1, l2 = luminance(hex_to_rgb(c1)), luminance(hex_to_rgb(c2))
    l1, l2 = max(l1, l2), min(l1, l2)
    return (l1 + 0.05) / (l2 + 0.05)


def assign_roles(colors):
    bg = colors[0]
    others = colors[1:]
    ink = max(others, key=lambda c: contrast(bg, c))
    remaining = [c for c in others if c != ink]
    accent1 = remaining[0] if remaining else ink
    accent2 = remaining[1] if len(remaining) > 1 else accent1
    accent3 = remaining[2] if len(remaining) > 2 else accent2
    return {"bg": bg, "ink": ink, "accent1": accent1, "accent2": accent2, "accent3": accent3}


_FONT_PATH_CACHE = {}


def _first_existing(paths):
    return next((p for p in paths if p and os.path.exists(p)), None)


def _find_by_filename_glob(font_family):
    """Last-ditch search: walk common font roots for anything whose
    filename loosely matches the family name, in case the package layout
    doesn't match any hardcoded candidate at all."""
    import glob
    slug = font_family.replace(" ", "")
    for root in ("/usr/share/fonts", "/usr/local/share/fonts"):
        for ext in ("ttf", "otf"):
            matches = glob.glob(f"{root}/**/*{slug}*.{ext}", recursive=True)
            if matches:
                return sorted(matches)[0]
    return None


def _resolve_font_path(font_family):
    """Falls back gracefully if a font package didn't land at the expected
    path on this OS/container (e.g. a different Linux distro's font
    packaging layout) - avoids hard-crashing the whole render."""
    if font_family in _FONT_PATH_CACHE:
        return _FONT_PATH_CACHE[font_family]

    candidates = FONT_FILES.get(font_family, [])
    resolved = (
        _first_existing(candidates)
        or _find_by_filename_glob(font_family)
        or _first_existing(FONT_FILES.get("Inter", []))
        or _first_existing(FONT_FILES.get("Roboto", []))
        or _first_existing([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ])
    )
    if not resolved:
        raise FileNotFoundError(
            f"No usable font file found for '{font_family}' and no fallback "
            f"font was present either. Check packages.txt installed correctly.")
    _FONT_PATH_CACHE[font_family] = resolved
    return resolved


def fit_font_size(text, font_family, max_width, start_size=180, min_size=36):
    path = _resolve_font_path(font_family)
    size = start_size
    while size > min_size:
        font = ImageFont.truetype(path, size)
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            return size
        size -= 4
    return min_size


def blob_path(cx, cy, base_r, points=10, variance=0.28, seed=None):
    rng = random.Random(seed)
    pts = []
    for i in range(points):
        angle = (2 * math.pi / points) * i
        r = base_r * (1 + rng.uniform(-variance, variance))
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    d = f"M {pts[0][0]:.1f},{pts[0][1]:.1f} "
    n = len(pts)
    for i in range(n):
        p0, p1 = pts[i], pts[(i + 1) % n]
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        d += f"Q {p0[0]:.1f},{p0[1]:.1f} {mid[0]:.1f},{mid[1]:.1f} "
    return d + "Z"


def star_path(cx, cy, r_outer, r_inner, points=8, rotation=0.0):
    pts = []
    for i in range(points * 2):
        r = r_outer if i % 2 == 0 else r_inner
        angle = (math.pi / points) * i + rotation
        pts.append((cx + r * math.sin(angle), cy - r * math.cos(angle)))
    d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
    return d


def leaf_path(x, y, length, width, angle_deg):
    a = math.radians(angle_deg)
    ex, ey = x + length * math.cos(a), y - length * math.sin(a)
    px, py = -math.sin(a) * width, -math.cos(a) * width
    mx, my = (x + ex) / 2, (y + ey) / 2
    c1 = (mx + px, my + py)
    c2 = (mx - px, my - py)
    return f"M {x:.1f},{y:.1f} Q {c1[0]:.1f},{c1[1]:.1f} {ex:.1f},{ey:.1f} Q {c2[0]:.1f},{c2[1]:.1f} {x:.1f},{y:.1f} Z"


def add_text(dwg, x, y, text, font_family, size, fill, anchor="middle", letter_spacing=None, weight="normal"):
    kwargs = dict(insert=(x, y), text_anchor=anchor, font_family=font_family,
                  font_size=size, fill=fill, font_weight=weight)
    if letter_spacing:
        kwargs["letter_spacing"] = letter_spacing
    dwg.add(dwg.text(text, **kwargs))


def motif_emblem_badge(dwg, roles, brand_name, tagline, seed, transparent):
    cx, cy = SIZE / 2, SIZE / 2
    if not transparent:
        dwg.add(dwg.rect((0, 0), (SIZE, SIZE), fill=roles["bg"]))
    dwg.add(dwg.circle((cx, cy), r=560, fill="none", stroke=roles["ink"], stroke_width=6))
    dwg.add(dwg.circle((cx, cy), r=520, fill="none", stroke=roles["accent1"], stroke_width=2))
    for i in range(36):
        angle = (2 * math.pi / 36) * i
        r1, r2 = 560, 585
        x1, y1 = cx + r1 * math.cos(angle), cy + r1 * math.sin(angle)
        x2, y2 = cx + r2 * math.cos(angle), cy + r2 * math.sin(angle)
        dwg.add(dwg.line((x1, y1), (x2, y2), stroke=roles["ink"], stroke_width=4))
    dwg.add(dwg.path(d=star_path(cx, cy - 330, 46, 20, points=5), fill=roles["accent1"]))
    return {"text_y": cy - 20, "text_size": None, "tagline_y": cy + 70, "cx": cx}


def motif_geo_grid(dwg, roles, brand_name, tagline, seed, transparent):
    rng = random.Random(seed)
    if not transparent:
        dwg.add(dwg.rect((0, 0), (SIZE, SIZE), fill=roles["bg"]))
    cols = 6
    cell = SIZE / cols
    palette_cycle = [roles["accent1"], roles["accent2"], roles["accent3"], roles["ink"]]
    for r in range(cols):
        for c in range(cols):
            if rng.random() > 0.55:
                continue
            x, y = c * cell, r * cell
            color = rng.choice(palette_cycle)
            shape = rng.choice(["circle", "square", "triangle"])
            op = rng.uniform(0.35, 0.85)
            if shape == "circle":
                dwg.add(dwg.circle((x + cell / 2, y + cell / 2), r=cell * 0.32, fill=color, opacity=op))
            elif shape == "square":
                s = cell * 0.55
                dwg.add(dwg.rect((x + (cell - s) / 2, y + (cell - s) / 2), (s, s), fill=color, opacity=op))
            else:
                s = cell * 0.6
                x0, y0 = x + cell / 2, y + (cell - s) / 2
                pts = [(x0, y0), (x0 - s / 2, y0 + s), (x0 + s / 2, y0 + s)]
                dwg.add(dwg.polygon(pts, fill=color, opacity=op))
    band_h = 300
    band_y = SIZE / 2 - band_h / 2
    if transparent:
        dwg.add(dwg.rect((0, band_y), (SIZE, band_h), fill=roles["bg"]))
    else:
        dwg.add(dwg.rect((0, band_y), (SIZE, band_h), fill=roles["bg"], opacity=0.92))
    return {"text_y": SIZE / 2 + 10, "text_size": None, "tagline_y": SIZE / 2 + 90, "cx": SIZE / 2}


def motif_organic_blob(dwg, roles, brand_name, tagline, seed, transparent):
    cx, cy = SIZE / 2, SIZE / 2
    if not transparent:
        dwg.add(dwg.rect((0, 0), (SIZE, SIZE), fill=roles["bg"]))
    dwg.add(dwg.path(d=blob_path(cx - 120, cy - 60, 480, points=9, seed=seed), fill=roles["accent1"], opacity=0.55))
    dwg.add(dwg.path(d=blob_path(cx + 150, cy + 120, 380, points=8, seed=(seed or 0) + 1), fill=roles["accent2"], opacity=0.5))
    dwg.add(dwg.path(d=blob_path(cx, cy, 260, points=7, seed=(seed or 0) + 2), fill=roles["accent3"], opacity=0.65))
    return {"text_y": cy, "text_size": None, "tagline_y": cy + 80, "cx": cx}


def motif_botanical_line(dwg, roles, brand_name, tagline, seed, transparent):
    cx, cy = SIZE / 2, SIZE / 2
    if not transparent:
        dwg.add(dwg.rect((0, 0), (SIZE, SIZE), fill=roles["bg"]))
    rng = random.Random(seed)
    for side in (-1, 1):
        stem_x = cx + side * 480
        wobble = 18 * side
        dwg.add(dwg.path(
            d=f"M {stem_x},{cy - 400} C {stem_x + wobble},{cy - 130} {stem_x - wobble},{cy + 130} {stem_x},{cy + 400}",
            fill="none", stroke=roles["ink"], stroke_width=3, opacity=0.8))
        n_leaves = 6
        for i in range(n_leaves):
            t = i / (n_leaves - 1)
            y = cy - 360 + t * 720
            x = stem_x + math.sin(t * math.pi) * wobble
            base_ang = 32 if side < 0 else 148
            ang = base_ang + rng.uniform(-14, 14)
            length = rng.uniform(70, 130)
            width = rng.uniform(26, 46)
            fill_color = roles["accent1"] if i % 2 == 0 else roles["accent2"]
            dwg.add(dwg.path(d=leaf_path(x, y, length, width, ang),
                              fill=fill_color, opacity=0.75,
                              stroke=roles["ink"], stroke_width=1.5))
    dwg.add(dwg.circle((cx, cy), r=430, fill="none", stroke=roles["ink"], stroke_width=2, opacity=0.5))
    return {"text_y": cy, "text_size": None, "tagline_y": cy + 90, "cx": cx}


def motif_retro_sunburst(dwg, roles, brand_name, tagline, seed, transparent):
    cx, cy = SIZE / 2, SIZE / 2
    if not transparent:
        dwg.add(dwg.rect((0, 0), (SIZE, SIZE), fill=roles["bg"]))
    rays = 24
    for i in range(rays):
        a0 = (2 * math.pi / rays) * i
        a1 = a0 + (2 * math.pi / rays) / 2
        color = roles["accent1"] if i % 2 == 0 else roles["accent2"]
        r = 760
        pts = [(cx, cy),
               (cx + r * math.cos(a0), cy + r * math.sin(a0)),
               (cx + r * math.cos(a1), cy + r * math.sin(a1))]
        dwg.add(dwg.polygon(pts, fill=color, opacity=0.9))
    dwg.add(dwg.circle((cx, cy), r=380, fill=roles["bg"]))
    dwg.add(dwg.circle((cx, cy), r=380, fill="none", stroke=roles["ink"], stroke_width=5))
    return {"text_y": cy, "text_size": None, "tagline_y": cy + 80, "cx": cx}


def motif_halftone_pop(dwg, roles, brand_name, tagline, seed, transparent):
    cx, cy = SIZE / 2, SIZE / 2
    if not transparent:
        dwg.add(dwg.rect((0, 0), (SIZE, SIZE), fill=roles["bg"]))
    dwg.add(dwg.path(d=star_path(cx, cy, 620, 460, points=14, rotation=0.15), fill=roles["accent1"]))
    step = 70
    for gy in range(0, SIZE, step):
        for gx in range(0, SIZE, step):
            d = math.hypot(gx - cx, gy - cy)
            rr = max(2, 22 - d / 55)
            if rr > 2:
                dwg.add(dwg.circle((gx, gy), r=rr, fill=roles["ink"], opacity=0.5))
    dwg.add(dwg.circle((cx, cy), r=420, fill=roles["bg"]))
    dwg.add(dwg.circle((cx, cy), r=420, fill="none", stroke=roles["ink"], stroke_width=6))
    return {"text_y": cy, "text_size": None, "tagline_y": cy + 80, "cx": cx}


MOTIF_RENDERERS = {
    "emblem_badge": motif_emblem_badge,
    "geo_grid": motif_geo_grid,
    "organic_blob": motif_organic_blob,
    "botanical_line": motif_botanical_line,
    "retro_sunburst": motif_retro_sunburst,
    "halftone_pop": motif_halftone_pop,
}


def render_concept(concept: dict, out_dir: str, seed: int = None, tagline: str = None):
    os.makedirs(out_dir, exist_ok=True)
    palette = concept["palette"]
    typography = concept["typography"]
    motif_id = concept["motif"]["id"]
    roles = assign_roles(palette["colors"])
    brand_name = concept["name"]
    tagline = tagline or "SMALL BATCH • EST. 2026"
    heading_font = typography["heading_font"]
    body_font = typography["body_font"]
    renderer = MOTIF_RENDERERS[motif_id]

    script_fonts = {"Dancing Script"}
    display_name = brand_name if heading_font in script_fonts else brand_name.upper()

    paths = {}
    for variant, transparent in (("poster", False), ("print", True)):
        dwg = svgwrite.Drawing(size=(SIZE, SIZE))
        layout = renderer(dwg, roles, brand_name, tagline, seed, transparent)
        max_w = SIZE * 0.62
        fsize = fit_font_size(display_name, heading_font, max_w, start_size=170, min_size=48)
        add_text(dwg, layout["cx"], layout["text_y"] + fsize * 0.32, display_name,
                  heading_font, fsize, roles["ink"], weight="bold")
        add_text(dwg, layout["cx"], layout["tagline_y"], tagline, body_font, 30,
                  roles["ink"], letter_spacing="4px")

        svg_path = os.path.join(out_dir, f"{concept['id']}_{variant}.svg")
        png_path = os.path.join(out_dir, f"{concept['id']}_{variant}.png")
        dwg.saveas(svg_path)
        cairosvg.svg2png(url=svg_path, write_to=png_path,
                          output_width=SIZE, output_height=SIZE,
                          background_color=None if transparent else roles["bg"])
        paths[variant] = png_path
    return paths
