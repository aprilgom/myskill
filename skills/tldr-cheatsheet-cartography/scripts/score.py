#!/usr/bin/env python3
"""Baseline scorer for TLDR cheat sheets."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Evidence:
    path: str
    detail: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def infer_source(tldr: Path) -> Path | None:
    name = tldr.name
    if name.endswith(".tldr.md"):
        return tldr.with_name(name.replace(".tldr.md", ".md"))
    return None


def strip_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    body = text[end + 4 :].lstrip()
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data, body


def headings(text: str) -> list[str]:
    return [m.group(2).strip() for m in re.finditer(r"^(#{1,6})\s+(.+?)\s*$", text, re.M)]


def code_blocks(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for m in re.finditer(r"```([A-Za-z0-9_+-]*)\n(.*?)\n```", text, re.S):
        blocks.append((m.group(1).strip(), m.group(2)))
    return blocks


def normalize_terms(title: str) -> set[str]:
    words = re.findall(r"[A-Za-z0-9가-힣_]+", title.lower())
    stop = {"the", "and", "or", "of", "to", "a", "an", "in", "with", "for", "및", "과", "와"}
    return {w for w in words if len(w) > 1 and w not in stop}


def grade(score: int) -> str:
    if score >= 90:
        return "Publish-Ready"
    if score >= 75:
        return "Strong With Minor Gaps"
    if score >= 60:
        return "Useful Draft"
    if score >= 40:
        return "Needs Editorial Pass"
    return "Not Yet a Cheat Sheet"


def category(id_: str, name: str, points: int, score: int, rationale: str, evidence: list[Evidence], gaps: list[str]):
    return {
        "id": id_,
        "name": name,
        "points": points,
        "score": max(0, min(points, score)),
        "rationale": rationale,
        "evidence": [e.__dict__ for e in evidence],
        "gaps": gaps,
    }


def score_file(tldr: Path, source: Path | None) -> dict:
    text = read_text(tldr)
    fm, body = strip_frontmatter(text)
    tldr_headings = headings(body)
    blocks = code_blocks(body)
    bullet_lines = re.findall(r"^\s*[-*]\s+", body, re.M)
    words = re.findall(r"\S+", body)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip() and not p.strip().startswith("```")]
    long_paragraphs = [p for p in paragraphs if len(re.findall(r"\S+", p)) > 80]
    todos = re.findall(r"TODO|FIXME|TBD|\[TODO", body, re.I)

    source_text = ""
    source_headings: list[str] = []
    extraction_gaps = []
    if source and source.exists():
        source_text = read_text(source)
        _, source_body = strip_frontmatter(source_text)
        source_headings = headings(source_body)
    elif source:
        extraction_gaps.append({"path": str(source), "reason": "paired source file not found"})

    heading_matches = 0
    if source_headings and tldr_headings:
        tldr_terms = [normalize_terms(h) for h in tldr_headings]
        for src in source_headings:
            src_terms = normalize_terms(src)
            if src_terms and any(src_terms & terms for terms in tldr_terms):
                heading_matches += 1
    coverage_ratio = heading_matches / len(source_headings) if source_headings else 0

    categories = []

    coverage_score = 8
    if source_headings:
        coverage_score = round(6 + min(14, coverage_ratio * 18))
    if len(words) < 80:
        coverage_score -= 6
    categories.append(category(
        "A",
        "Source Coverage & Prioritization",
        20,
        coverage_score,
        f"Matched {heading_matches}/{len(source_headings)} source headings by term overlap." if source_headings else "No paired source was available; coverage needs manual review.",
        [Evidence(str(tldr), f"{len(tldr_headings)} TLDR headings"), Evidence(str(source), f"{len(source_headings)} source headings")] if source else [Evidence(str(tldr), f"{len(tldr_headings)} TLDR headings")],
        ["Manual review required for renamed or intentionally collapsed sections."] + (["Paired source file missing."] if extraction_gaps else []),
    ))

    density = 16
    if len(words) < 120:
        density -= 6
    if len(words) > 1800:
        density -= 4
    if len(bullet_lines) < 5:
        density -= 4
    if len(long_paragraphs) > 1:
        density -= min(5, len(long_paragraphs) * 2)
    categories.append(category(
        "B",
        "Cheat Sheet Density & Scanability",
        16,
        density,
        f"{len(words)} words, {len(bullet_lines)} bullet lines, {len(long_paragraphs)} long paragraphs.",
        [Evidence(str(tldr), f"{len(words)} words")],
        ["Tighten long prose into grouped bullets."] if long_paragraphs else [],
    ))

    go_blocks = [b for lang, b in blocks if lang in {"go", "golang"}]
    tagged_blocks = [lang for lang, _ in blocks if lang]
    go_signal_count = sum(1 for _, b in blocks if re.search(r"\b(func|return|defer|for|if|type)\b", b))
    snippet_score = min(18, len(blocks) * 4 + len(go_blocks) * 2 + min(4, go_signal_count))
    if source_text and "```go" in source_text and not blocks:
        snippet_score = 2
    categories.append(category(
        "C",
        "Code Snippet Usefulness",
        18,
        snippet_score,
        f"{len(blocks)} code blocks, {len(go_blocks)} Go-tagged blocks, {len(tagged_blocks)} tagged blocks.",
        [Evidence(str(tldr), f"{len(blocks)} fenced code blocks")],
        ["Manual review must confirm snippets are correct and teach the source decisions."],
    ))

    correctness = 18
    if todos:
        correctness -= 5
    if any(len(b.splitlines()) > 45 for _, b in blocks):
        correctness -= 2
    if len(words) < 80:
        correctness -= 5
    categories.append(category(
        "D",
        "Correctness & Source Faithfulness",
        18,
        correctness,
        f"Found {len(todos)} placeholder markers and {sum(1 for _, b in blocks if len(b.splitlines()) > 45)} very long code blocks.",
        [Evidence(str(tldr), f"{len(todos)} TODO/FIXME/TBD markers")],
        ["Scanner cannot verify semantic correctness; compare against source manually."],
    ))

    cue_terms = re.findall(r"우선|사용|피하|avoid|prefer|when|if|should|must|주의|적합|중요", body, re.I)
    action_score = min(14, 4 + len(cue_terms))
    categories.append(category(
        "E",
        "Actionability & Decision Cues",
        14,
        action_score,
        f"Found {len(cue_terms)} action or decision cue terms.",
        [Evidence(str(tldr), f"{len(cue_terms)} decision cue terms")],
        ["Add explicit when-to-use and avoid guidance where source decisions are subtle."] if len(cue_terms) < 8 else [],
    ))

    integration = 8
    if not fm:
        integration -= 4
    if "build:" not in text or "render: never" not in text:
        integration -= 3
    categories.append(category(
        "F",
        "Integration With Site Conventions",
        8,
        integration,
        "Checked front matter and Hugo TLDR render convention.",
        [Evidence(str(tldr), "front matter present" if fm else "front matter missing")],
        ["Restore front matter with build.render: never."] if integration < 8 else [],
    ))

    maintainability = 6
    if len(words) > 2200:
        maintainability -= 3
    if len(blocks) > 12:
        maintainability -= 1
    if todos:
        maintainability -= 2
    categories.append(category(
        "G",
        "Maintainability & Edit Safety",
        6,
        maintainability,
        f"{len(words)} words and {len(blocks)} code blocks.",
        [Evidence(str(tldr), f"{len(words)} words")],
        ["Remove placeholders before publishing."] if todos else [],
    ))

    total = sum(c["score"] for c in categories)
    actions = []
    for c in categories:
        if c["score"] < c["points"] * 0.7:
            actions.append({
                "priority": round((c["points"] - c["score"]) / c["points"] * 100),
                "effort": "S" if c["points"] <= 8 else "M",
                "impact": "H" if c["points"] >= 18 else "M",
                "action": f"Improve {c['name']}: {c['gaps'][0] if c['gaps'] else c['rationale']}",
            })
    actions = sorted(actions, key=lambda a: a["priority"], reverse=True)[:5]

    return {
        "schema_version": "1.0",
        "target": str(tldr),
        "source": str(source) if source else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "score": total,
        "grade": grade(total),
        "mode": "heuristic baseline + manual cheatsheet review",
        "categories": categories,
        "risks": [
            {"severity": "medium", "title": "Semantic correctness requires manual review", "evidence": "Scanner checks structure and proxy signals only."}
        ],
        "actions": actions,
        "extraction_gaps": extraction_gaps,
    }


def print_markdown(result: dict) -> None:
    print(f"**Score**\n{result['score']}/100 - {result['grade']}")
    print(f"Mode: {result['mode']}\n")
    print("**Categories**")
    for c in result["categories"]:
        print(f"- {c['id']}. {c['name']}: {c['score']}/{c['points']} - {c['rationale']}")
    if result["actions"]:
        print("\n**Top Actions**")
        for i, action in enumerate(result["actions"][:3], 1):
            print(f"{i}. [{action['effort']}, priority {action['priority']}] {action['action']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tldr", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    source = args.source if args.source else infer_source(args.tldr)
    result = score_file(args.tldr, source)
    if args.json:
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown or not args.json:
        print_markdown(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
