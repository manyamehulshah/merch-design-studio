"""
Flat-illustration product templates, drawn procedurally with PIL - no
stock photos needed. Each render_* function returns (RGBA image, print_area).
"""
from PIL import Image, ImageDraw

CANVAS = 1600


def _new_canvas(bg=(255, 255, 255, 0)):
    return Image.new("RGBA", (CANVAS, CANVAS), bg)


def _shade(hex_color, factor):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if factor <= 1:
        r, g, b = r * factor, g * factor, b * factor
    else:
        r = r + (255 - r) * (factor - 1)
        g = g + (255 - g) * (factor - 1)
        b = b + (255 - b) * (factor - 1)
    return (int(max(0, min(255, r))), int(max(0, min(255, g))), int(max(0, min(255, b))), 255)


def render_tshirt(garment_hex="#F2F0EA"):
    img = _new_canvas()
    d = ImageDraw.Draw(img, "RGBA")
    base = _shade(garment_hex, 1.0)
    shadow = _shade(garment_hex, 0.85)
    highlight = _shade(garment_hex, 1.12)
    cx = CANVAS / 2

    body_top, body_bottom = 560, 1430
    body_left, body_right = 520, 1080
    shoulder_l, shoulder_r = cx - 150, cx + 150
    neck_w = 90
    sleeve_tip_l, sleeve_tip_r = 340, 1260

    pts = [
        (shoulder_l, body_top), (sleeve_tip_l, body_top + 60),
        (sleeve_tip_l + 90, body_top + 190), (body_left, body_top + 140),
        (body_left, body_bottom), (body_right, body_bottom),
        (body_right, body_top + 140), (sleeve_tip_r - 90, body_top + 190),
        (sleeve_tip_r, body_top + 60), (shoulder_r, body_top),
        (cx + neck_w, body_top - 20), (cx, body_top + 40), (cx - neck_w, body_top - 20),
    ]
    d.polygon(pts, fill=base, outline=_shade(garment_hex, 0.65))
    d.arc([cx - neck_w, body_top - 55, cx + neck_w, body_top + 55], start=20, end=160,
          fill=_shade(garment_hex, 0.7), width=8)
    d.polygon([(body_left + 20, body_top + 160), (body_left + 110, body_top + 160),
                (body_left + 70, body_bottom - 30), (body_left + 20, body_bottom - 30)],
               fill=(*shadow[:3], 55))
    d.polygon([(body_right - 110, body_top + 160), (body_right - 20, body_top + 160),
                (body_right - 20, body_bottom - 30), (body_right - 60, body_bottom - 30)],
               fill=(*highlight[:3], 45))

    print_area = (cx - 260, body_top + 190, cx + 260, body_top + 690)
    return img, print_area


def render_hoodie(garment_hex="#3C3C3C"):
    img = _new_canvas()
    d = ImageDraw.Draw(img, "RGBA")
    base = _shade(garment_hex, 1.0)
    cx = CANVAS / 2
    body_top, body_bottom = 620, 1450
    body_left, body_right = 500, 1100
    shoulder_l, shoulder_r = cx - 180, cx + 180
    sleeve_tip_l, sleeve_tip_r = 300, 1300

    # hood drawn first, BEHIND the body, so only the top lobe peeks out
    d.ellipse([cx - 165, body_top - 150, cx + 165, body_top + 110], fill=_shade(garment_hex, 0.85),
               outline=_shade(garment_hex, 0.55))
    d.ellipse([cx - 100, body_top - 60, cx + 100, body_top + 90], fill=_shade(garment_hex, 0.65))

    pts = [
        (shoulder_l, body_top), (sleeve_tip_l, body_top + 80),
        (sleeve_tip_l + 100, body_top + 220), (body_left, body_top + 170),
        (body_left, body_bottom), (body_right, body_bottom),
        (body_right, body_top + 170), (sleeve_tip_r - 100, body_top + 220),
        (sleeve_tip_r, body_top + 80), (shoulder_r, body_top),
    ]
    d.polygon(pts, fill=base, outline=_shade(garment_hex, 0.6))
    # pocket
    d.rounded_rectangle([cx - 170, body_top + 480, cx + 170, body_top + 620], radius=20,
                          outline=_shade(garment_hex, 0.55), width=4)
    # drawstrings
    d.line([(cx - 40, body_top + 90), (cx - 55, body_top + 250)], fill=_shade(garment_hex, 0.4), width=6)
    d.line([(cx + 40, body_top + 90), (cx + 55, body_top + 250)], fill=_shade(garment_hex, 0.4), width=6)

    print_area = (cx - 250, body_top + 250, cx + 250, body_top + 700)
    return img, print_area


def render_mug(garment_hex="#FFFFFF"):
    img = _new_canvas()
    d = ImageDraw.Draw(img, "RGBA")
    base = _shade(garment_hex, 1.0)
    cx = CANVAS / 2
    top, bottom = 520, 1180
    left, right = 560, 1040

    d.rounded_rectangle([left, top, right, bottom], radius=24, fill=base, outline=_shade(garment_hex, 0.75))
    d.ellipse([left, top - 40, right, top + 40], fill=_shade(garment_hex, 1.08), outline=_shade(garment_hex, 0.75))
    d.ellipse([left + 14, top - 26, right - 14, top + 26], fill=_shade(garment_hex, 0.9))
    d.arc([right - 40, top + 120, right + 220, bottom - 120], start=280, end=80, fill=_shade(garment_hex, 0.85), width=46)
    d.rectangle([left, top + 20, left + 40, bottom], fill=(*_shade(garment_hex, 0.85)[:3], 90))
    d.rectangle([right - 50, top + 20, right, bottom], fill=(*_shade(garment_hex, 1.15)[:3], 60))

    print_area = (left + 90, top + 90, right - 90, top + 470)
    return img, print_area


def render_tote(garment_hex="#E8E2D5"):
    img = _new_canvas()
    d = ImageDraw.Draw(img, "RGBA")
    base = _shade(garment_hex, 1.0)
    cx = CANVAS / 2
    top, bottom = 560, 1400
    left, right = 480, 1120

    d.rounded_rectangle([left, top, right, bottom], radius=18, fill=base, outline=_shade(garment_hex, 0.7))
    for gx in (left + 60, right - 60):
        d.line([(gx, top), (gx, bottom)], fill=(*_shade(garment_hex, 0.8)[:3], 120), width=4)
    strap_w = 46
    d.arc([cx - 260, top - 260, cx - 260 + 200, top + 60], start=180, end=360, fill=_shade(garment_hex, 0.65), width=strap_w // 2)
    d.arc([cx + 60, top - 260, cx + 260, top + 60], start=180, end=360, fill=_shade(garment_hex, 0.65), width=strap_w // 2)

    print_area = (left + 100, top + 120, right - 100, top + 560)
    return img, print_area


def render_cap(garment_hex="#1A1A1A"):
    img = _new_canvas()
    d = ImageDraw.Draw(img, "RGBA")
    base = _shade(garment_hex, 1.0)
    cx = CANVAS / 2
    cy = 780
    r = 300

    # crown: clean upper-half dome (angles 180->360 sweep through the top point)
    d.pieslice([cx - r, cy - r, cx + r, cy + r], start=180, end=360, fill=base,
                outline=_shade(garment_hex, 0.55), width=3)
    # brim: flattened lower-half ellipse jutting out beneath the dome
    brim_top = cy - 10
    d.pieslice([cx - r - 40, brim_top, cx + r + 40, brim_top + 170], start=0, end=180,
                fill=_shade(garment_hex, 0.8), outline=_shade(garment_hex, 0.55), width=3)
    # button + radial seams on the crown
    d.ellipse([cx - 12, cy - r - 4, cx + 12, cy - r + 20], fill=_shade(garment_hex, 0.6))
    for frac in (-0.7, -0.35, 0, 0.35, 0.7):
        d.line([(cx, cy - r + 10), (cx + r * frac, cy - 6)], fill=_shade(garment_hex, 0.65), width=3)

    print_area = (cx - r * 0.62, cy - r * 0.72, cx + r * 0.62, cy - 30)
    return img, print_area


def render_bottle(garment_hex="#DCE7E8"):
    img = _new_canvas()
    d = ImageDraw.Draw(img, "RGBA")
    base = _shade(garment_hex, 1.0)
    cx = CANVAS / 2
    top, bottom = 380, 1420
    left, right = 640, 960

    # cap
    d.rounded_rectangle([cx - 60, top - 90, cx + 60, top + 10], radius=10, fill=_shade(garment_hex, 0.6))
    # neck
    d.rounded_rectangle([cx - 70, top, cx + 70, top + 120], radius=14, fill=base, outline=_shade(garment_hex, 0.65))
    # body
    d.rounded_rectangle([left, top + 100, right, bottom], radius=60, fill=base, outline=_shade(garment_hex, 0.65))
    d.rectangle([left, top + 60, right, top + 160], fill=(*_shade(garment_hex, 0.7)[:3], 255))
    # shading
    d.rectangle([left, top + 160, left + 40, bottom], fill=(*_shade(garment_hex, 0.85)[:3], 90))
    d.rectangle([right - 50, top + 160, right, bottom], fill=(*_shade(garment_hex, 1.15)[:3], 70))

    print_area = (left + 60, top + 260, right - 60, top + 760)
    return img, print_area


def render_notebook(garment_hex="#EDE7DA"):
    img = _new_canvas()
    d = ImageDraw.Draw(img, "RGBA")
    base = _shade(garment_hex, 1.0)
    top, bottom = 460, 1360
    left, right = 540, 1180

    d.rectangle([left, top, right, bottom], fill=base, outline=_shade(garment_hex, 0.55), width=3)
    # spine
    d.rectangle([left - 24, top, left, bottom], fill=_shade(garment_hex, 0.55))
    for y in range(top + 30, bottom - 20, 55):
        d.ellipse([left - 30, y, left + 6, y + 24], fill=(20, 20, 20, 255))
    # corner fold shading
    d.polygon([(right - 90, bottom), (right, bottom), (right, bottom - 90)], fill=(*_shade(garment_hex, 0.75)[:3], 200))

    print_area = (left + 90, top + 140, right - 90, top + 640)
    return img, print_area


def render_sticker(garment_hex="#FFFFFF"):
    """Die-cut circular sticker - background stays transparent outside the circle."""
    img = _new_canvas()
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = CANVAS / 2, CANVAS / 2
    r = 620
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=_shade(garment_hex, 1.0))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 255), width=18)
    d.ellipse([cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10], outline=(160, 160, 160, 140), width=6)
    print_area = (cx - r + 90, cy - r + 90, cx + r - 90, cy + r - 90)
    return img, print_area


PRODUCTS = {
    "tshirt": render_tshirt,
    "hoodie": render_hoodie,
    "mug": render_mug,
    "tote": render_tote,
    "cap": render_cap,
    "bottle": render_bottle,
    "notebook": render_notebook,
    "sticker": render_sticker,
}
