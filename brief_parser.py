"""
Stage 1: Trend Researcher (replacement)
----------------------------------------
No external API / no web scraping. Matches the free-text brief against a
curated style knowledge base (data/word_banks.json + data/style_bank.json).
100% free and unlimited to run.
"""
import json
import os
import re


def _find_data_dir():
    """Locate the data/ folder without assuming a fixed nesting depth -
    works whether this file lives in engine/ next to a sibling data/
    folder, or everything got flattened into one directory during upload
    (e.g. GitHub drag-and-drop losing subfolder structure)."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [here]
    # walk up a few levels, checking both "this dir" and "this dir/data"
    d = here
    for _ in range(4):
        candidates.append(os.path.join(d, "data"))
        d = os.path.dirname(d)
        candidates.append(d)
    candidates.append(os.path.join(os.getcwd(), "data"))
    for c in candidates:
        if os.path.isfile(os.path.join(c, "word_banks.json")):
            return c
    raise FileNotFoundError(
        "Could not find data/word_banks.json anywhere near "
        f"{here} or in the current working directory. Make sure the "
        "'data' folder (with style_bank.json and word_banks.json) was "
        "uploaded to the repo.")


DATA_DIR = _find_data_dir()


def _load(name):
    with open(os.path.join(DATA_DIR, name), "r") as f:
        return json.load(f)


def parse_brief(brief_text: str) -> dict:
    word_banks = _load("word_banks.json")
    text = brief_text.lower()

    mood_scores = {}
    for tag, keywords in word_banks["mood_keywords"].items():
        count = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", text))
        if count:
            mood_scores[tag] = count

    industry_scores = {}
    for industry, keywords in word_banks["industry_keywords"].items():
        count = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", text))
        if count:
            industry_scores[industry] = count

    mood_tags = sorted(mood_scores, key=lambda t: -mood_scores[t])
    industry = max(industry_scores, key=industry_scores.get) if industry_scores else "general"

    if not mood_tags:
        mood_tags = ["modern", "minimal"]

    return {
        "raw": brief_text,
        "mood_tags": mood_tags,
        "industry": industry,
        "industry_scores": industry_scores,
        "mood_scores": mood_scores,
    }


if __name__ == "__main__":
    import sys
    brief = sys.argv[1] if len(sys.argv) > 1 else "Luxury coffee brand for Gen Z"
    print(json.dumps(parse_brief(brief), indent=2))
