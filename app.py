"""
Merch Design Studio - interactive app
---------------------------------------
Brief in -> concepts out -> pick favorites -> mockups on every product ->
polished PDF portfolio. 100% free/local engine underneath (no image-gen API).

Run with:  streamlit run app.py
"""
import os
import sys
import tempfile

import streamlit as st

def _find_engine_dir():
    """Locate the engine/ folder without assuming a fixed nesting depth -
    handles both the intended app/ + engine/ layout and a flattened repo
    where everything landed in one directory (no engine/ subfolder at all -
    in that case brief_parser.py etc. are already importable from here)."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [here]
    d = here
    for _ in range(4):
        candidates.append(os.path.join(d, "engine"))
        d = os.path.dirname(d)
        candidates.append(d)
    for c in candidates:
        if os.path.isfile(os.path.join(c, "brief_parser.py")):
            return c
    return here  # last resort: let the following imports raise a clear error


ENGINE_DIR = _find_engine_dir()
sys.path.insert(0, ENGINE_DIR)

from brief_parser import parse_brief
from concept_generator import generate_concepts
from artwork_generator import render_concept
from mockup_compositor import make_all_mockups
from portfolio_builder import build_portfolio

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKDIR = os.path.join(tempfile.gettempdir(), "merch_studio_session")
ART_DIR = os.path.join(WORKDIR, "artwork")
MOCK_DIR = os.path.join(WORKDIR, "mockups")
PORT_DIR = os.path.join(WORKDIR, "portfolio")
for d in (ART_DIR, MOCK_DIR, PORT_DIR):
    os.makedirs(d, exist_ok=True)

ALL_PRODUCTS = ["tshirt", "hoodie", "mug", "tote", "cap", "bottle", "notebook", "sticker"]

st.set_page_config(page_title="Merch Design Studio", page_icon="👕", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #141414; }
h1, h2, h3, p, label, .stMarkdown { color: #F3EFE7 !important; }
.stButton>button { background-color: #D8C9A3; color: #141414; font-weight: 700; border: none; }
.stButton>button:hover { background-color: #c9b98d; color: #141414; }
div[data-baseweb="radio"] label, div[data-baseweb="checkbox"] label { color: #F3EFE7 !important; }
</style>
""", unsafe_allow_html=True)

st.title("Merch Design Studio")
st.caption("Free, unlimited, procedural design pipeline - brief in, product-ready portfolio out.")

if "concepts" not in st.session_state:
    st.session_state.concepts = None
    st.session_state.parsed = None
    st.session_state.brief = ""
    st.session_state.artwork_paths = {}
    st.session_state.selected_ids = []

# ---------------- Step 1: input ----------------
st.header("1. Describe your brand")
brief = st.text_input("Brand brief", placeholder="e.g. Luxury coffee brand for Gen Z",
                       value=st.session_state.brief)

scope = st.radio("How many directions do you want to explore?",
                  ["Full collection (30-50 designs)", "Focused (2-3 styles)"], horizontal=True)

products_wanted = st.multiselect("Which products should designs be applied to?",
                                  ALL_PRODUCTS, default=ALL_PRODUCTS)

generate_clicked = st.button("Generate Designs", type="primary")

if generate_clicked and brief.strip():
    count = 40 if scope.startswith("Full") else 3
    with st.spinner(f"Generating {count} design directions..."):
        parsed = parse_brief(brief)
        concepts = generate_concepts(parsed, count=count, seed=None)
        artwork_paths = {}
        progress = st.progress(0.0)
        for i, c in enumerate(concepts):
            paths = render_concept(c, ART_DIR, seed=i)
            artwork_paths[c["id"]] = paths
            progress.progress((i + 1) / len(concepts))
        progress.empty()

    st.session_state.concepts = concepts
    st.session_state.parsed = parsed
    st.session_state.brief = brief
    st.session_state.artwork_paths = artwork_paths
    st.session_state.selected_ids = []
    st.session_state.products_wanted = products_wanted

# ---------------- Step 2: gallery + selection ----------------
if st.session_state.concepts:
    st.header(f"2. Pick your favorites ({len(st.session_state.concepts)} generated)")
    st.caption(f"Mood: {', '.join(st.session_state.parsed['mood_tags'])} | "
               f"Category: {st.session_state.parsed['industry']}")

    cols_per_row = 4
    concepts = st.session_state.concepts
    selected = set(st.session_state.selected_ids)

    for row_start in range(0, len(concepts), cols_per_row):
        row_concepts = concepts[row_start:row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, c in zip(cols, row_concepts):
            with col:
                poster_path = st.session_state.artwork_paths[c["id"]]["poster"]
                st.image(poster_path, use_container_width=True)
                checked = st.checkbox(c["name"], value=(c["id"] in selected), key=f"chk_{c['id']}")
                if checked:
                    selected.add(c["id"])
                else:
                    selected.discard(c["id"])
    st.session_state.selected_ids = list(selected)

    st.divider()
    st.header("3. Build mockups + portfolio")
    garment_hex = st.color_picker("Base product color", "#F2F0EA")

    build_clicked = st.button("Apply to Products & Build Portfolio", type="primary",
                               disabled=(len(st.session_state.selected_ids) == 0))

    if build_clicked:
        chosen = [c for c in concepts if c["id"] in st.session_state.selected_ids]
        products = st.session_state.get("products_wanted", ALL_PRODUCTS) or ALL_PRODUCTS
        with st.spinner("Applying designs to products and building portfolio..."):
            all_mockups = {}
            for c in chosen:
                print_path = st.session_state.artwork_paths[c["id"]]["print"]
                mockups = make_all_mockups(c, print_path, MOCK_DIR, products=products,
                                            garment_hex=garment_hex)
                all_mockups[c["id"]] = mockups

            primary = chosen[0]
            pdf_path = os.path.join(PORT_DIR, "merch_portfolio.pdf")
            build_portfolio(
                st.session_state.brief, st.session_state.parsed, chosen, primary,
                {cid: paths["poster"] for cid, paths in st.session_state.artwork_paths.items()},
                all_mockups[primary["id"]], pdf_path,
            )

        st.success("Portfolio built.")
        st.session_state.pdf_path = pdf_path
        st.session_state.all_mockups = all_mockups

    if st.session_state.get("pdf_path") and os.path.exists(st.session_state.pdf_path):
        st.subheader("Mockup previews")
        for cid, mockups in st.session_state.get("all_mockups", {}).items():
            name = next(c["name"] for c in concepts if c["id"] == cid)
            st.markdown(f"**{name}**")
            mcols = st.columns(len(mockups))
            for mcol, (product, path) in zip(mcols, mockups.items()):
                with mcol:
                    st.image(path, caption=product, use_container_width=True)

        with open(st.session_state.pdf_path, "rb") as f:
            st.download_button("Download Portfolio PDF", f, file_name="merch_portfolio.pdf",
                                mime="application/pdf", type="primary")
