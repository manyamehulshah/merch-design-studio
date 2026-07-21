"""
Stage 6: Portfolio Builder (premium dark theme)
--------------------------------------------------
The layout/typography quality of a design agency deck - dark background,
bold display type, bordered image grids - built with reportlab. This part
of the "looks expensive" bar has nothing to do with AI image quality; it's
just careful page design, and it's free.
"""
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                 PageBreak, Image as RLImage, Table, TableStyle, NextPageTemplate)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

BG = colors.HexColor("#141414")
CREAM = colors.HexColor("#F3EFE7")
MUTED = colors.HexColor("#9A9A93")
LINE = colors.HexColor("#3A3A36")
ACCENT = colors.HexColor("#D8C9A3")

FONT_DIR_CANDIDATES = {
    # reportlab's TTFont only supports glyf-outline TrueType files, not
    # CFF/postscript-outline OTF - so .ttf paths must be tried first.
    "Heading": [
        "/usr/share/fonts/truetype/montserrat/Montserrat-Black.ttf",
        "/usr/share/fonts/opentype/montserrat/Montserrat-Black.otf",
    ],
    "HeadingBold": [
        "/usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf",
        "/usr/share/fonts/opentype/montserrat/Montserrat-Bold.otf",
    ],
    "Body": [
        "/usr/share/fonts/truetype/open-sans/OpenSans-Regular.ttf",
        "/usr/share/fonts/opentype/inter/Inter-Regular.otf",
    ],
    "BodyLight": [
        "/usr/share/fonts/truetype/open-sans/OpenSans-Light.ttf",
        "/usr/share/fonts/opentype/inter/Inter-Light.otf",
    ],
}

_FONTS_REGISTERED = {}


def _register_fonts():
    if _FONTS_REGISTERED:
        return _FONTS_REGISTERED
    for name, candidates in FONT_DIR_CANDIDATES.items():
        path = next((p for p in candidates if os.path.exists(p)), None)
        if path:
            pdfmetrics.registerFont(TTFont(name, path))
            _FONTS_REGISTERED[name] = name
        else:
            _FONTS_REGISTERED[name] = "Helvetica-Bold" if "Heading" in name else "Helvetica"
    return _FONTS_REGISTERED


def _dot_marker():
    t = Table([["", "", ""]], colWidths=[9, 9, 9], rowHeights=[9])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), ACCENT),
        ("BACKGROUND", (1, 0), (1, 0), ACCENT),
        ("BACKGROUND", (2, 0), (2, 0), ACCENT),
    ]))
    return t


def _dark_page(canvas: pdfcanvas.Canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BG)
    canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
    fonts = _register_fonts()
    canvas.setFont(fonts["Body"], 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.75 * inch, 0.45 * inch, "MERCH DESIGN STUDIO")
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.45 * inch, f"{doc.page:02d}")
    canvas.restoreState()


def build_portfolio(brief_text: str, parsed_brief: dict, concepts: list,
                     selected_concept: dict, artwork_paths: dict, mockup_paths: dict,
                     out_path: str, brand_line: str = "AI DESIGN PIPELINE"):
    fonts = _register_fonts()

    title_style = ParagraphStyle("Title", fontName=fonts["Heading"], fontSize=42, leading=46,
                                  textColor=CREAM, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle("Subtitle", fontName=fonts["Body"], fontSize=13, leading=18,
                                     textColor=MUTED, alignment=TA_CENTER)
    kicker_style = ParagraphStyle("Kicker", fontName=fonts["Body"], fontSize=10, leading=14,
                                   textColor=ACCENT, alignment=TA_CENTER, tracking=2)
    h2 = ParagraphStyle("H2", fontName=fonts["Heading"], fontSize=24, leading=28,
                         textColor=CREAM, spaceAfter=14)
    body = ParagraphStyle("Body", fontName=fonts["Body"], fontSize=10.5, leading=16, textColor=MUTED)
    caption = ParagraphStyle("Caption", fontName=fonts["HeadingBold"], fontSize=10, leading=13,
                              textColor=CREAM, alignment=TA_CENTER, spaceBefore=6)
    small = ParagraphStyle("Small", fontName=fonts["Body"], fontSize=8.5, textColor=MUTED)

    story = []

    # ---------------- Cover ----------------
    story.append(Spacer(1, 1.7 * inch))
    story.append(Paragraph("MERCH DESIGN PORTFOLIO", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(brief_text.upper(), subtitle_style))
    story.append(Spacer(1, 0.35 * inch))
    line_tbl = Table([[""]], colWidths=[2.6 * inch], rowHeights=[1])
    line_tbl.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, -1), 1, LINE)]))
    story.append(line_tbl)
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(brand_line, kicker_style))
    story.append(Spacer(1, 2.2 * inch))

    contact_tbl = Table([[Paragraph(f"{len(concepts)} CONCEPTS &nbsp;|&nbsp; "
                                     f"{len(mockup_paths)} PRODUCT MOCKUPS &nbsp;|&nbsp; "
                                     f"GENERATED FREE, NO STOCK IMAGERY",
                                     ParagraphStyle("Contact", fontName=fonts["Body"], fontSize=9,
                                                     textColor=CREAM, alignment=TA_CENTER))]],
                         colWidths=[5.5 * inch])
    contact_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(contact_tbl)
    story.append(NextPageTemplate("Inner"))
    story.append(PageBreak())

    # ---------------- Creative direction ----------------
    story.append(_dot_marker())
    story.append(Spacer(1, 8))
    story.append(Paragraph("CREATIVE DIRECTION", h2))
    story.append(Paragraph(f"<font color='#F3EFE7'><b>Brief</b></font> &nbsp; {brief_text}", body))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Mood direction</b> &nbsp; {', '.join(parsed_brief['mood_tags']).upper()}", body))
    story.append(Paragraph(f"<b>Category</b> &nbsp; {parsed_brief['industry'].upper()}", body))
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        f"{len(concepts)} distinct design directions were generated from this brief using a "
        f"curated palette, typography, and motif system, then filtered down to unique, "
        f"non-redundant concepts. The strongest-fit direction below was carried through to "
        f"final artwork and product mockups.", body))
    story.append(PageBreak())

    # ---------------- Concept grid ----------------
    story.append(_dot_marker())
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"CONCEPT DIRECTIONS ({len(concepts)})", h2))
    thumbs_per_row = 3
    rows = []
    row = []
    for c in concepts:
        thumb_path = artwork_paths.get(c["id"])
        cell_flow = []
        if thumb_path and os.path.exists(thumb_path):
            img = RLImage(thumb_path, width=1.75 * inch, height=1.75 * inch)
            framed = Table([[img]], colWidths=[1.85 * inch], rowHeights=[1.85 * inch])
            framed.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.75, LINE),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            cell_flow.append(framed)
        cell_flow.append(Paragraph(c["name"].upper(), caption))
        row.append(cell_flow)
        if len(row) == thumbs_per_row:
            rows.append(row)
            row = []
    if row:
        while len(row) < thumbs_per_row:
            row.append([Paragraph("", body)])
        rows.append(row)

    grid = Table(rows, colWidths=[2.05 * inch] * thumbs_per_row)
    grid.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(grid)
    story.append(PageBreak())

    # ---------------- Selected concept hero ----------------
    story.append(_dot_marker())
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"SELECTED DIRECTION — {selected_concept['name'].upper()}", h2))
    story.append(Paragraph(selected_concept["description"], body))
    story.append(Spacer(1, 14))
    hero_path = artwork_paths.get(selected_concept["id"])
    if hero_path and os.path.exists(hero_path):
        hero_img = RLImage(hero_path, width=4.3 * inch, height=4.3 * inch)
        hero_framed = Table([[hero_img]], colWidths=[4.4 * inch], rowHeights=[4.4 * inch])
        hero_framed.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, LINE),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        story.append(hero_framed)
    story.append(PageBreak())

    # ---------------- Product mockups ----------------
    story.append(_dot_marker())
    story.append(Spacer(1, 8))
    story.append(Paragraph("PRODUCT MOCKUPS", h2))
    mock_items = list(mockup_paths.items())
    per_row = 3
    mock_rows = []
    row = []
    for product, path in mock_items:
        if not os.path.exists(path):
            continue
        img = RLImage(path, width=1.7 * inch, height=1.7 * inch)
        framed = Table([[img]], colWidths=[1.8 * inch], rowHeights=[1.8 * inch])
        framed.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.75, LINE),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        cell = [framed, Paragraph(product.upper(), caption)]
        row.append(cell)
        if len(row) == per_row:
            mock_rows.append(row)
            row = []
    if row:
        while len(row) < per_row:
            row.append([Paragraph("", body)])
        mock_rows.append(row)
    mock_table = Table(mock_rows, colWidths=[2.0 * inch] * per_row)
    mock_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
    ]))
    story.append(mock_table)
    story.append(Spacer(1, 20))
    story.append(Paragraph(small_footer_note(), small))

    doc = BaseDocTemplate(out_path, pagesize=letter)
    frame_cover = Frame(0.9 * inch, 0.9 * inch, letter[0] - 1.8 * inch, letter[1] - 1.8 * inch, id="cover")
    frame_inner = Frame(0.85 * inch, 0.85 * inch, letter[0] - 1.7 * inch, letter[1] - 1.7 * inch, id="inner")
    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[frame_cover], onPage=_dark_page),
        PageTemplate(id="Inner", frames=[frame_inner], onPage=_dark_page),
    ])
    doc.build(story)
    return out_path


def small_footer_note():
    return ("Every design on this page was generated procedurally (palette theory + "
            "typography pairing + vector motif system) - no stock photography, no "
            "diffusion model, no per-image API cost.")
