#!/usr/bin/env python3
"""VC Evaluation Cartography - startup diligence signal scanner.

Usage:
    python score.py /path/to/data-room --json vc-evaluation-score.json
    python score.py /path/to/data-room --markdown

The scorer is intentionally heuristic. It collects repeatable evidence and
produces a baseline that should be manually reviewed with the VC rubric.
"""
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
    "A": ("Market Size & Timing", 15, ("tam", "sam", "som", "market", "cagr", "growth", "beachhead", "timing", "tailwind", "regulation")),
    "B": ("Problem Urgency & Customer Pain", 10, ("problem", "pain", "workflow", "customer interview", "icp", "buyer", "roi", "manual", "urgent")),
    "C": ("Product, Technology & Roadmap", 10, ("product", "demo", "roadmap", "technology", "model", "platform", "integration", "api", "patent", "ip")),
    "D": ("Traction & Customer Evidence", 15, ("arr", "mrr", "revenue", "growth", "retention", "churn", "customer", "pilot", "loi", "pipeline", "cohort", "usage")),
    "E": ("Business Model & Unit Economics", 10, ("pricing", "acv", "gross margin", "cac", "ltv", "payback", "subscription", "margin", "unit economics")),
    "F": ("Go-to-Market & Distribution", 10, ("gtm", "go-to-market", "sales", "channel", "partner", "funnel", "conversion", "sales cycle", "distribution")),
    "G": ("Team & Founder-Market Fit", 10, ("founder", "team", "hiring", "advisor", "domain expertise", "operator", "ex-", "background")),
    "H": ("Financial Plan & Fundraising Fit", 10, ("burn", "runway", "round", "valuation", "use of funds", "milestone", "raise", "financial model", "forecast")),
    "I": ("Moat, Competition & Defensibility", 5, ("competition", "competitor", "moat", "defensible", "differentiation", "switching cost", "network effect")),
    "J": ("Key Risks & Diligence Gaps", 5, ("risk", "dependency", "concentration", "legal", "security", "privacy", "compliance", "gap", "mitigation")),
}

METRIC_RE = re.compile(
    r"(?i)(\$?\d+(?:\.\d+)?\s?(?:k|m|b|mm|bn|%|x)?|arr|mrr|cac|ltv|acv|gmv|gross margin|retention|churn|runway|burn)"
)


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
        return "IC-Ready", "green"
    if total >= 75:
        return "Strong Diligence Candidate", "green"
    if total >= 60:
        return "Promising but Incomplete", "amber"
    if total >= 40:
        return "High-Risk / Needs Evidence", "amber"
    return "Not Yet Investable", "red"


def add_action(actions: list[Action], title: str, category: str, effort: str, hours: float, impact: str, impact_score: int) -> None:
    actions.append(Action(title, category, effort, hours, impact, impact_score, round(impact_score / hours, 2)))


def score_keyword_coverage(max_points: int, hit_count: int, file_count: int, metric_count: int) -> int:
    raw = min(max_points, round(hit_count * 1.4 + file_count * 1.7 + min(metric_count, 8) * 0.45))
    return int(raw)


def term_count(text: str, term: str) -> int:
    escaped = re.escape(term.lower())
    if re.search(r"[^a-z0-9]", term.lower()):
        pattern = escaped
    else:
        pattern = rf"\b{escaped}\b"
    return len(re.findall(pattern, text))


def term_present(text: str, term: str) -> bool:
    return term_count(text, term) > 0


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
        metric_hits = METRIC_RE.findall(text)
        documents.append({"path": rel(target, path), "text": lowered, "metrics": metric_hits[:20]})
        all_text_parts.append(lowered)

    combined = "\n".join(all_text_parts)
    actions: list[Action] = []
    categories: dict[str, CategoryScore] = {}

    for key, (name, maximum, keywords) in CATEGORIES.items():
        keyword_hits = sum(term_count(combined, term) for term in keywords)
        files_with_hits = sorted({doc["path"] for doc in documents if any(term_present(doc["text"], term) for term in keywords)})
        metric_count = sum(len(doc["metrics"]) for doc in documents if doc["path"] in files_with_hits)
        score_value = score_keyword_coverage(maximum, keyword_hits, len(files_with_hits), metric_count)
        findings: list[str] = []
        if files_with_hits:
            findings.append(f"Evidence appears in {len(files_with_hits)} file(s): {', '.join(files_with_hits[:3])}.")
        if metric_count:
            findings.append(f"Metric-like evidence detected {metric_count} time(s).")
        if score_value < maximum * 0.5:
            findings.append("Evidence is thin; manual diligence should validate this category before IC use.")
            add_action(
                actions,
                f"Fill evidence gap for {name}",
                key,
                "M",
                6,
                "Reduces IC uncertainty on a weak category before partner review.",
                maximum - score_value + 4,
            )
        categories[key] = CategoryScore(
            name=name,
            score=score_value,
            max=maximum,
            evidence={"keyword_hits": keyword_hits, "files": files_with_hits[:8], "metric_hits": metric_count},
            findings=findings,
        )

    total = sum(category.score for category in categories.values())
    grade_name, grade_color = grade(total)
    metric_hits = []
    for doc in documents:
        for metric in doc["metrics"][:5]:
            metric_hits.append({"path": doc["path"], "metric": metric})

    weakest = sorted(categories.items(), key=lambda item: item[1].score / item[1].max)[:2]
    strongest = sorted(categories.items(), key=lambda item: item[1].score / item[1].max, reverse=True)[:2]
    insights = [
        "Strongest signals: " + ", ".join(f"{key} {cat.name}" for key, cat in strongest) + ".",
        "Weakest diligence areas: " + ", ".join(f"{key} {cat.name}" for key, cat in weakest) + ".",
    ]

    if not documents:
        add_action(actions, "Provide machine-readable deck, memo, or data-room documents", "J", "S", 1, "Enables evidence-based scoring instead of filename-only review.", 10)
    if extraction_failures:
        add_action(actions, "Convert unreadable PDFs or scans to text", "J", "S", 2, "Prevents false negatives from missing deck, data-room, or financial-model evidence.", 8)
    if not metric_hits:
        add_action(actions, "Add a metrics appendix with current KPI values", "D", "S", 2, "Lets IC test traction, unit economics, and financing assumptions quickly.", 9)

    actions.sort(key=lambda action: action.priority, reverse=True)
    return {
        "meta": {
            "deal": target.stem if target.is_file() else target.name,
            "scored_at": datetime.now(timezone.utc).date().isoformat(),
            "files_total": len(files),
            "documents_scored": len(documents),
            "score_mode": "heuristic baseline + manual VC review",
        },
        "total": total,
        "grade": grade_name,
        "grade_color": grade_color,
        "categories": {key: asdict(value) for key, value in categories.items()},
        "insights": insights,
        "actions": [asdict(action) for action in actions[:12]],
        "extras": {
            "metric_hits": metric_hits[:50],
            "evidence_files": [doc["path"] for doc in documents],
            "extraction_failures": extraction_failures[:50],
        },
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [f"# VC Evaluation: {report['meta']['deal']}", "", f"Score: {report['total']}/100 - {report['grade']}", ""]
    lines.append("## Categories")
    for key, category in report["categories"].items():
        lines.append(f"- {key}. {category['name']}: {category['score']}/{category['max']}")
    lines.extend(["", "## Top Diligence Actions"])
    for action in report["actions"][:5]:
        lines.append(f"- [{action['effort']}, priority {action['priority']}] {action['title']} - {action['impact']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target")
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    report = score(target)
    if args.json_path:
        out = Path(args.json_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.markdown or not args.json_path:
        print(markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
