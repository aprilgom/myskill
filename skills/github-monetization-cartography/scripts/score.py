#!/usr/bin/env python3
"""GitHub Monetization Cartography - repository evidence scanner."""
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


IGNORE_DIRS = {".git", "node_modules", ".cache", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}
TEXT_EXTS = {".md", ".txt", ".csv", ".tsv", ".json", ".html", ".htm", ".yml", ".yaml", ".toml", ".xml"}
ARCHIVE_TEXT_EXTS = {".docx", ".pptx", ".xlsx"}
DEFAULT_MAX_FILES = 500
MAX_TEXT_BYTES = 120_000

CATEGORIES: dict[str, tuple[str, int, tuple[str, ...]]] = {
    "A": ("Buyer & Use Case Clarity", 15, ("buyer", "economic buyer", "icp", "persona", "teams", "enterprise", "agency", "use case", "workflow", "customer", "procurement", "compliance")),
    "B": ("Demand Proxy Quality", 15, ("stars", "forks", "downloads", "dependents", "adoption", "production", "users", "community", "issues", "discussions", "feature request", "popular", "integrations")),
    "C": ("Productization Readiness", 15, ("install", "quickstart", "getting started", "docs", "documentation", "example", "demo", "release", "changelog", "semver", "docker", "api", "sdk")),
    "D": ("Monetization Path Fit", 15, ("hosted", "cloud", "saas", "pro", "enterprise", "support", "consulting", "license", "marketplace", "plugin", "managed", "commercial")),
    "E": ("Revenue Proof & Conversion Evidence", 15, ("pricing", "price", "paid", "sponsor", "sponsors", "stripe", "billing", "checkout", "contract", "paid pilot", "mrr", "arr", "subscription", "conversion")),
    "F": ("Maintenance Economics", 10, ("support", "sla", "maintainer", "maintenance", "triage", "backlog", "dependency", "security", "cost to serve", "roadmap", "issue template")),
    "G": ("Distribution Surface", 10, ("github marketplace", "marketplace", "npm", "pypi", "docker hub", "homebrew", "vscode", "jetbrains", "wordpress", "shopify", "integration", "website", "partner")),
    "H": ("Revenue Experiment Readiness", 5, ("waitlist", "landing page", "trial", "paid onboarding", "sponsor tier", "support tier", "enterprise intake", "checkout", "next experiment", "paid pilot")),
}

IMPORTANT_FILES = {
    "readme": re.compile(r"(^|/)readme(\.|$)", re.I),
    "funding": re.compile(r"(^|/)(funding\.yml|sponsors?\.md)$", re.I),
    "license": re.compile(r"(^|/)licen[sc]e(\.|$)", re.I),
    "package": re.compile(r"(^|/)(package\.json|pyproject\.toml|setup\.py|cargo\.toml|go\.mod|gemfile|composer\.json|dockerfile)$", re.I),
    "release": re.compile(r"(^|/)(changelog|changes|release-notes|releases)(\.|/|$)", re.I),
    "docs": re.compile(r"(^|/)(docs?|examples?|demo|samples?)(/|$)", re.I),
    "issues": re.compile(r"(^|/)\.github/(issue_template|pull_request_template|workflows)(/|$)", re.I),
}

METRIC_RE = re.compile(r"(?i)(\b\d{2,}(?:,\d{3})*\s?(?:stars|forks|downloads|users|customers|dependents|installs|issues|discussions)\b|\$\s?\d+(?:\.\d+)?(?:\s?[kmb])?(?:\s?/\s?(?:month|mo|year|yr|seat|user))?|\bmrr\b|\barr\b)")
BUYER_RE = re.compile(r"(?i)\b(buyer|economic buyer|budget owner|procurement|enterprise|team|agency|customer|compliance|security team|platform team|devops|revops)\b")
DEMAND_RE = re.compile(r"(?i)\b(stars?|forks?|downloads?|dependents?|installs?|production users?|adoption|feature requests?|discussions?|community)\b")
PRODUCT_RE = re.compile(r"(?i)\b(quickstart|getting started|install|docker|demo|examples?|api docs?|sdk|changelog|release|semver)\b")
PATH_RE = re.compile(r"(?i)\b(hosted|cloud|saas|enterprise|paid support|support plan|consulting|marketplace|plugin|managed|commercial license|dual licen[sc]e)\b")
REVENUE_RE = re.compile(r"(?i)\b(pricing|paid customers?|paid users?|paid pilots?|sponsors?|sponsor tiers?|stripe|billing|checkout|contract|mrr|arr|subscription|invoice|conversion)\b")
MAINT_RE = re.compile(r"(?i)\b(sla|support|maintainer|maintenance|triage|security policy|dependency|backlog|roadmap)\b")
DIST_RE = re.compile(r"(?i)\b(github marketplace|npm|pypi|docker hub|homebrew|vscode marketplace|jetbrains marketplace|integration|website|partner)\b")
EXPERIMENT_RE = re.compile(r"(?i)\b(waitlist|landing page|trial|paid onboarding|sponsor tier|support tier|enterprise intake|checkout|next experiment|paid pilot)\b")
NEGATED_REVENUE_RE = re.compile(r"(?is)\b(?:no|not|without)\b[^.!?\n]*(?:pricing|paid|sponsor|billing|checkout|contract|mrr|arr|revenue|support tier|paid pilot)[^.!?\n]*")
EDUCATIONAL_ARCHIVE_RE = re.compile(r"(?i)\b(interview|study guide|primer|tutorials?|learning resources?|papers?|reading list|awesome list|curated list|course|class exercise)\b")


@dataclass
class Category:
    id: str
    name: str
    points: int
    score: int
    rationale: str
    evidence: list[dict[str, str]] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)


@dataclass
class Action:
    priority: float
    effort: str
    impact: str
    action: str


def read_text(path: Path) -> str:
    try:
        with path.open("rb") as handle:
            data = handle.read(MAX_TEXT_BYTES + 1)
        return data[:MAX_TEXT_BYTES].decode("utf-8", errors="ignore")
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


def file_priority(path: Path) -> tuple[int, int, str]:
    normalized = str(path).lower()
    name = path.name.lower()
    if IMPORTANT_FILES["readme"].search(normalized):
        return (0, len(normalized), normalized)
    if IMPORTANT_FILES["funding"].search(normalized):
        return (1, len(normalized), normalized)
    if IMPORTANT_FILES["license"].search(normalized):
        return (2, len(normalized), normalized)
    if IMPORTANT_FILES["package"].search(normalized):
        return (3, len(normalized), normalized)
    if name in {"pricing.md", "pricing.json", "plans.ts", "plans.js", "billing.ts", "billing.tsx"}:
        return (4, len(normalized), normalized)
    if any(part in normalized for part in ("/pricing", "/billing", "/enterprise", "/ee/", "/cloud", "/marketplace", "/support")):
        return (5, len(normalized), normalized)
    if IMPORTANT_FILES["release"].search(normalized):
        return (6, len(normalized), normalized)
    if IMPORTANT_FILES["issues"].search(normalized):
        return (7, len(normalized), normalized)
    if IMPORTANT_FILES["docs"].search(normalized):
        return (8, len(normalized), normalized)
    return (20, len(normalized), normalized)


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
    if suffix in TEXT_EXTS or path.name.lower() in {"dockerfile", "gemfile", "makefile"}:
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


def term_count(text: str, term: str) -> int:
    escaped = re.escape(term.lower())
    pattern = escaped if re.search(r"[^a-z0-9]", term.lower()) else rf"\b{escaped}\b"
    return len(re.findall(pattern, text.lower()))


def grade(total: int) -> str:
    if total >= 85:
        return "Repo Monetization-Ready"
    if total >= 70:
        return "GitHub Revenue Experiment Ready"
    if total >= 55:
        return "Monetization Hypothesis Formed"
    if total >= 35:
        return "Repo Demand Evidence Thin"
    return "Not Yet Monetizable From Repo Evidence"


def collect_documents(target: Path, max_files: int = DEFAULT_MAX_FILES) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, int]]:
    files = sorted(walk_files(target), key=file_priority)
    documents: list[dict[str, Any]] = []
    extraction_gaps: list[dict[str, str]] = []
    inventory = {key: 0 for key in IMPORTANT_FILES}
    supported = TEXT_EXTS | ARCHIVE_TEXT_EXTS | {".pdf"}

    scanned_candidates = 0
    limit_reported = False
    for path in files:
        relative = rel(target, path)
        for key, pattern in IMPORTANT_FILES.items():
            if pattern.search(relative):
                inventory[key] += 1
        if path.suffix.lower() not in supported and path.name.lower() not in {"dockerfile", "gemfile", "makefile"}:
            continue
        scanned_candidates += 1
        if scanned_candidates > max_files:
            if not limit_reported:
                extraction_gaps.append({"path": str(target), "reason": f"scan limited to first {max_files} prioritized text/archive files"})
                limit_reported = True
            continue
        text = extract_text(path)
        if not text.strip():
            extraction_gaps.append({"path": relative, "reason": "text extraction unavailable"})
            continue
        documents.append({
            "path": relative,
            "text": f"{relative}\n{text}".lower(),
            "metrics": METRIC_RE.findall(text)[:20],
        })
    return documents, extraction_gaps, inventory


def signal_summary(combined: str, inventory: dict[str, int]) -> dict[str, bool]:
    positive_revenue_text = NEGATED_REVENUE_RE.sub(" ", combined)
    return {
        "buyer": bool(BUYER_RE.search(combined)),
        "demand": bool(DEMAND_RE.search(combined)),
        "product": bool(PRODUCT_RE.search(combined)) or inventory["package"] > 0,
        "path": bool(PATH_RE.search(combined)),
        "revenue": bool(REVENUE_RE.search(positive_revenue_text)) or inventory["funding"] > 0,
        "maintenance": bool(MAINT_RE.search(combined)) or inventory["issues"] > 0,
        "distribution": bool(DIST_RE.search(combined)) or inventory["package"] > 0,
        "experiment": bool(EXPERIMENT_RE.search(positive_revenue_text)),
        "license": inventory["license"] > 0,
        "educational_archive": bool(EDUCATIONAL_ARCHIVE_RE.search(combined)) and inventory["package"] == 0 and inventory["funding"] == 0,
    }


def keyword_score(max_points: int, keyword_hits: int, files_with_hits: int, metric_count: int, inventory_bonus: int = 0) -> int:
    raw = round(keyword_hits * 1.1 + files_with_hits * 1.7 + min(metric_count, 8) * 0.45 + inventory_bonus)
    return max(0, min(max_points, raw))


def evidence_for(documents: list[dict[str, Any]], keywords: tuple[str, ...], limit: int = 4) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    seen: set[str] = set()
    for doc in documents:
        hits = [term for term in keywords if term_count(doc["text"], term)]
        if not hits or doc["path"] in seen:
            continue
        detail = "signals: " + ", ".join(hits[:5])
        if doc["metrics"]:
            detail += "; metrics: " + ", ".join(doc["metrics"][:3])
        evidence.append({"path": doc["path"], "detail": detail})
        seen.add(doc["path"])
        if len(evidence) >= limit:
            break
    return evidence


def apply_caps(cat_id: str, score_value: int, signals: dict[str, bool]) -> tuple[int, list[str]]:
    gaps: list[str] = []
    capped = score_value
    if cat_id == "A" and not signals["buyer"]:
        capped = min(capped, 4)
        gaps.append("concrete buyer or budget owner")
    elif cat_id == "B" and not signals["demand"]:
        capped = min(capped, 5)
        gaps.append("repo-native demand proxy such as adoption, downloads, stars, issues, or dependents")
    elif cat_id == "C" and not signals["product"]:
        capped = min(capped, 5)
        gaps.append("installable product surface with docs, examples, or package metadata")
    elif cat_id == "D" and not signals["path"]:
        capped = min(capped, 5)
        gaps.append("credible paid path such as hosted, enterprise, marketplace, support, or plugin")
    elif cat_id == "E" and not signals["revenue"]:
        capped = min(capped, 4)
        gaps.append("direct revenue or conversion proof")
    elif cat_id == "F" and not signals["maintenance"]:
        capped = min(capped, 4)
        gaps.append("maintenance/support economics evidence")
    elif cat_id == "G" and not signals["distribution"]:
        capped = min(capped, 4)
        gaps.append("distribution channel beyond the repository")
    elif cat_id == "H" and not signals["experiment"]:
        capped = min(capped, 2)
        gaps.append("specific next paid experiment")
    return capped, gaps


def score_repository(target: Path, max_files: int = DEFAULT_MAX_FILES) -> dict[str, Any]:
    documents, extraction_gaps, inventory = collect_documents(target, max_files=max_files)
    combined = "\n".join(doc["text"] for doc in documents)
    positive_revenue_combined = NEGATED_REVENUE_RE.sub(" ", combined)
    signals = signal_summary(combined, inventory)
    categories: list[Category] = []
    total_keyword_hits = 0

    for cat_id, (name, maximum, keywords) in CATEGORIES.items():
        scoring_text = positive_revenue_combined if cat_id in {"D", "E", "H"} else combined
        keyword_hits = sum(term_count(scoring_text, term) for term in keywords)
        total_keyword_hits += keyword_hits
        files_with_hits = len({doc["path"] for doc in documents if any(term_count(NEGATED_REVENUE_RE.sub(" ", doc["text"]) if cat_id in {"D", "E", "H"} else doc["text"], term) for term in keywords)})
        metric_count = sum(len(doc["metrics"]) for doc in documents if any(term_count(NEGATED_REVENUE_RE.sub(" ", doc["text"]) if cat_id in {"D", "E", "H"} else doc["text"], term) for term in keywords))
        inventory_bonus = 0
        if cat_id == "C":
            inventory_bonus = min(4, inventory["package"] + inventory["docs"] + inventory["release"])
        elif cat_id == "E":
            inventory_bonus = min(3, inventory["funding"])
        elif cat_id == "F":
            inventory_bonus = min(3, inventory["issues"] + inventory["release"])
        raw_score = keyword_score(maximum, keyword_hits, files_with_hits, metric_count, inventory_bonus)
        final_score, gaps = apply_caps(cat_id, raw_score, signals)
        evidence = evidence_for(documents, keywords)
        rationale = f"{keyword_hits} keyword hits across {files_with_hits} files"
        if inventory_bonus:
            rationale += f"; repo inventory bonus {inventory_bonus}"
        categories.append(Category(cat_id, name, maximum, final_score, rationale, evidence, gaps))

    total = sum(cat.score for cat in categories)
    risks: list[dict[str, str]] = []
    if signals["demand"] and not signals["revenue"]:
        risks.append({"severity": "high", "title": "Popularity without monetization proof", "evidence": "Demand proxy terms appear, but direct revenue/conversion proof is absent."})
        total = min(total, 69)
    if signals["educational_archive"]:
        risks.append({"severity": "high", "title": "Educational/archive content can mimic business keywords", "evidence": "The repo looks like interview, tutorial, paper, or curated learning content without package or funding metadata; business terms may be examples rather than this repo's monetization path."})
        total = min(total, 54)
    if not signals["buyer"]:
        risks.append({"severity": "high", "title": "No clear economic buyer", "evidence": "Repository evidence does not identify a buyer or budget owner."})
        total = min(total, 55)
    if signals["revenue"] and not signals["path"]:
        risks.append({"severity": "medium", "title": "Revenue language lacks a clear paid path", "evidence": "Revenue terms appear without hosted, enterprise, support, marketplace, or plugin packaging evidence."})
    if not signals["license"]:
        risks.append({"severity": "medium", "title": "License path unclear", "evidence": "No license file was detected, so paid path fit needs manual review."})
    if total_keyword_hits > 120 or total >= 70:
        manual_review_required = True
    else:
        manual_review_required = bool(risks or extraction_gaps)

    actions = recommended_actions(categories, signals)
    return {
        "schema_version": "1.0",
        "target": str(target),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "score": int(total),
        "grade": grade(int(total)),
        "mode": "GitHub repo evidence baseline + manual monetization review",
        "manual_review_required": manual_review_required,
        "signals": signals,
        "repo_inventory": inventory,
        "categories": [asdict(cat) for cat in categories],
        "risks": risks,
        "actions": [asdict(action) for action in actions[:5]],
        "extraction_gaps": extraction_gaps,
        "metadata": {"documents_scanned": len(documents), "total_keyword_hits": total_keyword_hits},
    }


def recommended_actions(categories: list[Category], signals: dict[str, bool]) -> list[Action]:
    scores = {cat.id: cat.score / cat.points for cat in categories}
    actions: list[Action] = []
    if scores["A"] < 0.65:
        actions.append(Action(96, "M", "H", "Name the economic buyer and paid use case in the README, then tie top examples/issues to that buyer's workflow."))
    if signals["demand"] and not signals["revenue"]:
        actions.append(Action(94, "S", "H", "Convert demand proxy into a paid test: sponsor tiers, paid support intake, or paid pilot outreach to visible users."))
    if scores["D"] < 0.65:
        actions.append(Action(88, "M", "H", "Choose one paid path that fits the repo: hosted service, enterprise support, marketplace app, plugin, or commercial license."))
    if scores["C"] < 0.65:
        actions.append(Action(78, "M", "M", "Tighten productization with quickstart, demo, examples, release notes, and package metadata that support buyer evaluation."))
    if scores["F"] < 0.6:
        actions.append(Action(72, "S", "M", "Document support boundaries and turn recurring issue patterns into a paid support or managed-service wedge."))
    if scores["G"] < 0.6:
        actions.append(Action(68, "M", "M", "Add or improve a distribution surface such as package registry metadata, marketplace listing, integration docs, or buyer-facing website."))
    if not actions:
        actions.append(Action(82, "S", "H", "Run a narrow paid conversion test with the strongest visible user segment before expanding packaging."))
    return sorted(actions, key=lambda item: item.priority, reverse=True)


def markdown_report(result: dict[str, Any]) -> str:
    lines = [
        f"**Score**\n{result['score']}/100 - {result['grade']}",
        f"Mode: {result['mode']}",
        "",
        "**Top Risks**",
    ]
    if result["risks"]:
        lines.extend(f"- {risk['severity']}: {risk['title']}" for risk in result["risks"][:3])
    else:
        lines.append("- No high-priority risk detected by scanner.")
    lines.extend(["", "**Top Revenue Actions**"])
    lines.extend(f"- [{a['effort']}, priority {a['priority']}] {a['action']}" for a in result["actions"][:3])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path, required=True)
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES, help="Maximum prioritized text/archive files to scan")
    args = parser.parse_args()

    result = score_repository(args.target.resolve(), max_files=args.max_files)
    args.json_path.parent.mkdir(parents=True, exist_ok=True)
    args.json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.markdown:
        print(markdown_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
