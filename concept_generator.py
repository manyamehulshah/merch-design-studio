"""
Stage 2 + 3: Creative Director + weak-concept filter
------------------------------------------------------
Generates N candidate design directions from a parsed brief, then removes
near-duplicate concepts. Fully procedural - no LLM call, no API cost.
"""
import json
import os
import random

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _load(name):
    with open(os.path.join(DATA_DIR, name), "r") as f:
        return json.load(f)


def _score(item_tags, mood_tags):
    return sum(1 for t in item_tags if t in mood_tags)


def _weighted_choice(rng, items, weights):
    total = sum(weights)
    if total <= 0:
        return rng.choice(items)
    r = rng.uniform(0, total)
    upto = 0
    for item, w in zip(items, weights):
        upto += w
        if upto >= r:
            return item
    return items[-1]


def generate_concepts(parsed_brief: dict, count: int = 30, seed: int = None) -> list:
    rng = random.Random(seed)
    style_bank = _load("style_bank.json")
    word_banks = _load("word_banks.json")

    mood_tags = parsed_brief["mood_tags"]
    industry = parsed_brief["industry"]

    palettes = style_bank["palettes"]
    typographies = style_bank["typography_pairings"]
    motifs = style_bank["motif_styles"]

    palette_weights = [_score(p["tags"], mood_tags) + 0.6 for p in palettes]
    typo_weights = [_score(t["tags"], mood_tags) + 0.6 for t in typographies]
    motif_weights = [_score(m["tags"], mood_tags) + 0.6 for m in motifs]

    adjectives = []
    for tag in mood_tags:
        adjectives.extend(word_banks["adjectives_by_tag"].get(tag, []))
    if not adjectives:
        for adjs in word_banks["adjectives_by_tag"].values():
            adjectives.extend(adjs)
    adjectives = list(dict.fromkeys(adjectives))

    nouns = list(word_banks["nouns_by_industry"].get(industry, []))
    nouns.extend(word_banks["nouns_by_industry"]["general"])
    nouns = list(dict.fromkeys(nouns))

    raw_concepts = []
    seen_combo = set()
    attempts = 0
    max_attempts = count * 15

    while len(raw_concepts) < count and attempts < max_attempts:
        attempts += 1
        palette = _weighted_choice(rng, palettes, palette_weights)
        typography = _weighted_choice(rng, typographies, typo_weights)
        motif = _weighted_choice(rng, motifs, motif_weights)

        combo_key = (palette["id"], typography["id"], motif["id"])
        if combo_key in seen_combo:
            continue
        seen_combo.add(combo_key)

        adj = rng.choice(adjectives)
        noun = rng.choice(nouns)
        name = f"{adj} {noun}"

        fit_score = (
            _score(palette["tags"], mood_tags)
            + _score(typography["tags"], mood_tags)
            + _score(motif["tags"], mood_tags)
        )

        raw_concepts.append({
            "id": f"concept_{len(raw_concepts) + 1:02d}",
            "name": name,
            "palette": palette,
            "typography": typography,
            "motif": motif,
            "fit_score": fit_score,
            "description": (
                f"\"{name}\" pairs a {palette['name'].lower()} palette with "
                f"{typography['name'].lower()} type and a {motif['name'].lower()} "
                f"motif - built for a {', '.join(mood_tags) if mood_tags else 'modern'} "
                f"{industry if industry != 'general' else 'brand'} audience."
            ),
        })

    by_name = {}
    for c in raw_concepts:
        if c["name"] not in by_name or c["fit_score"] > by_name[c["name"]]["fit_score"]:
            by_name[c["name"]] = c
    deduped = list(by_name.values())

    deduped.sort(key=lambda c: -c["fit_score"])
    for i, c in enumerate(deduped, 1):
        c["id"] = f"concept_{i:02d}"

    return deduped


if __name__ == "__main__":
    import sys
    from brief_parser import parse_brief

    brief = sys.argv[1] if len(sys.argv) > 1 else "Luxury coffee brand for Gen Z"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    parsed = parse_brief(brief)
    concepts = generate_concepts(parsed, count=n, seed=42)
    print(f"Generated {len(concepts)} unique concepts")
