#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path


TEXT_EXTS = {
    ".css", ".scss", ".sass", ".less", ".ts", ".tsx", ".js", ".jsx", ".mjs",
    ".html", ".md", ".json", ".yaml", ".yml", ".vue", ".svelte", ".astro",
}

CATEGORY_POINTS = {
    "A": 10,
    "B": 15,
    "C": 15,
    "D": 15,
    "E": 10,
    "F": 15,
    "G": 10,
    "H": 5,
    "I": 5,
}


def read_text(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def section(text, heading):
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.M)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^## ", text[start:], re.M)
    end = start + next_match.start() if next_match else len(text)
    return text[start:end].strip()


def parse_table_rows(block):
    rows = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0].lower() not in {"name", "role", "level", "element"}:
            rows.append(cells)
    return rows


def parse_reference(path):
    text = read_text(path)
    title = re.search(r"^#\s+(.+?)\s+—\s+Style Reference\s*$", text, re.M)
    theme = re.search(r"\*\*Theme:\*\*\s*([A-Za-z-]+)", text)
    color_section = section(text, "Tokens — Colors")
    typography_section = section(text, "Tokens — Typography")
    spacing_section = section(text, "Tokens — Spacing & Shapes")
    components_section = section(text, "Components")
    dos_section = section(text, "Do's and Don'ts")
    imagery_section = section(text, "Imagery")
    layout_section = section(text, "Layout")
    quick_section = section(text, "Quick Start")

    colors = []
    for cells in parse_table_rows(color_section):
        if len(cells) >= 4:
            colors.append({
                "name": cells[0],
                "value": strip_code(cells[1]),
                "token": strip_code(cells[2]),
                "role": cells[3],
            })

    fonts = []
    for match in re.finditer(r"^###\s+(.+?)\s+—\s+(.+?)\s+·\s+`([^`]+)`", typography_section, re.M):
        font_block_start = match.end()
        next_match = re.search(r"^###\s+", typography_section[font_block_start:], re.M)
        font_block = typography_section[font_block_start:font_block_start + next_match.start()] if next_match else typography_section[font_block_start:]
        fonts.append({
            "name": match.group(1).strip(),
            "description": match.group(2).strip(),
            "token": match.group(3).strip(),
            "weights": find_line_values(font_block, "Weights"),
            "sizes": find_line_values(font_block, "Sizes"),
            "line_height": find_line_values(font_block, "Line height"),
            "letter_spacing": find_line_values(font_block, "Letter spacing"),
        })

    type_scale = []
    type_scale_block = re.search(r"### Type Scale(.*?)(?:^## |\Z)", typography_section, re.S | re.M)
    if type_scale_block:
        for cells in parse_table_rows(type_scale_block.group(1)):
            if len(cells) >= 5:
                type_scale.append({
                    "role": cells[0],
                    "size": cells[1],
                    "line_height": cells[2],
                    "letter_spacing": cells[3],
                    "token": strip_code(cells[4]),
                })

    spacing = []
    spacing_block = re.search(r"### Spacing Scale(.*?)(?:^### |\Z)", spacing_section, re.S | re.M)
    if spacing_block:
        for cells in parse_table_rows(spacing_block.group(1)):
            if len(cells) >= 3:
                spacing.append({"name": cells[0], "value": cells[1], "token": strip_code(cells[2])})

    radii = []
    radius_block = re.search(r"### Border Radius(.*?)(?:^### |\Z)", spacing_section, re.S | re.M)
    if radius_block:
        for cells in parse_table_rows(radius_block.group(1)):
            if len(cells) >= 2:
                radii.append({"element": cells[0], "value": cells[1]})

    layout_tokens = {}
    for key, label in [("section_gap", "Section gap"), ("card_padding", "Card padding"), ("element_gap", "Element gap"), ("page_max_width", "Page max-width")]:
        m = re.search(rf"\*\*{re.escape(label)}:\*\*\s*([^\n]+)", spacing_section)
        if m:
            layout_tokens[key] = m.group(1).strip()

    shadows = []
    shadow_block = re.search(r"### Shadows(.*?)(?:^### |\Z)", spacing_section, re.S | re.M)
    if shadow_block:
        for cells in parse_table_rows(shadow_block.group(1)):
            if len(cells) >= 3:
                shadows.append({"name": cells[0], "value": strip_code(cells[1]), "token": strip_code(cells[2])})

    components = []
    for match in re.finditer(r"^###\s+(.+?)\s*$", components_section, re.M):
        start = match.end()
        next_match = re.search(r"^###\s+", components_section[start:], re.M)
        body = components_section[start:start + next_match.start()] if next_match else components_section[start:]
        components.append({"name": match.group(1).strip(), "body": compact(body)})

    do_rules = extract_bullets_after(dos_section, "### Do")
    dont_rules = extract_bullets_after(dos_section, "### Don't")
    quick_colors = {}
    q = re.search(r"Quick Color Reference:\s*(.*?)(?:\n\n|Example Component Prompts:)", section(text, "Agent Prompt Guide"), re.S)
    if q:
        for line in q.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                quick_colors[slug(k)] = v.strip()

    css_vars = sorted(set(re.findall(r"--[a-zA-Z0-9_-]+", quick_section)))
    hexes = sorted(set(re.findall(r"#[0-9a-fA-F]{3,8}\b", text)))

    return {
        "path": str(Path(path).resolve()),
        "brand": title.group(1).strip() if title else Path(path).stem,
        "theme": theme.group(1).lower() if theme else None,
        "sections_detected": sorted([name for name, value in {
            "colors": colors,
            "typography": fonts,
            "type_scale": type_scale,
            "spacing": spacing,
            "radii": radii,
            "shadows": shadows,
            "components": components,
            "do_rules": do_rules,
            "dont_rules": dont_rules,
            "imagery": imagery_section,
            "layout": layout_section,
            "quick_start": quick_section,
        }.items() if value]),
        "colors": colors,
        "fonts": fonts,
        "type_scale": type_scale,
        "spacing": spacing,
        "radii": radii,
        "layout_tokens": layout_tokens,
        "shadows": shadows,
        "components": components,
        "do_rules": do_rules,
        "dont_rules": dont_rules,
        "imagery": compact(imagery_section),
        "layout": compact(layout_section),
        "quick_colors": quick_colors,
        "css_vars": css_vars,
        "hexes": hexes,
    }


def strip_code(value):
    return value.replace("`", "").strip()


def compact(value):
    return re.sub(r"\s+", " ", value.strip())


def find_line_values(block, label):
    m = re.search(rf"- \*\*{re.escape(label)}:\*\*\s*([^\n]+)", block)
    if not m:
        return []
    return [v.strip() for v in re.split(r",\s*", m.group(1))]


def extract_bullets_after(block, heading):
    m = re.search(rf"^{re.escape(heading)}\s*(.*?)(?:^### |\Z)", block, re.M | re.S)
    if not m:
        return []
    return [line.strip()[2:].strip() for line in m.group(1).splitlines() if line.strip().startswith("- ")]


def scan_project(path):
    root = Path(path)
    files = []
    extraction_gaps = []
    corpus_parts = []
    for file_path in root.rglob("*"):
        if any(part in {".git", "node_modules", ".next", "dist", "build", "__pycache__"} for part in file_path.parts):
            continue
        if not file_path.is_file():
            continue
        rel = str(file_path.relative_to(root))
        if file_path.suffix.lower() not in TEXT_EXTS:
            if file_path.stat().st_size > 0:
                extraction_gaps.append({"path": rel, "reason": "unsupported or binary file"})
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            extraction_gaps.append({"path": rel, "reason": str(exc)})
            continue
        files.append({"path": rel, "text": text})
        corpus_parts.append(f"\n/* {rel} */\n{text}")
    corpus = "\n".join(corpus_parts)
    return {
        "root": str(root.resolve()),
        "files": files,
        "corpus": corpus,
        "lower": corpus.lower(),
        "extraction_gaps": extraction_gaps,
    }


def evidence_for_value(scan, value, label):
    if not value:
        return []
    needles = {value, value.lower()}
    if value.startswith("--"):
        needles.add(f"var({value})")
    out = []
    for f in scan["files"]:
        text_lower = f["text"].lower()
        if any(n.lower() in text_lower for n in needles):
            out.append({"path": f["path"], "detail": f"{label} `{value}` appears"})
            if len(out) >= 5:
                break
    return out


def count_matches(items, scan, key, label):
    matches = []
    for item in items:
        value = item.get(key)
        ev = evidence_for_value(scan, value, label)
        if ev:
            matches.append({"item": item, "evidence": ev})
    return matches


def contains_any(scan, words):
    lower = scan["lower"]
    return [w for w in words if w.lower() in lower]


def cap_score(points, ratio):
    return max(0, min(points, round(points * ratio)))


def score(reference, scan):
    categories = []
    risks = []
    actions = []
    manual_gaps = [
        {"area": "rendered visual match", "reason": "source scan cannot verify composition, responsive behavior, or final browser rendering"},
        {"area": "font loading", "reason": "source scan can find font declarations but cannot confirm actual webfont availability"},
        {"area": "imagery quality", "reason": "asset relevance and visual quality require screenshot or browser review"},
    ]

    def add_cat(cid, name, score_value, rationale, evidence=None, gaps=None):
        categories.append({
            "id": cid,
            "name": name,
            "points": CATEGORY_POINTS[cid],
            "score": int(max(0, min(CATEGORY_POINTS[cid], score_value))),
            "rationale": rationale,
            "evidence": evidence or [],
            "gaps": gaps or [],
        })

    expected_sections = {"colors", "typography", "spacing", "radii", "components", "do_rules", "dont_rules", "layout", "quick_start"}
    section_ratio = len(expected_sections.intersection(reference["sections_detected"])) / len(expected_sections)
    parse_score = cap_score(10, section_ratio)
    add_cat("A", "Reference Parse Completeness", parse_score, f"Detected {len(reference['sections_detected'])} reference sections.", [
        {"path": reference["path"], "detail": "Sections: " + ", ".join(reference["sections_detected"])}
    ], [] if parse_score >= 8 else ["Some expected Refero sections were not extracted."])

    token_values = [c["token"] for c in reference["colors"]] + reference["css_vars"]
    token_values = sorted(set(v for v in token_values if v))
    token_matches = [ev for v in token_values for ev in evidence_for_value(scan, v, "token")]
    token_ratio = len({e["detail"] for e in token_matches}) / max(1, len(token_values))
    raw_hex_matches = [ev for h in reference["hexes"] for ev in evidence_for_value(scan, h, "color value")]
    token_score = cap_score(15, min(1, token_ratio * 0.75 + min(1, len(raw_hex_matches) / max(1, len(reference["hexes"]))) * 0.25))
    add_cat("B", "Token Implementation", token_score, f"Found {len(token_matches)} token references and {len(raw_hex_matches)} raw value references.", token_matches[:8] + raw_hex_matches[:4], [] if token_score >= 10 else ["Reference tokens are missing or only weakly represented in source."])

    color_matches = count_matches(reference["colors"], scan, "value", "color")
    quick_color_values = [re.search(r"#[0-9a-fA-F]{3,8}\b", v).group(0) for v in reference["quick_colors"].values() if re.search(r"#[0-9a-fA-F]{3,8}\b", v)]
    role_matches = [ev for v in quick_color_values for ev in evidence_for_value(scan, v, "quick color role")]
    color_score = cap_score(15, min(1, (len(color_matches) / max(1, len(reference["colors"]))) * 0.65 + (len(role_matches) / max(1, len(quick_color_values))) * 0.35))
    add_cat("C", "Color Role Adherence", color_score, f"Matched {len(color_matches)} of {len(reference['colors'])} color values and {len(role_matches)} quick role values.", flatten_evidence(color_matches)[:8] + role_matches[:5], [] if color_score >= 10 else ["Primary color roles may not be implemented or may require manual CTA/surface review."])

    font_evidence = []
    for font in reference["fonts"]:
        for needle in [font["name"], font["token"]]:
            font_evidence.extend(evidence_for_value(scan, needle, "font"))
    type_tokens = [t["token"] for t in reference["type_scale"]]
    type_evidence = [ev for v in type_tokens for ev in evidence_for_value(scan, v, "type token")]
    tracking_values = sorted(set(v for f in reference["fonts"] for v in f.get("letter_spacing", []) if v and v != "normal"))
    tracking_evidence = [ev for v in tracking_values for ev in evidence_for_value(scan, v.split(" at ")[0], "tracking")]
    typ_score = cap_score(15, min(1, (len(font_evidence) / max(1, len(reference["fonts"]))) * 0.45 + (len(type_evidence) / max(1, len(type_tokens))) * 0.4 + min(1, len(tracking_evidence) / max(1, len(tracking_values))) * 0.15))
    add_cat("D", "Typography Adherence", typ_score, f"Found {len(font_evidence)} font references, {len(type_evidence)} type token references, and {len(tracking_evidence)} tracking references.", (font_evidence + type_evidence + tracking_evidence)[:10], [] if typ_score >= 10 else ["Typography tokens, scale, or tracking are weakly represented."])

    dim_values = [s["value"] for s in reference["spacing"]] + [r["value"] for r in reference["radii"]] + list(reference["layout_tokens"].values())
    shadow_values = [s["token"] for s in reference["shadows"]] + [s["value"] for s in reference["shadows"]]
    dim_evidence = [ev for v in dim_values for ev in evidence_for_value(scan, v, "dimension")]
    shadow_evidence = [ev for v in shadow_values for ev in evidence_for_value(scan, v, "shadow")]
    dim_expected = len(dim_values) + (len(shadow_values) if shadow_values else 0)
    dim_score = cap_score(10, min(1, (len(dim_evidence) + len(shadow_evidence)) / max(1, dim_expected)))
    if not reference["shadows"] and "box-shadow" in scan["lower"] and any("shadow" in rule.lower() and ("do not" in rule.lower() or "avoid" in rule.lower()) for rule in reference["dont_rules"]):
        dim_score = max(0, dim_score - 2)
        risks.append({"severity": "medium", "title": "Shadow usage may violate flat-surface guidance", "evidence": "Reference has no shadow table and a Don't rule discourages shadows, but source contains box-shadow."})
    add_cat("E", "Spacing, Radius, and Elevation", dim_score, f"Found {len(dim_evidence)} dimensional references and {len(shadow_evidence)} shadow/elevation references.", (dim_evidence + shadow_evidence)[:10], [] if dim_score >= 7 else ["Spacing, radius, or elevation values are missing or inconsistent."])

    component_words = [slug(c["name"]).replace("-", " ") for c in reference["components"]]
    component_hits = []
    for component in reference["components"]:
        words = [w for w in re.split(r"[^A-Za-z]+", component["name"]) if len(w) > 2]
        hits = contains_any(scan, words)
        value_hits = []
        for value in re.findall(r"#[0-9a-fA-F]{3,8}\b|\d+(?:\.\d+)?px", component["body"]):
            value_hits.extend(evidence_for_value(scan, value, f"component value for {component['name']}"))
        if hits or value_hits:
            component_hits.append({"component": component["name"], "hits": hits, "evidence": value_hits[:3]})
    component_score = cap_score(15, len(component_hits) / max(1, len(reference["components"])))
    add_cat("F", "Component Pattern Match", component_score, f"Matched evidence for {len(component_hits)} of {len(reference['components'])} documented components.", [{"path": "source scan", "detail": f"{c['component']}: words={', '.join(c['hits']) or 'value match'}"} for c in component_hits[:8]] + [ev for c in component_hits for ev in c["evidence"]][:5], [] if component_score >= 10 else ["Documented component patterns are weakly represented."])

    layout_terms = extract_layout_terms(reference)
    layout_hits = contains_any(scan, layout_terms)
    layout_value_evidence = [ev for v in reference["layout_tokens"].values() for ev in evidence_for_value(scan, v, "layout value")]
    layout_score = cap_score(10, min(1, len(layout_hits) / max(1, len(layout_terms)) * 0.5 + len(layout_value_evidence) / max(1, len(reference["layout_tokens"])) * 0.5))
    add_cat("G", "Layout and Density Match", layout_score, f"Found {len(layout_hits)} layout terms and {len(layout_value_evidence)} layout values.", [{"path": "source scan", "detail": "Layout terms: " + ", ".join(layout_hits[:12])}] + layout_value_evidence[:6], [] if layout_score >= 7 else ["Layout model and density require manual review."])

    visual_terms = extract_visual_terms(reference)
    visual_hits = contains_any(scan, visual_terms)
    asset_hits = contains_any(scan, ["img", "image", "picture", "background-image", "gradient", ".png", ".jpg", ".webp", ".svg"])
    visual_score = cap_score(5, min(1, (len(visual_hits) / max(1, len(visual_terms))) * 0.6 + (1 if asset_hits else 0) * 0.4))
    add_cat("H", "Imagery and Visual Language", visual_score, f"Found {len(visual_hits)} visual-language terms and asset/media signals: {', '.join(asset_hits[:6]) or 'none'}.", [{"path": "source scan", "detail": "Visual terms: " + ", ".join(visual_hits[:10])}], ["Confirm asset relevance and visual quality with screenshots."])

    dont_violations = detect_dont_violations(reference, scan)
    dont_score = max(0, 5 - len(dont_violations))
    risks.extend({"severity": "medium", "title": v["title"], "evidence": v["evidence"]} for v in dont_violations)
    add_cat("I", "Explicit Don't Violation Control", dont_score, f"Detected {len(dont_violations)} possible Don't-rule conflicts.", [{"path": v.get("path", "source scan"), "detail": v["evidence"]} for v in dont_violations[:8]], [] if dont_violations else ["Some prose Don't rules may require manual review."])

    for cat in categories:
        if cat["score"] < cat["points"] * 0.65:
            actions.append({
                "priority": min(100, 70 + cat["points"]),
                "effort": "M" if cat["points"] >= 10 else "S",
                "impact": "H" if cat["points"] >= 10 else "M",
                "action": f"Improve {cat['name']} by mapping missing Refero rules to concrete CSS/component changes.",
                "evidence": cat["rationale"],
            })
    if not actions:
        actions.append({"priority": 70, "effort": "S", "impact": "M", "action": "Run browser screenshot review to close manual visual gaps.", "evidence": "Source scan cannot verify rendered composition."})

    total = sum(c["score"] for c in categories)
    return {
        "schema_version": "1.0",
        "target": scan["root"],
        "reference": {
            "path": reference["path"],
            "brand": reference["brand"],
            "theme": reference["theme"],
            "sections_detected": reference["sections_detected"],
        },
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "score": total,
        "grade": grade(total),
        "mode": "heuristic source scan + manual visual review",
        "categories": categories,
        "extracted_rules": summarize_rules(reference),
        "risks": risks,
        "actions": sorted(actions, key=lambda x: x["priority"], reverse=True)[:8],
        "extraction_gaps": scan["extraction_gaps"][:40],
        "manual_review_gaps": manual_gaps,
    }


def flatten_evidence(matches):
    out = []
    for m in matches:
        out.extend(m["evidence"])
    return out


def extract_layout_terms(reference):
    text = " ".join([reference.get("layout", ""), " ".join(reference.get("layout_tokens", {}).keys())]).lower()
    candidates = ["full-bleed", "contained", "max-width", "grid", "two-column", "centered", "sticky", "section", "card", "navigation", "density", "hero"]
    return [c for c in candidates if c in text] or candidates[:6]


def extract_visual_terms(reference):
    text = reference.get("imagery", "").lower()
    candidates = ["image", "gradient", "product", "screenshot", "photo", "photography", "texture", "render", "icon", "illustration", "mockup", "dark", "light"]
    return [c for c in candidates if c in text] or ["image", "gradient", "product", "icon"]


def detect_dont_violations(reference, scan):
    violations = []
    lower = scan["lower"]
    dont_text = " ".join(reference["dont_rules"]).lower()
    if "gradient" in dont_text and ("do not" in dont_text or "avoid" in dont_text or "refrain" in dont_text) and "gradient(" in lower:
        violations.append({"title": "Gradient usage may conflict with Don't rule", "evidence": "Reference discourages gradients but source contains gradient()."})
    if "shadow" in dont_text and ("do not" in dont_text or "avoid" in dont_text or "refrain" in dont_text) and "box-shadow" in lower:
        violations.append({"title": "Shadow usage may conflict with Don't rule", "evidence": "Reference discourages shadows but source contains box-shadow."})
    if "generic blue" in dont_text and re.search(r"#[0-9a-f]{0,2}(?:00|33|3b|06)[0-9a-f]{2}(?:ff|fd|f6|d4)\b", lower):
        violations.append({"title": "Generic blue risk", "evidence": "Reference warns against generic blue and source contains blue-like hex values."})
    if "system fonts" in dont_text and ("system-ui" in lower or "sans-serif" in lower):
        violations.append({"title": "System font risk", "evidence": "Reference discourages generic system fonts and source contains system-ui/sans-serif."})
    return violations


def summarize_rules(reference):
    return {
        "brand": reference["brand"],
        "theme": reference["theme"],
        "colors": [{"name": c["name"], "value": c["value"], "token": c["token"], "role": c["role"]} for c in reference["colors"][:20]],
        "primary_fonts": [{"name": f["name"], "token": f["token"]} for f in reference["fonts"]],
        "type_tokens": [t["token"] for t in reference["type_scale"]],
        "spacing_tokens": [s["token"] for s in reference["spacing"]],
        "radii": reference["radii"],
        "layout_tokens": reference["layout_tokens"],
        "components": [c["name"] for c in reference["components"]],
        "do_count": len(reference["do_rules"]),
        "dont_count": len(reference["dont_rules"]),
    }


def grade(score_value):
    if score_value >= 85:
        return "Reference-Aligned"
    if score_value >= 70:
        return "Mostly Aligned"
    if score_value >= 55:
        return "Partially Aligned"
    if score_value >= 35:
        return "Drift Risk"
    return "Reference Not Followed"


def print_markdown(result):
    print(f"# Refero Design Adherence: {result['score']}/100 ({result['grade']})")
    print(f"- Reference: {result['reference']['path']}")
    print(f"- Target: {result['target']}")
    print(f"- Brand: {result['reference']['brand']} / theme: {result['reference']['theme']}")
    print("\n## Categories")
    for cat in result["categories"]:
        print(f"- {cat['name']}: {cat['score']}/{cat['points']} — {cat['rationale']}")
    print("\n## Top Actions")
    for action in result["actions"][:3]:
        print(f"- P{action['priority']} [{action['effort']}/{action['impact']}]: {action['action']}")
    if result["risks"]:
        print("\n## Risks")
        for risk in result["risks"][:5]:
            print(f"- {risk['severity']}: {risk['title']} — {risk['evidence']}")


def main():
    parser = argparse.ArgumentParser(description="Score frontend adherence to a Refero design reference.")
    parser.add_argument("target", help="Project or frontend path to scan")
    parser.add_argument("--reference", required=True, help="Refero style reference markdown file")
    parser.add_argument("--json", dest="json_path", help="Write score JSON to this path")
    parser.add_argument("--markdown", action="store_true", help="Print markdown summary")
    args = parser.parse_args()

    reference = parse_reference(args.reference)
    scan = scan_project(args.target)
    result = score(reference, scan)

    if args.json_path:
        out = Path(args.json_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.markdown or not args.json_path:
        print_markdown(result)


if __name__ == "__main__":
    main()
