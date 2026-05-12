#!/usr/bin/env python3
"""Mission Cartography - mission clarity and alignment signal scanner."""
from __future__ import annotations

import argparse
import json
import os
import re
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


IGNORE_DIRS = {".git", "node_modules", ".cache", "__pycache__", ".venv", "venv", "dist", "build"}
TEXT_EXTS = {".md", ".txt", ".csv", ".tsv", ".json", ".html", ".htm"}
ARCHIVE_TEXT_EXTS = {".docx", ".pptx", ".xlsx"}

CATEGORIES: dict[str, tuple[str, int, tuple[str, ...]]] = {
    "A": ("Mission Clarity & Specificity", 18, ("mission", "purpose", "north star", "why we exist", "vision", "intended change", "outcome")),
    "B": ("Audience & Stakeholder Definition", 14, ("target user", "customer", "stakeholder", "beneficiary", "persona", "segment", "buyer", "community", "audience")),
    "C": ("Problem Evidence & Urgency", 16, ("problem", "pain", "urgency", "urgent", "unmet need", "evidence", "interview", "research", "survey", "complaint", "risk")),
    "D": ("Product & Roadmap Alignment", 18, ("roadmap", "feature", "priority", "use case", "workflow", "value proposition", "scope", "release", "product")),
    "E": ("Strategic Trade-off Power", 12, ("principle", "focus", "not doing", "trade-off", "tradeoff", "prioritization", "decision criteria", "constraint", "strategy")),
    "F": ("Measurement & Feedback Loops", 12, ("kpi", "metric", "okr", "north-star metric", "success criteria", "feedback loop", "retention", "adoption", "cohort")),
    "G": ("Narrative Consistency Across Artifacts", 10, ("mission", "purpose", "north star", "vision", "why we exist")),
}

MISSION_RE = re.compile(r"(?im)^\s{0,3}(?:#+\s*)?(mission|purpose|north star|why we exist|vision)\b[:\s-]*(.{0,220})$")
AUDIENCE_RE = re.compile(r"(?i)\b(target users?|customers?|beneficiar(?:y|ies)|stakeholders?|personas?|segments?|buyers?|community|founders?|students?|teams?|developers?)\b")
PROBLEM_RE = re.compile(r"(?i)\b(problem|pain|urgent|urgency|unmet need|research|interviews?|survey|complaints?|support tickets?|risk|evidence)\b")
PRODUCT_RE = re.compile(r"(?i)\b(roadmap|features?|product|workflow|use cases?|priorit(?:y|ies)|release|scope|value proposition)\b")
TRADEOFF_RE = re.compile(r"(?i)\b(not doing|will not|trade-?offs?|prioritization|decision criteria|principles?|constraints?|focus|strategy)\b")
MEASURE_RE = re.compile(r"(?i)\b(kpis?|metrics?|okrs?|north-star metric|success criteria|feedback loops?|retention|adoption|cohorts?|activation|survey)\b")
GENERIC_SLOGAN_RE = re.compile(r"(?i)\b(empower|transform|revolutionize|impactful|world-class|seamless|innovative|next-generation|unlock)\b")


@dataclass
class CategoryScore:
    name: str
    score: int
    max: int
    evidence: dict[str, Any] = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)


@dataclass
class Action:
    title: str
    category: str
    effort: str
    effort_hours: float
    impact: str
    impact_score: int
    priority: float


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def walk_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    out: list[Path] = []
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        for file_name in files:
            out.append(Path(current) / file_name)
    return out


def rel(root: Path, path: Path) -> str:
    base = root if root.is_dir() else root.parent
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def zip_xml_text(path: Path, prefix: str) -> str:
    chunks: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if not name.startswith(prefix) or not name.endswith(".xml"):
                    continue
                try:
                    root = ElementTree.fromstring(archive.read(name))
                except Exception:
                    continue
                chunks.extend(node.text or "" for node in root.iter() if node.text)
    except Exception:
        return ""
    return " ".join(chunks)


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTS:
        return read_text(path)
    if suffix == ".docx":
        return zip_xml_text(path, "word/")
    if suffix == ".pptx":
        return zip_xml_text(path, "ppt/slides/")
    if suffix == ".xlsx":
        return zip_xml_text(path, "xl/")
    if suffix == ".pdf":
        raw = read_text(path)
        return raw if len(raw.strip()) > 100 else ""
    return ""


def grade(total: int) -> tuple[str, str]:
    if total >= 90:
        return "Mission-Led", "green"
    if total >= 75:
        return "Mission-Aligned", "green"
    if total >= 60:
        return "Mission-Formed", "amber"
    if total >= 40:
        return "Mission-Fragile", "amber"
    return "Mission-Drifting", "red"


def term_count(text: str, term: str) -> int:
    escaped = re.escape(term.lower())
    pattern = escaped if re.search(r"[^a-z0-9]", term.lower()) else rf"\b{escaped}\b"
    return len(re.findall(pattern, text))


def term_present(text: str, term: str) -> bool:
    return term_count(text, term) > 0


def mission_statements(documents: list[dict[str, Any]]) -> list[dict[str, str]]:
    statements: list[dict[str, str]] = []
    for doc in documents:
        for match in MISSION_RE.finditer(doc["raw"]):
            text = " ".join(part.strip(" :-") for part in match.groups() if part.strip())
            statements.append({"path": doc["path"], "statement": text[:260]})
    return statements


def proof_signals(combined: str, statements: list[dict[str, str]], mission_files: set[str]) -> dict[str, bool | int]:
    return {
        "mission": bool(statements) or bool(re.search(r"(?i)\b(mission|purpose|north star|why we exist)\b", combined)),
        "specific_mission": any(len(item["statement"].split()) >= 8 for item in statements),
        "audience": bool(AUDIENCE_RE.search(combined)),
        "problem": bool(PROBLEM_RE.search(combined)),
        "product": bool(PRODUCT_RE.search(combined)),
        "tradeoff": bool(TRADEOFF_RE.search(combined)),
        "measure": bool(MEASURE_RE.search(combined)),
        "repeated_mission": len(mission_files) >= 2,
        "generic_slogan": bool(GENERIC_SLOGAN_RE.search(" ".join(item["statement"] for item in statements))),
    }


def score_keyword_coverage(max_points: int, hit_count: int, file_count: int, direct_count: int) -> int:
    raw = round(hit_count * 1.1 + file_count * 1.9 + min(direct_count, 10) * 1.2)
    return int(min(max_points, raw))


def apply_evidence_floor(category: str, score_value: int, signals: dict[str, bool | int]) -> tuple[int, list[str]]:
    missing: list[str] = []
    cap = score_value
    if category == "A":
        if not signals["mission"]:
            cap = min(cap, 3)
            missing.append("explicit mission or purpose statement")
        elif not signals["specific_mission"]:
            cap = min(cap, 9)
            missing.append("specific mission sentence with concrete intended change")
        else:
            cap = max(cap, 12)
    elif category == "B" and not signals["audience"]:
        cap = min(cap, 4)
        missing.append("named target user, beneficiary, or stakeholder")
    elif category == "B":
        cap = max(cap, 8)
    elif category == "C" and not signals["problem"]:
        cap = min(cap, 4)
        missing.append("problem evidence or urgency")
    elif category == "D" and not (signals["mission"] and signals["product"]):
        cap = min(cap, 6)
        missing.append("explicit mission-to-product or roadmap link")
    elif category == "E" and not signals["tradeoff"]:
        cap = min(cap, 4)
        missing.append("trade-off, focus, or prioritization criteria")
    elif category == "F" and not signals["measure"]:
        cap = min(cap, 3)
        missing.append("mission metric or feedback loop")
    elif category == "G" and not signals["repeated_mission"]:
        cap = min(cap, 4)
        missing.append("mission narrative repeated across multiple artifacts")
    return cap, missing


def add_action(actions: list[Action], title: str, category: str, effort: str, hours: float, impact: str, impact_score: int) -> None:
    actions.append(Action(title, category, effort, hours, impact, impact_score, round(impact_score / hours, 2)))


def score(target: Path) -> dict[str, Any]:
    files = walk_files(target)
    supported = [p for p in files if p.suffix.lower() in TEXT_EXTS | ARCHIVE_TEXT_EXTS | {".pdf"}]
    documents: list[dict[str, Any]] = []
    extraction_failures: list[str] = []
    all_text_parts: list[str] = []

    for path in supported:
        text = extract_text(path)
        if not text.strip():
            extraction_failures.append(rel(target, path))
            continue
        lowered = text.lower() + " " + path.name.lower()
        documents.append({"path": rel(target, path), "text": lowered, "raw": text})
        all_text_parts.append(lowered)

    combined = "\n".join(all_text_parts)
    statements = mission_statements(documents)
    mission_files = {item["path"] for item in statements}
    signals = proof_signals(combined, statements, mission_files)
    categories: dict[str, CategoryScore] = {}
    actions: list[Action] = []
    manual_review_checks: list[str] = []
    total_keyword_hits = 0

    direct_patterns = {
        "A": MISSION_RE,
        "B": AUDIENCE_RE,
        "C": PROBLEM_RE,
        "D": PRODUCT_RE,
        "E": TRADEOFF_RE,
        "F": MEASURE_RE,
        "G": MISSION_RE,
    }

    for key, (name, maximum, keywords) in CATEGORIES.items():
        keyword_hits = sum(term_count(combined, term) for term in keywords)
        total_keyword_hits += keyword_hits
        files_with_hits = sorted({doc["path"] for doc in documents if any(term_present(doc["text"], term) for term in keywords)})
        direct_count = sum(len(direct_patterns[key].findall(doc["raw"])) for doc in documents if doc["path"] in files_with_hits)
        score_value = score_keyword_coverage(maximum, keyword_hits, len(files_with_hits), direct_count)
        score_value, missing_proof = apply_evidence_floor(key, score_value, signals)
        findings: list[str] = []
        if files_with_hits:
            findings.append(f"Evidence appears in {len(files_with_hits)} file(s): {', '.join(files_with_hits[:3])}.")
        if direct_count:
            findings.append(f"Direct category evidence detected {direct_count} time(s).")
        if missing_proof and keyword_hits:
            findings.append(f"Keyword hits need manual review because {missing_proof[0]} is missing.")
            manual_review_checks.append(f"{key} {name}: verify {missing_proof[0]}.")
        if key == "A" and signals["generic_slogan"] and score_value >= maximum * 0.5:
            findings.append("Mission-like language includes generic slogan terms; verify specificity manually.")
            manual_review_checks.append("A Mission Clarity & Specificity: check for aspirational wording without concrete scope.")
        if score_value < maximum * 0.5:
            findings.append("Evidence is thin; validate this mission category before treating alignment as proven.")
            add_action(
                actions,
                f"Strengthen {name}",
                key,
                "M",
                4,
                "Improves mission clarity where the current evidence is too thin for confident decisions.",
                maximum - score_value + 5,
            )
        categories[key] = CategoryScore(
            name=name,
            score=score_value,
            max=maximum,
            evidence={"keyword_hits": keyword_hits, "files": files_with_hits[:8], "direct_hits": direct_count},
            findings=findings,
        )

    if not documents:
        add_action(actions, "Provide machine-readable mission, strategy, roadmap, or product documents", "A", "S", 1, "Enables evidence-based mission scoring instead of filename-only review.", 10)
    if extraction_failures:
        add_action(actions, "Convert unreadable PDFs or scans to text", "A", "S", 2, "Prevents false negatives from missing mission evidence.", 8)
    if not signals["mission"]:
        add_action(actions, "Write one explicit mission sentence", "A", "S", 1, "Creates a reviewable anchor for audience, problem, product, and metric alignment.", 16)
    if not signals["audience"]:
        add_action(actions, "Name the primary audience and stakeholder roles", "B", "S", 2, "Prevents the mission from becoming too broad to guide product decisions.", 12)
    if not signals["problem"]:
        add_action(actions, "Attach problem evidence to the mission", "C", "M", 3, "Connects the mission to real user pain, urgency, or research evidence.", 14)
    if not signals["product"]:
        add_action(actions, "Map top product capabilities to mission outcomes", "D", "M", 4, "Shows whether the roadmap actually advances the stated mission.", 13)
    if not signals["measure"]:
        add_action(actions, "Define 2-3 mission progress metrics", "F", "S", 2, "Makes mission progress measurable instead of purely narrative.", 12)
    if not actions:
        add_action(actions, "Run a focused mission review with product lead and target-user evidence", "A", "S", 2, "Confirms the high baseline score with human judgment on specificity, credibility, and trade-off usefulness.", 6)

    total = sum(category.score for category in categories.values())
    grade_name, grade_color = grade(total)
    actions_sorted = sorted(actions, key=lambda action: (-action.priority, action.category, action.title))
    high_risk_categories = [f"{key}. {cat.name}" for key, cat in categories.items() if cat.score < cat.max * 0.4]

    insights: list[str] = []
    if statements:
        insights.append(f"Mission-like statements found in {len(mission_files)} artifact(s).")
    else:
        insights.append("No explicit mission statement was found in extracted text.")
    if high_risk_categories:
        insights.append(f"Weakest evidence: {', '.join(high_risk_categories[:3])}.")
    if signals["measure"]:
        insights.append("Mission measurement or feedback-loop language is present.")

    return {
        "schema_version": "1.0",
        "target": str(target),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "score": total,
        "total": total,
        "grade": grade_name,
        "grade_color": grade_color,
        "mode": "heuristic baseline + manual mission review",
        "categories": {key: asdict(value) for key, value in categories.items()},
        "risks": [
            {"severity": "high", "title": item, "evidence": "Category score is below 40% of available points."}
            for item in high_risk_categories[:5]
        ],
        "actions": [asdict(action) for action in actions_sorted[:10]],
        "extraction_gaps": [{"path": item, "reason": "text extraction unavailable"} for item in extraction_failures],
        "insights": insights,
        "extras": {
            "mission_statements": statements[:8],
            "evidence_files": sorted({doc["path"] for doc in documents}),
            "extraction_failures": extraction_failures,
            "manual_review_required": bool(manual_review_checks) or bool(signals["generic_slogan"]) or total_keyword_hits > 40,
            "manual_review_checks": sorted(set(manual_review_checks)),
            "signals": signals,
        },
        "meta": {
            "project": target.name or str(target),
            "scored_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "files_total": len(files),
            "supported_files": len(supported),
            "documents_scored": len(documents),
            "score_mode": "heuristic baseline + manual mission review",
        },
    }


def print_markdown(report: dict[str, Any]) -> None:
    print(f"**Score**\n{report['total']}/100 - {report['grade']}")
    print(f"Mode: {report['mode']}\n")
    print("**Mission Read**")
    for insight in report.get("insights", [])[:2]:
        print(f"- {insight}")
    print("\n**Top Alignment Actions**")
    for action in report.get("actions", [])[:3]:
        print(f"- [{action['effort']}, priority {action['priority']}] {action['title']} - {action['impact']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target")
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    report = score(Path(args.target).resolve())
    if args.json_path:
        out = Path(args.json_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if args.markdown or not args.json_path:
        print_markdown(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
