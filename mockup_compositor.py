"""
Stage 5: Mockup Creator
------------------------
Composites the transparent "print" artwork onto procedurally-drawn product
templates. No stock photography needed, runs unlimited times for free.
"""
import os
from PIL import Image

from product_templates import PRODUCTS


def make_mockup(print_png_path: str, product: str, garment_hex: str, out_path: str):
    if product not in PRODUCTS:
        raise ValueError(f"Unknown product '{product}'. Options: {list(PRODUCTS)}")

    template_img, print_area = PRODUCTS[product](garment_hex)
    art = Image.open(print_png_path).convert("RGBA")

    x0, y0, x1, y1 = print_area
    area_w, area_h = x1 - x0, y1 - y0

    scale = min(area_w / art.width, area_h / art.height)
    new_w, new_h = int(art.width * scale), int(art.height * scale)
    art_resized = art.resize((new_w, new_h), Image.LANCZOS)

    paste_x = int(x0 + (area_w - new_w) / 2)
    paste_y = int(y0 + (area_h - new_h) / 2)

    template_img.alpha_composite(art_resized, (paste_x, paste_y))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    template_img.save(out_path)
    return out_path


def make_all_mockups(concept: dict, print_png_path: str, out_dir: str,
                      products=("tshirt", "hoodie", "mug", "tote", "cap", "bottle", "notebook", "sticker"),
                      garment_hex="#F2F0EA"):
    results = {}
    for product in products:
        out_path = os.path.join(out_dir, f"{concept['id']}_{product}.png")
        results[product] = make_mockup(print_png_path, product, garment_hex, out_path)
    return results
