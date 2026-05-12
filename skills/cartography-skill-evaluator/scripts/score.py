#!/usr/bin/env python3
"""Baseline scorer for cartography-style skill folders."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CATEGORIES = {
    "cartography_contract_trigger_fit": ("Cartography Contract & Trigger Fit", 15),
    "rubric_design_quality": ("Rubric Design Quality", 20),
    "evidence_collection_scanner_fit": ("Evidence Collection & Scanner Fit", 15),
    "json_schema_output_stability": ("JSON Schema & Output Stability", 10),
    "dashboard_decision_usefulness": ("Dashboard Decision Usefulness", 10),
    "validation_integrity": ("Validation Integrity", 15),
    "roi_action_quality": ("ROI Action Quality", 10),
    "progressive_disclosure_maintainability": ("Progressive Disclosure & Maintainability", 5),
}


@dataclass
class Finding:
    severity: str
    title: str
    evidence: str
    fix: str


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def has_any(text: str, terms: list[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def extract_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip("\"'")
    return meta


def count_rubric_points(text: str) -> int | None:
    points = [int(match) for match in re.findall(r"\|\s*[^|\n]+\s*\|\s*[^|\n]+\s*\|\s*(\d{1,2})\s*\|", text)]
    if points:
        return sum(points)
    points = [int(match) for match in re.findall(r"\b(\d{1,2})\s*(?:points|pts|점)\b", text, re.IGNORECASE)]
    return sum(points) if points else None


def category(score: int, max_score: int, rationale: str, evidence: list[str], gaps: list[str]) -> dict[str, Any]:
    return {
        "score": max(0, min(score, max_score)),
        "max": max_score,
        "rationale": rationale,
        "evidence": evidence,
        "gaps": gaps,
    }


def evaluate(path: Path) -> dict[str, Any]:
    skill = path
    skill_md = skill / "SKILL.md"
    text = read_text(skill_md)
    all_text_parts = [text]
    files = {p.relative_to(skill).as_posix(): p for p in skill.rglob("*") if p.is_file()} if skill.exists() else {}
    generated_cache_files = [
        rel for rel in files
        if "__pycache__/" in rel or rel.endswith((".pyc", ".pyo"))
    ]
    for rel, file_path in files.items():
        if rel != "SKILL.md" and file_path.suffix in {".md", ".py", ".html", ".yaml", ".yml"}:
            all_text_parts.append(read_text(file_path))
    all_text = "\n".join(all_text_parts)
    document_text = "\n".join(
        [text]
        + [
            read_text(file_path)
            for rel, file_path in files.items()
            if rel.startswith("references/") and file_path.suffix == ".md"
        ]
    )
    meta = extract_frontmatter(text)
    findings: list[Finding] = []

    # A. Contract and trigger
    trigger_score = 0
    trigger_ev: list[str] = []
    trigger_gaps: list[str] = []
    desc = meta.get("description", "")
    if meta.get("name") and desc:
        trigger_score += 4
        trigger_ev.append("SKILL.md has name and description frontmatter")
    else:
        findings.append(Finding("P1", "Missing required frontmatter", "SKILL.md", "Add name and description frontmatter."))
        trigger_gaps.append("Missing complete frontmatter")
    if has_any(desc, ["cartography", "map", "dashboard", "score", "rubric"]):
        trigger_score += 4
        trigger_ev.append("Description includes cartography trigger cues")
    else:
        trigger_gaps.append("Description lacks cartography-specific trigger cues")
    if has_any(text, ["target", "decision", "evaluat", "assess", "score supports"]):
        trigger_score += 4
        trigger_ev.append("Workflow discusses target/decision/evaluation context")
    else:
        trigger_gaps.append("Target and decision context are unclear")
    if has_any(text, ["do not use", "exclusion", "not legal", "not financial", "unless"]):
        trigger_score += 3
        trigger_ev.append("Exclusions or boundary language found")
    else:
        trigger_gaps.append("No explicit exclusion or misuse boundary found")

    # B. Rubric
    rubric_score = 0
    rubric_ev: list[str] = []
    rubric_gaps: list[str] = []
    rubric_files = [rel for rel in files if "rubric" in rel.lower() and rel.endswith(".md")]
    rubric_text = "\n".join([text] + [read_text(files[rel]) for rel in rubric_files])
    point_total = count_rubric_points(rubric_text)
    if rubric_files:
        rubric_score += 2
        rubric_ev.append(f"Rubric reference present: {', '.join(rubric_files[:3])}")
    else:
        rubric_gaps.append("No rubric reference file found")
    if point_total == 100:
        rubric_score += 4
        rubric_ev.append("Rubric point total appears to be 100")
    elif point_total is not None:
        rubric_gaps.append(f"Detected rubric point total is {point_total}, not 100")
        findings.append(Finding("P2", "Rubric point total is not 100", f"detected total: {point_total}", "Normalize category weights to exactly 100 points."))
    else:
        rubric_gaps.append("Could not detect rubric point total")
    if has_any(all_text, ["expert model", "expert evaluation", "competent practitioner", "domain expert", "disqualifier", "failure mode"]):
        rubric_score += 4
        rubric_ev.append("Expert decision model or domain failure modes are documented")
    else:
        rubric_gaps.append("Expert decision model and domain-specific failure modes are not explicit")
    if has_any(all_text, ["non-overlapping", "independent", "decision-relevant", "observable", "evidence criteria"]):
        rubric_score += 4
        rubric_ev.append("Rubric quality criteria are documented")
    else:
        rubric_gaps.append("Rubric independence/evidence criteria are not explicit")
    if has_any(all_text, ["grade", "90-100", "85-100", "<35", "<40", "bands"]):
        rubric_score += 3
        rubric_ev.append("Grade bands are documented")
    else:
        rubric_gaps.append("Grade bands are missing")
    if has_any(all_text, ["manual review", "not an oracle", "heuristic baseline"]):
        rubric_score += 3
        rubric_ev.append("Manual review boundary is documented")
    else:
        rubric_gaps.append("Manual review boundary is missing")

    # C. Evidence/scanner
    scanner_score = 0
    scanner_ev: list[str] = []
    scanner_gaps: list[str] = []
    score_py = "scripts/score.py" in files
    if score_py:
        scanner_score += 5
        scanner_ev.append("scripts/score.py exists")
        score_text = read_text(files["scripts/score.py"])
        if has_any(score_text, ["argparse", "--json"]):
            scanner_score += 3
            scanner_ev.append("Scorer accepts CLI/json output")
        else:
            scanner_gaps.append("Scorer CLI/json handling is unclear")
        if has_any(score_text, ["evidence", "path", "gaps", "extraction"]):
            scanner_score += 4
            scanner_ev.append("Scorer appears to emit evidence/gaps")
        else:
            scanner_gaps.append("Scorer does not clearly emit evidence/gaps")
        if has_any(score_text + all_text, ["proxy", "manual-review", "manual review", "expert-only", "not an oracle", "confidence limits"]):
            scanner_score += 2
            scanner_ev.append("Scanner/proxy confidence boundaries are documented")
        else:
            scanner_gaps.append("Scanner proxy validity and expert-only judgment boundaries are unclear")
        if has_any(score_text, ["utf-8", "errors=", "UnicodeDecodeError", "pdf", "docx", "pptx", "xlsx"]):
            scanner_score += 1
            scanner_ev.append("Scorer handles extraction or decoding boundaries")
        else:
            scanner_gaps.append("Extraction/decode boundaries are unclear")
    else:
        scanner_gaps.append("No scripts/score.py found")

    # D. JSON stability
    json_score = 0
    json_ev: list[str] = []
    json_gaps: list[str] = []
    if has_any(all_text, ["schema_version", "\"categories\"", "\"actions\"", "json"]):
        json_score += 5
        json_ev.append("JSON schema/output fields are documented")
    else:
        json_gaps.append("JSON schema is weak or undocumented")
    if score_py and has_any(read_text(files["scripts/score.py"]), ["json.dump", "json.dumps"]):
        json_score += 3
        json_ev.append("Scorer writes JSON")
    else:
        json_gaps.append("Scorer JSON write path not confirmed")
    if "scripts/render_dashboard.py" in files and has_any(read_text(files["scripts/render_dashboard.py"]), ["required", "KeyError", "raise", "placeholder"]):
        json_score += 2
        json_ev.append("Renderer appears to validate or use required fields")
    else:
        json_gaps.append("Renderer field validation not confirmed")

    # E. Dashboard
    dashboard_score = 0
    dashboard_ev: list[str] = []
    dashboard_gaps: list[str] = []
    if "assets/template.html" in files:
        dashboard_score += 3
        dashboard_ev.append("assets/template.html exists")
        template = read_text(files["assets/template.html"])
        if has_any(template + all_text, ["category", "risk", "action", "evidence", "gap"]):
            dashboard_score += 4
            dashboard_ev.append("Dashboard includes decision fields")
        else:
            dashboard_gaps.append("Dashboard decision fields are unclear")
        if "{{" not in template or has_any(all_text, ["placeholder", "unresolved"]):
            dashboard_score += 3
            dashboard_ev.append("Placeholder handling is documented or template has no placeholders")
        else:
            dashboard_gaps.append("Template has placeholders without documented checks")
    else:
        dashboard_gaps.append("No assets/template.html found")

    # F. Validation
    validation_score = 0
    validation_ev: list[str] = []
    validation_gaps: list[str] = []
    if "scripts/self_test.py" in files:
        validation_score += 5
        validation_ev.append("scripts/self_test.py exists")
    else:
        validation_gaps.append("No scripts/self_test.py found")
    if has_any(all_text, ["py_compile", "self_test", "no unresolved", "placeholder", "non-empty", "fixture"]):
        validation_score += 6
        validation_ev.append("Validation steps cover compile/test/render/placeholders")
    else:
        validation_gaps.append("Validation steps are thin")
    if "scripts/self_test.py" in files and has_any(read_text(files["scripts/self_test.py"]), ["TemporaryDirectory", "fixture", "assert", "render"]):
        validation_score += 2
        validation_ev.append("Self-test appears fixture/assertion based")
    else:
        validation_gaps.append("Self-test fixture/assertion strength not confirmed")
    if "scripts/self_test.py" in files and has_any(read_text(files["scripts/self_test.py"]) + all_text, ["weak proxy", "manual-review gap", "manual review gap", "expert-only", "misleading score"]):
        validation_score += 2
        validation_ev.append("Validation references weak-proxy or expert-only score risks")
    else:
        validation_gaps.append("Validation does not clearly test weak-proxy or expert-only score risks")

    # G. ROI actions
    action_score = 0
    action_ev: list[str] = []
    action_gaps: list[str] = []
    if has_any(all_text, ["roi", "priority", "effort", "impact"]):
        action_score += 5
        action_ev.append("ROI action fields are documented")
    else:
        action_gaps.append("ROI action fields are missing")
    if has_any(all_text, ["top 3", "rank", "high-weight", "severe risk", "highest ROI"]):
        action_score += 3
        action_ev.append("Action ranking guidance is present")
    else:
        action_gaps.append("Action ranking guidance is weak")
    if score_py and has_any(read_text(files["scripts/score.py"]), ["actions", "priority", "effort", "impact"]):
        action_score += 2
        action_ev.append("Scorer appears to emit actions")
    else:
        action_gaps.append("Scorer action emission not confirmed")

    # H. Disclosure/maintainability
    maint_score = 0
    maint_ev: list[str] = []
    maint_gaps: list[str] = []
    if len(text.splitlines()) <= 220:
        maint_score += 1
        maint_ev.append("SKILL.md is concise")
    else:
        maint_gaps.append("SKILL.md may be too long")
    missing_refs = []
    for ref in re.findall(r"`([^`]+)`", text):
        if ref.startswith(("scripts/", "references/", "assets/", "agents/")) and ref not in files:
            missing_refs.append(ref)
    if not missing_refs:
        maint_score += 2
        maint_ev.append("No missing backtick file references detected")
    else:
        maint_gaps.append(f"Missing referenced files: {', '.join(sorted(set(missing_refs))[:5])}")
    unwanted = [rel for rel in files if Path(rel).name.lower() in {"readme.md", "changelog.md", "installation_guide.md", "quick_reference.md"}]
    if not unwanted:
        maint_score += 1
        maint_ev.append("No unwanted auxiliary docs found")
    else:
        maint_gaps.append(f"Unwanted auxiliary docs found: {', '.join(unwanted)}")
    if "agents/openai.yaml" in files:
        maint_score += 1
        maint_ev.append("agents/openai.yaml exists")
    else:
        maint_gaps.append("agents/openai.yaml missing")
    if generated_cache_files:
        maint_score = max(0, maint_score - 1)
        maint_gaps.append(f"Generated Python cache files found: {', '.join(generated_cache_files[:5])}")
        findings.append(Finding("P3", "Generated cache files are present", "scripts/__pycache__", "Remove generated Python cache files from the skill folder."))

    categories = {
        "cartography_contract_trigger_fit": category(trigger_score, 15, "Frontmatter, trigger cues, target/decision boundaries.", trigger_ev, trigger_gaps),
        "rubric_design_quality": category(rubric_score, 20, "Rubric presence, expert-model fit, weighting, evidence criteria, grade bands, manual review.", rubric_ev, rubric_gaps),
        "evidence_collection_scanner_fit": category(scanner_score, 15, "Scorer presence, CLI behavior, evidence/gap output, proxy validity, extraction boundaries.", scanner_ev, scanner_gaps),
        "json_schema_output_stability": category(json_score, 10, "Documented JSON schema and renderer compatibility.", json_ev, json_gaps),
        "dashboard_decision_usefulness": category(dashboard_score, 10, "Dashboard template and decision fields.", dashboard_ev, dashboard_gaps),
        "validation_integrity": category(validation_score, 15, "Compile, self-test, fixture, render, placeholder checks.", validation_ev, validation_gaps),
        "roi_action_quality": category(action_score, 10, "Action fields, ranking guidance, scorer emission.", action_ev, action_gaps),
        "progressive_disclosure_maintainability": category(maint_score, 5, "Concise structure, references, metadata, clutter.", maint_ev, maint_gaps),
    }

    for key, item in categories.items():
        if item["score"] <= item["max"] * 0.45:
            findings.append(Finding("P2", f"Weak {CATEGORIES[key][0]}", "; ".join(item["gaps"]) or "low baseline score", "Patch this category before relying on the cartography output."))
    if "[TODO" in document_text or "TODO:" in document_text or "Structuring This Skill" in document_text:
        findings.append(Finding("P2", "Unresolved TODO text remains", "TODO marker detected", "Replace scaffold placeholders with executable instructions."))

    total = sum(item["score"] for item in categories.values())
    grade = (
        "Production cartography skill" if total >= 90 else
        "Strong with small gaps" if total >= 80 else
        "Usable with targeted fixes" if total >= 70 else
        "Risky cartography" if total >= 60 else
        "Needs redesign"
    )
    actions = make_actions(categories, findings)

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target": str(skill.resolve()),
        "score": total,
        "grade": grade,
        "mode": "heuristic baseline; manual cartography review required",
        "categories": categories,
        "findings": [finding.__dict__ for finding in findings],
        "risks": [
            {
                "severity": finding.severity,
                "risk": finding.title,
                "evidence": finding.evidence,
            }
            for finding in findings
        ],
        "extraction_gaps": [
            gap
            for item in categories.values()
            for gap in item["gaps"]
            if has_any(gap, ["extraction", "decode", "unsupported", "missing", "not confirmed", "unclear"])
        ],
        "actions": actions,
    }


def make_actions(categories: dict[str, dict[str, Any]], findings: list[Finding]) -> list[dict[str, Any]]:
    weights = {key: max_score for key, (_, max_score) in CATEGORIES.items()}
    actions: list[dict[str, Any]] = []
    for key, item in categories.items():
        gap = item["max"] - item["score"]
        if gap <= 0:
            continue
        effort = "S" if gap <= 3 else "M"
        priority = round((gap / max(1, weights[key])) * 100)
        first_gap = item["gaps"][0] if item["gaps"] else "Improve evidence for this category"
        actions.append({
            "priority": priority,
            "effort": effort,
            "impact": "H" if priority >= 45 else "M",
            "action": f"Improve {CATEGORIES[key][0]}: {first_gap}",
        })
    for finding in findings:
        if finding.severity == "P1":
            actions.append({"priority": 100, "effort": "S", "impact": "H", "action": finding.fix})
    return sorted(actions, key=lambda item: item["priority"], reverse=True)[:5]


def markdown(result: dict[str, Any]) -> str:
    lines = [
        f"**Score**\n{result['score']}/100 - {result['grade']}",
        "\n**Rubric Breakdown**",
    ]
    for key, item in result["categories"].items():
        name, _ = CATEGORIES[key]
        lines.append(f"- {name}: {item['score']}/{item['max']}")
    if result["findings"]:
        lines.append("\n**Findings**")
        for idx, finding in enumerate(result["findings"][:7], 1):
            lines.append(f"{idx}. [{finding['severity']}] {finding['title']} - {finding['fix']}")
    if result["actions"]:
        lines.append("\n**Top Actions**")
        for idx, action in enumerate(result["actions"][:3], 1):
            lines.append(f"{idx}. [{action['effort']}, priority {action['priority']}] {action['action']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path)
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    result = evaluate(args.target)
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.markdown or not args.json_path:
        print(markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
