#!/usr/bin/env python3
"""Monetization Cartography - project revenue-readiness signal scanner."""
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
    "A": ("Customer & Buyer Clarity", 15, ("icp", "buyer", "persona", "segment", "customer", "user", "founder", "sales lead", "agency")),
    "B": ("Pain Severity & Willingness To Pay", 15, ("pain", "urgent", "roi", "hours per week", "willingness to pay", "paid pilot", "loi", "budget", "manual")),
    "C": ("Pricing & Packaging", 15, ("pricing", "price", "subscription", "monthly", "annual", "starter", "team", "enterprise", "seat", "package")),
    "D": ("Revenue Evidence & Traction", 15, ("mrr", "arr", "revenue", "paid", "pilot", "loi", "customer interviews", "contract", "conversion", "retention")),
    "E": ("Unit Economics & Margin", 15, ("cac", "ltv", "payback", "gross margin", "margin", "cost to serve", "arpu", "acv", "churn")),
    "F": ("Distribution & Conversion Path", 15, ("distribution", "channel", "marketplace", "partner", "sales", "funnel", "trial", "conversion", "website")),
    "G": ("Revenue Experiment Readiness", 10, ("experiment", "onboarding", "waitlist", "preorder", "landing page", "checkout", "billing", "stripe", "next test")),
}

METRIC_RE = re.compile(r"(?i)(\$?\d+(?:\.\d+)?\s?(?:k|m|b|mm|bn|%|x)?|mrr|arr|cac|ltv|arpu|acv|payback|gross margin|churn)")
BUYER_RE = re.compile(r"(?i)\b(buyer|economic buyer|payer|budget owner|vp sales|founder|procurement|revops lead|agency partner)\b")
PRICE_RE = re.compile(r"(?i)(\$\s?\d+(?:\.\d+)?(?:\s?[kmb])?(?:\s?/\s?(?:month|mo|year|yr|seat|user))?|\b\d+(?:\.\d+)?\s?(?:usd|krw|eur|gbp|per month|per year|/month|/mo|/year|/yr)\b)")
REVENUE_PROOF_RE = re.compile(r"(?i)\b(mrr|arr|paid pilot|paid pilots|paid customer|paid customers|loi|lois|contract|contracts|renewal|retention|pipeline)\b")
ECONOMICS_RE = re.compile(r"(?i)\b(cac|ltv|payback|gross margin|cost to serve|arpu|acv|churn)\b")
PAIN_PROOF_RE = re.compile(r"(?i)\b(pain|urgent|expensive|risk|saved labor|hours per week|manual work|roi)\b")
EXPERIMENT_PROOF_RE = re.compile(r"(?i)\b(next experiment|next test|checkout|billing|stripe|preorder|paid onboarding|paid pilot|paid pilots|waitlist qualification)\b")
NEGATED_PROOF_SENTENCE_RE = re.compile(r"(?is)(?:^|[.!?\n])\s*(?:no|not|without)\b[^.!?\n]*(?:payer|price|paid|checkout|contract|mrr|arr|cac|margin|conversion)[^.!?\n]*")


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
    if total >= 85:
        return "Monetization-Ready", "green"
    if total >= 70:
        return "Revenue Experiment Ready", "green"
    if total >= 55:
        return "Monetization Hypothesis Formed", "amber"
    if total >= 35:
        return "Revenue Evidence Thin", "amber"
    return "Not Yet Monetizable", "red"


def term_count(text: str, term: str) -> int:
    escaped = re.escape(term.lower())
    pattern = escaped if re.search(r"[^a-z0-9]", term.lower()) else rf"\b{escaped}\b"
    return len(re.findall(pattern, text))


def term_present(text: str, term: str) -> bool:
    return term_count(text, term) > 0


def score_keyword_coverage(max_points: int, hit_count: int, file_count: int, metric_count: int) -> int:
    raw = round(hit_count * 1.35 + file_count * 1.8 + min(metric_count, 10) * 0.55)
    return int(min(max_points, raw))


def proof_signals(text: str) -> dict[str, bool]:
    positive_text = NEGATED_PROOF_SENTENCE_RE.sub(" ", text)
    return {
        "buyer": bool(BUYER_RE.search(positive_text)),
        "price": bool(PRICE_RE.search(positive_text)),
        "revenue": bool(REVENUE_PROOF_RE.search(positive_text)),
        "economics": bool(ECONOMICS_RE.search(positive_text)),
        "pain": bool(PAIN_PROOF_RE.search(positive_text)),
        "experiment": bool(EXPERIMENT_PROOF_RE.search(positive_text)),
    }


def apply_evidence_floor(category: str, score_value: int, signals: dict[str, bool]) -> tuple[int, list[str]]:
    missing: list[str] = []
    cap = score_value
    if category == "A" and not signals["buyer"]:
        cap = min(cap, 4)
        missing.append("concrete buyer or payer")
    elif category == "B" and not (signals["pain"] and (signals["price"] or signals["revenue"])):
        cap = min(cap, 5)
        missing.append("pain plus willingness-to-pay proof")
    elif category == "C" and not signals["price"]:
        cap = min(cap, 4)
        missing.append("concrete price point or paid SKU")
    elif category == "D" and not signals["revenue"]:
        cap = min(cap, 4)
        missing.append("revenue, LOI, contract, or paid-pilot proof")
    elif category == "E" and not signals["economics"]:
        cap = min(cap, 5)
        missing.append("unit economics or margin proof")
    elif category == "F" and not signals["buyer"]:
        cap = min(cap, 6)
        missing.append("buyer-specific distribution path")
    elif category == "G" and not signals["experiment"]:
        cap = min(cap, 3)
        missing.append("concrete revenue experiment")
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
        metrics = METRIC_RE.findall(text)
        documents.append({"path": rel(target, path), "text": lowered, "metrics": metrics[:20]})
        all_text_parts.append(lowered)

    combined = "\n".join(all_text_parts)
    signals = proof_signals(combined)
    categories: dict[str, CategoryScore] = {}
    actions: list[Action] = []
    manual_review_checks: list[str] = []
    total_keyword_hits = 0

    for key, (name, maximum, keywords) in CATEGORIES.items():
        keyword_hits = sum(term_count(combined, term) for term in keywords)
        total_keyword_hits += keyword_hits
        files_with_hits = sorted({doc["path"] for doc in documents if any(term_present(doc["text"], term) for term in keywords)})
        metric_count = sum(len(doc["metrics"]) for doc in documents if doc["path"] in files_with_hits)
        score_value = score_keyword_coverage(maximum, keyword_hits, len(files_with_hits), metric_count)
        score_value, missing_proof = apply_evidence_floor(key, score_value, signals)
        findings: list[str] = []
        if files_with_hits:
            findings.append(f"Evidence appears in {len(files_with_hits)} file(s): {', '.join(files_with_hits[:3])}.")
        if metric_count:
            findings.append(f"Metric-like revenue evidence detected {metric_count} time(s).")
        if missing_proof and keyword_hits:
            findings.append(f"Keyword hits need manual review because {missing_proof[0]} is missing.")
            manual_review_checks.append(f"{key} {name}: verify evidence path and {missing_proof[0]}.")
        if score_value < maximum * 0.5:
            findings.append("Evidence is thin; validate this monetization category before treating revenue potential as proven.")
            add_action(
                actions,
                f"Run a focused revenue experiment for {name}",
                key,
                "M",
                4,
                "Turns a weak monetization assumption into observable buyer behavior.",
                maximum - score_value + 5,
            )
        categories[key] = CategoryScore(
            name=name,
            score=score_value,
            max=maximum,
            evidence={"keyword_hits": keyword_hits, "files": files_with_hits[:8], "metric_hits": metric_count},
            findings=findings,
        )

    metric_hits: list[dict[str, str]] = []
    for doc in documents:
        for metric in doc["metrics"][:5]:
            metric_hits.append({"path": doc["path"], "metric": metric})

    if not documents:
        add_action(actions, "Provide machine-readable project, customer, pricing, or revenue documents", "A", "S", 1, "Enables evidence-based monetization scoring instead of filename-only review.", 10)
    if extraction_failures:
        add_action(actions, "Convert unreadable PDFs or scans to text", "A", "S", 2, "Prevents false negatives from missing revenue or customer evidence.", 8)
    if not metric_hits:
        add_action(actions, "Add a revenue metrics appendix", "D", "S", 2, "Makes price, conversion, margin, and traction assumptions reviewable.", 9)
    if not signals["buyer"]:
        add_action(actions, "Close the buyer and payer unknowns", "A", "S", 2, "Names who pays, who uses the product, and what purchase trigger creates budget.", 12)
    if not signals["price"]:
        add_action(actions, "Fill the pricing gap with one testable paid offer", "C", "S", 2, "Turns monetization language into a concrete price, package, and conversion ask.", 12)
    if not signals["revenue"]:
        add_action(actions, "Fill the revenue proof gap", "D", "M", 4, "Separates real buyer behavior from generic revenue, traction, or marketing language.", 12)
    if categories["G"].score >= 5:
        add_action(actions, "Prioritize the next monetization experiment", "G", "S", 1.5, "Moves from evidence review to a measurable revenue test with buyer behavior.", 9)

    actions.sort(key=lambda action: action.priority, reverse=True)
    total = sum(category.score for category in categories.values())
    grade_name, grade_color = grade(total)
    if total >= 70:
        manual_review_checks.append("High score: require evidence paths plus concrete buyer, price, and revenue proof before presenting as monetization-ready.")
    if total_keyword_hits >= 24:
        manual_review_checks.append("Keyword-dense target: check duplicated or generic revenue language before trusting the score.")
    if not (signals["buyer"] and signals["price"] and signals["revenue"]):
        manual_review_checks.append("Core proof gap: buyer, price, and revenue evidence are not all present.")
    manual_review_required = bool(manual_review_checks)
    if manual_review_required:
        add_action(actions, "Manually review buyer, price, and revenue proof", "D", "S", 1.5, "Prevents keyword-dense documents from being treated as stronger evidence than they are.", 10)
        actions.sort(key=lambda action: action.priority, reverse=True)
    weakest = sorted(categories.items(), key=lambda item: item[1].score / item[1].max)[:2]
    strongest = sorted(categories.items(), key=lambda item: item[1].score / item[1].max, reverse=True)[:2]

    return {
        "meta": {
            "project": target.stem if target.is_file() else target.name,
            "scored_at": datetime.now(timezone.utc).date().isoformat(),
            "files_total": len(files),
            "documents_scored": len(documents),
            "score_mode": "heuristic baseline + manual monetization review",
        },
        "total": total,
        "grade": grade_name,
        "grade_color": grade_color,
        "categories": {key: asdict(value) for key, value in categories.items()},
        "insights": [
            "Strongest monetization signals: " + ", ".join(f"{key} {cat.name}" for key, cat in strongest) + ".",
            "Weakest monetization gaps: " + ", ".join(f"{key} {cat.name}" for key, cat in weakest) + ".",
        ],
        "actions": [asdict(action) for action in actions[:12]],
        "extras": {
            "metric_hits": metric_hits[:50],
            "evidence_files": [doc["path"] for doc in documents],
            "extraction_failures": extraction_failures[:50],
            "proof_signals": signals,
            "manual_review_required": manual_review_required,
            "manual_review_checks": manual_review_checks[:12],
        },
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [f"# Monetization Cartography: {report['meta']['project']}", "", f"Score: {report['total']}/100 - {report['grade']}", ""]
    lines.append("## Categories")
    for key, category in report["categories"].items():
        lines.append(f"- {key}. {category['name']}: {category['score']}/{category['max']}")
    lines.extend(["", "## Top Monetization Actions"])
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
