#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path


TEXT_EXTENSIONS = {
    ".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".jsx", ".ts",
    ".tsx", ".vue", ".svelte", ".md", ".mdx", ".json", ".astro"
}

CATEGORIES = [
    ("A", "First-Viewport Composition", 18),
    ("B", "Brand Signal and Specificity", 14),
    ("C", "Hero Discipline and Content Budget", 14),
    ("D", "Visual Anchor and Atmosphere", 12),
    ("E", "Typography and Visual Direction", 12),
    ("F", "Restraint and Section Focus", 10),
    ("G", "Responsive Composition", 8),
    ("H", "Motion and Interaction Presence", 6),
    ("I", "Design-System Fit and React Practice", 6),
]


def read_files(target):
    target = Path(target)
    files = []
    gaps = []
    if target.is_file():
        candidates = [target]
    else:
        ignored = {"node_modules", ".git", "dist", "build", ".next", "coverage"}
        candidates = [
            p for p in target.rglob("*")
            if p.is_file() and not any(part in ignored for part in p.parts)
        ]

    for path in candidates:
        rel = str(path if target.is_file() else path.relative_to(target))
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".pdf"}:
                gaps.append({"path": rel, "reason": "binary or media file requires visual/manual review"})
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            gaps.append({"path": rel, "reason": "text extraction failed"})
            continue
        files.append({"path": rel, "text": text})
    return files, gaps


def count(pattern, corpus):
    return len(re.findall(pattern, corpus, flags=re.I | re.M))


def has(pattern, corpus):
    return bool(re.search(pattern, corpus, flags=re.I | re.M))


def evidence_path(files, pattern):
    regex = re.compile(pattern, flags=re.I | re.M)
    for item in files:
        if regex.search(item["text"]):
            return item["path"]
    return None


def grade(score):
    if score >= 85:
        return "Distinctive and Ship-Ready"
    if score >= 70:
        return "Strong With Targeted Revisions"
    if score >= 55:
        return "Directionally Plausible"
    if score >= 35:
        return "Generic or Overbuilt"
    return "Rework First"


def make_category(cid, name, points, score, rationale, evidence, gaps):
    return {
        "id": cid,
        "name": name,
        "points": points,
        "score": max(0, min(points, int(round(score)))),
        "rationale": rationale,
        "evidence": evidence,
        "gaps": gaps,
    }


def scan(target):
    files, extraction_gaps = read_files(target)
    corpus = "\n".join(item["text"] for item in files)

    signals = {
        "hero": count(r"\b(hero|masthead|jumbotron|headline)\b", corpus),
        "brand": count(r"\b(brand|logo|wordmark|product-name|site-title)\b", corpus),
        "cards": count(r"\b(card|panel|tile|shadow-|rounded-|border-radius)\b", corpus),
        "badges": count(r"\b(badge|chip|pill|tag|sticker|callout)\b", corpus),
        "stats": count(r"\b(stats?|metrics?|kpi|counter|number-strip)\b", corpus),
        "schedule": count(r"\b(schedule|agenda|event|this week|calendar|address)\b", corpus),
        "media": count(r"\b(img|image|picture|video|canvas|background-image|url\(|\.webp|\.jpg|\.png|\.mp4)\b", corpus),
        "gradient": count(r"\b(linear-gradient|radial-gradient|conic-gradient)\b", corpus),
        "flat_bg": count(r"background(?:-color)?\s*:\s*(#[0-9a-f]{3,8}|white|black|#[fF]{3,6})\s*;", corpus),
        "default_fonts": count(r"\b(Inter|Roboto|Arial|system-ui|-apple-system|BlinkMacSystemFont)\b", corpus),
        "font_face": count(r"@font-face|fonts\.googleapis|font-family\s*:\s*(?!.*(?:Inter|Roboto|Arial|system-ui|-apple-system))", corpus),
        "css_vars": count(r"--[a-z0-9-]+\s*:", corpus),
        "purple": count(r"#(?:7c3aed|8b5cf6|a855f7|9333ea|6d28d9)|purple|violet|indigo", corpus),
        "motion": count(r"\b(animation|transition|framer-motion|motion\.|@keyframes|animate-)\b", corpus),
        "reduced_motion": count(r"prefers-reduced-motion", corpus),
        "responsive": count(r"@media|@container|clamp\(|minmax\(|vw|vh|dvh|svh", corpus),
        "tests": count(r"playwright|cypress|storybook|screenshot|viewport|axe|testing-library", corpus),
        "react_modern": count(r"useEffectEvent|startTransition|useDeferredValue", corpus),
        "memo": count(r"useMemo|useCallback", corpus),
        "design_system": count(r"design-system|tokens|theme|variant|components/ui|radix|shadcn|chakra|mui", corpus),
        "sections": count(r"<section|\bsection\b", corpus),
    }

    categories = []
    risks = []
    actions = []
    manual_gaps = [
        {"path": str(target), "reason": "manual screenshot review required for first-viewport composition and brand test"},
        {"path": str(target), "reason": "manual review required to judge image relevance, typography taste, and motion quality"},
    ]

    hero_path = evidence_path(files, r"\b(hero|masthead|headline)\b")
    card_clutter = signals["cards"] + signals["badges"] + signals["stats"] + signals["schedule"]
    comp_score = 9
    if signals["hero"]:
        comp_score += 4
    if signals["sections"] and card_clutter < 20:
        comp_score += 3
    if card_clutter > 50:
        comp_score -= 6
    elif card_clutter > 25:
        comp_score -= 3
    categories.append(make_category(
        "A", "First-Viewport Composition", 18, comp_score,
        "Hero and section evidence are balanced against dashboard-like clutter signals.",
        [{"path": hero_path or str(target), "detail": f"hero signals={signals['hero']}, clutter signals={card_clutter}"}],
        ["Screenshot review must confirm the first viewport reads as one composition."],
    ))

    brand_score = 5 + min(signals["brand"], 5)
    generic_terms = count(r"\b(transform|accelerate|streamline|unlock|next generation|all-in-one|beautifully|powerful)\b", corpus)
    if generic_terms > 8:
        brand_score -= 3
    if signals["brand"] == 0:
        risks.append({"severity": "high", "title": "Weak brand signal", "evidence": "No strong brand/logo/wordmark source signal found."})
        actions.append({"priority": 96, "effort": "S", "impact": "H", "action": "Make the brand or product name a hero-level visual signal, not only nav text.", "evidence": "Brand signal is missing or weak."})
    categories.append(make_category(
        "B", "Brand Signal and Specificity", 14, brand_score,
        "Brand, logo, and product-name signals are checked against generic copy risk.",
        [{"path": evidence_path(files, r"\b(brand|logo|wordmark|product-name)\b") or str(target), "detail": f"brand signals={signals['brand']}, generic copy signals={generic_terms}"}],
        ["Manual brand test: remove nav and confirm the first viewport still belongs to this brand."],
    ))

    hero_budget_score = 12
    if signals["cards"] > 18:
        hero_budget_score -= 4
    if signals["badges"] > 8:
        hero_budget_score -= 3
    if signals["stats"] + signals["schedule"] > 8:
        hero_budget_score -= 4
    if hero_budget_score < 9:
        risks.append({"severity": "medium", "title": "Hero clutter risk", "evidence": f"cards={signals['cards']}, badges={signals['badges']}, stats/schedule={signals['stats'] + signals['schedule']}."})
        actions.append({"priority": 92, "effort": "M", "impact": "H", "action": "Reduce the first viewport to brand, one headline, one support sentence, one CTA group, and one dominant visual.", "evidence": "Hero content budget appears overloaded."})
    categories.append(make_category(
        "C", "Hero Discipline and Content Budget", 14, hero_budget_score,
        "Hero clutter signals reduce the score because they compete with the primary composition.",
        [{"path": evidence_path(files, r"\b(card|badge|chip|stats?|schedule|event)\b") or str(target), "detail": f"cards={signals['cards']}, badges={signals['badges']}, stats/schedule={signals['stats'] + signals['schedule']}"}],
        ["Source scan cannot prove these elements appear inside the first viewport."],
    ))

    visual_score = 3
    if signals["media"]:
        visual_score += 5
    if signals["gradient"]:
        visual_score += 2
    if signals["flat_bg"] > signals["gradient"] + signals["media"]:
        visual_score -= 2
    if signals["media"] == 0:
        actions.append({"priority": 88, "effort": "M", "impact": "H", "action": "Add a dominant real visual anchor showing product, place, atmosphere, or context.", "evidence": "No image/video/canvas/media source signal found."})
    categories.append(make_category(
        "D", "Visual Anchor and Atmosphere", 12, visual_score,
        "Media, background image, and atmosphere signals are rewarded; flat backgrounds alone are weak.",
        [{"path": evidence_path(files, r"\b(img|picture|video|canvas|background-image|linear-gradient|radial-gradient)\b") or str(target), "detail": f"media={signals['media']}, gradients={signals['gradient']}, flat backgrounds={signals['flat_bg']}"}],
        ["Manual review must confirm the visual anchor is real and relevant, not decorative only."],
    ))

    type_score = 4 + min(signals["css_vars"], 4) + min(signals["font_face"], 3)
    if signals["default_fonts"]:
        type_score -= 4
    if signals["purple"] > 8:
        type_score -= 2
        risks.append({"severity": "low", "title": "Purple/default palette risk", "evidence": f"purple/violet signals={signals['purple']}."})
    categories.append(make_category(
        "E", "Typography and Visual Direction", 12, type_score,
        "Custom font and CSS-variable evidence improves the score; default stacks and purple bias reduce it.",
        [{"path": evidence_path(files, r"font-family|@font-face|--[a-z0-9-]+\s*:") or str(target), "detail": f"default fonts={signals['default_fonts']}, css variables={signals['css_vars']}, purple signals={signals['purple']}"}],
        ["Manual review must judge whether type and color are purposeful for the domain."],
    ))

    restraint_score = 8
    if signals["cards"] > 30:
        restraint_score -= 4
    if signals["badges"] > 12:
        restraint_score -= 2
    if signals["sections"] > 16:
        restraint_score -= 2
    categories.append(make_category(
        "F", "Restraint and Section Focus", 10, restraint_score,
        "Repeated cards, badges, and many sections are treated as clutter risk.",
        [{"path": evidence_path(files, r"\b(card|badge|chip|pill|<section)\b") or str(target), "detail": f"cards={signals['cards']}, badges={signals['badges']}, sections={signals['sections']}"}],
        ["Manual review must confirm whether cards are interaction containers or decorative wrappers."],
    ))

    resp_score = 2 + min(signals["responsive"], 5)
    if signals["tests"]:
        resp_score += 1
    if signals["responsive"] < 2:
        actions.append({"priority": 84, "effort": "S", "impact": "H", "action": "Verify and tune the layout at desktop and mobile widths with screenshots.", "evidence": "Responsive source evidence is thin."})
    categories.append(make_category(
        "G", "Responsive Composition", 8, resp_score,
        "Responsive CSS and screenshot/test evidence indicate whether the composition can survive viewport changes.",
        [{"path": evidence_path(files, r"@media|@container|clamp\(|playwright|viewport|screenshot") or str(target), "detail": f"responsive signals={signals['responsive']}, test signals={signals['tests']}"}],
        ["Actual desktop and mobile rendering must be checked before ship-readiness claims."],
    ))

    motion_score = min(4, signals["motion"])
    if signals["motion"] >= 2:
        motion_score += 1
    if signals["reduced_motion"]:
        motion_score += 1
    categories.append(make_category(
        "H", "Motion and Interaction Presence", 6, motion_score,
        "Motion declarations and reduced-motion handling are counted as baseline evidence.",
        [{"path": evidence_path(files, r"animation|transition|@keyframes|framer-motion|prefers-reduced-motion") or str(target), "detail": f"motion signals={signals['motion']}, reduced-motion={signals['reduced_motion']}"}],
        ["Manual review must confirm motion creates hierarchy rather than noise."],
    ))

    system_score = 3
    if signals["design_system"]:
        system_score += 2
    if signals["react_modern"]:
        system_score += 1
    if signals["memo"] > signals["react_modern"] + 3:
        system_score -= 1
    categories.append(make_category(
        "I", "Design-System Fit and React Practice", 6, system_score,
        "Design-system reuse and repo-aligned React patterns are rewarded; unnecessary memoization is flagged lightly.",
        [{"path": evidence_path(files, r"design-system|tokens|theme|useEffectEvent|startTransition|useDeferredValue|useMemo|useCallback") or str(target), "detail": f"design-system={signals['design_system']}, modern React={signals['react_modern']}, memo callbacks={signals['memo']}"}],
        ["Existing design-system constraints may justify exceptions to the landing-page rules."],
    ))

    for category in categories:
        if category["score"] < category["points"] * 0.55:
            actions.append({
                "priority": 70 + category["points"],
                "effort": "M",
                "impact": "H" if category["points"] >= 12 else "M",
                "action": f"Improve {category['name'].lower()} using the rubric's strong-evidence criteria.",
                "evidence": category["rationale"],
            })

    total = sum(item["score"] for item in categories)
    result = {
        "schema_version": "1.0",
        "target": str(target),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "score": total,
        "grade": grade(total),
        "mode": "heuristic baseline + manual visual review",
        "categories": categories,
        "risks": risks,
        "actions": sorted(actions, key=lambda item: item["priority"], reverse=True)[:8],
        "extraction_gaps": extraction_gaps + manual_gaps,
        "metadata": {"files_scanned": len(files), "signals": signals},
    }
    return result


def print_markdown(data):
    print(f"# Frontend Design Cartography: {data['score']}/100")
    print(f"Grade: {data['grade']}")
    print()
    for category in data["categories"]:
        print(f"- {category['id']}. {category['name']}: {category['score']}/{category['points']}")
    if data["risks"]:
        print("\n## Risks")
        for risk in data["risks"]:
            print(f"- {risk['severity']}: {risk['title']} ({risk['evidence']})")
    if data["actions"]:
        print("\n## Top Actions")
        for action in data["actions"][:3]:
            print(f"- P{action['priority']}: {action['action']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target")
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    data = scan(args.target)
    if args.json_path:
        Path(args.json_path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.markdown or not args.json_path:
        print_markdown(data)


if __name__ == "__main__":
    main()
