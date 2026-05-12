#!/usr/bin/env python3
"""Heuristic scorer for Codex/Claude-style skill improvement readiness."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CATEGORIES = {
    "trigger_accuracy": ("Trigger Accuracy", 20),
    "workflow_executability": ("Workflow Executability", 20),
    "evaluation_separation": ("Evaluation Separation", 15),
    "validation_integrity": ("Validation Integrity", 15),
    "progressive_disclosure": ("Progressive Disclosure", 10),
    "resource_design": ("Resource Design", 10),
    "output_usefulness": ("Output Usefulness", 5),
    "maintainability": ("Maintainability", 5),
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
    meta = extract_frontmatter(text)
    files = {p.relative_to(skill).as_posix(): p for p in skill.rglob("*") if p.is_file()} if skill.exists() else {}
    text_files = [
        read_text(p)
        for rel, p in files.items()
        if p.suffix in {".md", ".py", ".html", ".yaml", ".yml"} and "__pycache__/" not in rel
    ]
    all_text = "\n".join([text] + text_files)
    findings: list[Finding] = []

    trigger_score = 0
    trigger_ev: list[str] = []
    trigger_gaps: list[str] = []
    desc = meta.get("description", "")
    if meta.get("name") and desc:
        trigger_score += 5
        trigger_ev.append("SKILL.md has name and description frontmatter")
    else:
        trigger_gaps.append("Missing complete frontmatter")
        findings.append(Finding("P1", "Missing required frontmatter", "SKILL.md", "Add name and description frontmatter."))
    if has_any(desc, ["improve", "fix", "upgrade", "refactor", "optimize"]):
        trigger_score += 5
        trigger_ev.append("Description includes improvement intent")
    else:
        trigger_gaps.append("Description lacks improvement trigger verbs")
    if has_any(desc, ["skill", "skill.md", "metadata", "references", "scripts"]):
        trigger_score += 5
        trigger_ev.append("Description names skill artifacts")
    else:
        trigger_gaps.append("Description does not name target artifacts")
    if has_any(text, ["guardrails", "do not", "unless", "not allowed"]):
        trigger_score += 5
        trigger_ev.append("Boundary and misuse guidance is present")
    else:
        trigger_gaps.append("Boundary guidance is thin")

    workflow_score = 0
    workflow_ev: list[str] = []
    workflow_gaps: list[str] = []
    ordered_steps = len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))
    if ordered_steps >= 6:
        workflow_score += 6
        workflow_ev.append(f"Workflow has {ordered_steps} ordered steps")
    else:
        workflow_gaps.append("Workflow has too few explicit steps")
    if has_any(text, ["identify the target", "if the user gives", "ambiguous"]):
        workflow_score += 4
        workflow_ev.append("Target discovery rules are explicit")
    else:
        workflow_gaps.append("Target discovery is unclear")
    if has_any(text, ["patch", "edit", "scoped", "target skill"]):
        workflow_score += 4
        workflow_ev.append("Scoped editing instructions are present")
    else:
        workflow_gaps.append("Scoped editing instructions are missing")
    if has_any(text, ["rerun", "verify", "report"]):
        workflow_score += 6
        workflow_ev.append("Rerun, verify, and report loop is present")
    else:
        workflow_gaps.append("Closeout loop is incomplete")

    separation_score = 0
    separation_ev: list[str] = []
    separation_gaps: list[str] = []
    if has_any(text, ["separate evaluator and improver", "eval agent/phase", "improve agent/phase"]):
        separation_score += 5
        separation_ev.append("Evaluator and improver roles are distinct")
    else:
        separation_gaps.append("Eval/improve roles are not distinct")
    if has_any(text, ["baseline evaluation", "--json", "before.json", "after.json"]):
        separation_score += 5
        separation_ev.append("Before/after evaluation artifacts are required")
    else:
        separation_gaps.append("Baseline artifacts are not required")
    if has_any(text, ["skipped", "remaining risks", "manual review", "do not treat automated score as final"]):
        separation_score += 5
        separation_ev.append("Skipped findings and manual review limits are addressed")
    else:
        separation_gaps.append("Skipped/manual findings reporting is weak")

    validation_score = 0
    validation_ev: list[str] = []
    validation_gaps: list[str] = []
    if has_any(text, ["frontmatter", "referenced files exist", "scripts compile"]):
        validation_score += 4
        validation_ev.append("Structural integrity checks are named")
    else:
        validation_gaps.append("Structural checks are weak")
    if has_any(text, ["py_compile", "self_test", "smoke test", "no generated cache"]):
        validation_score += 4
        validation_ev.append("Executable verification commands or checks are named")
    else:
        validation_gaps.append("Executable verification is thin")
    if "scripts/self_test.py" in files:
        validation_score += 4
        validation_ev.append("scripts/self_test.py exists")
    else:
        validation_gaps.append("No scripts/self_test.py found")
    if has_any(all_text, ["fixture", "assert", "non-empty", "unresolved"]):
        validation_score += 3
        validation_ev.append("Fixture/assertion based validation is present")
    else:
        validation_gaps.append("Fixture/assertion validation is missing")

    disclosure_score = 0
    disclosure_ev: list[str] = []
    disclosure_gaps: list[str] = []
    if len(text.splitlines()) <= 180:
        disclosure_score += 3
        disclosure_ev.append("SKILL.md stays concise")
    else:
        disclosure_gaps.append("SKILL.md may be too long")
    if any(rel.startswith("references/") for rel in files):
        disclosure_score += 3
        disclosure_ev.append("Reference files support progressive disclosure")
    else:
        disclosure_gaps.append("No references directory found")
    if has_any(text, ["read `references/", "Pattern Reference", "Files"]):
        disclosure_score += 4
        disclosure_ev.append("References are connected from SKILL.md")
    else:
        disclosure_gaps.append("References are not clearly connected")

    resource_score = 0
    resource_ev: list[str] = []
    resource_gaps: list[str] = []
    if "references/rubric.md" in files:
        resource_score += 3
        resource_ev.append("references/rubric.md exists")
    else:
        resource_gaps.append("No rubric reference file found")
    if "scripts/score.py" in files:
        resource_score += 3
        resource_ev.append("scripts/score.py exists")
    else:
        resource_gaps.append("No scorer script found")
    if "scripts/render_dashboard.py" in files and "assets/template.html" in files:
        resource_score += 2
        resource_ev.append("Renderer and HTML template exist")
    else:
        resource_gaps.append("Dashboard renderer/template missing")
    if "agents/openai.yaml" in files:
        resource_score += 2
        resource_ev.append("Agent metadata exists")
    else:
        resource_gaps.append("Agent metadata missing")

    output_score = 0
    output_ev: list[str] = []
    output_gaps: list[str] = []
    if has_any(text, ["Before/After", "Changed Files", "Improvements", "Remaining Risks", "Verification"]):
        output_score += 3
        output_ev.append("Final report fields are specified")
    else:
        output_gaps.append("Final report shape is incomplete")
    if has_any(text, ["findings", "roi", "actions", "priority"]):
        output_score += 2
        output_ev.append("Findings and ROI action reporting are connected")
    else:
        output_gaps.append("Finding/action reporting is weak")

    maint_score = 0
    maint_ev: list[str] = []
    maint_gaps: list[str] = []
    missing_refs = []
    for ref in re.findall(r"`([^`]+)`", text):
        if ref.startswith(("scripts/", "references/", "assets/", "agents/")) and ref not in files:
            missing_refs.append(ref)
    if not missing_refs:
        maint_score += 2
        maint_ev.append("No missing backtick file references detected")
    else:
        maint_gaps.append(f"Missing referenced files: {', '.join(sorted(set(missing_refs))[:5])}")
    generated_cache = [rel for rel in files if "__pycache__/" in rel or rel.endswith((".pyc", ".pyo"))]
    if not generated_cache:
        maint_score += 2
        maint_ev.append("No generated cache files found")
    else:
        maint_gaps.append(f"Generated cache files found: {', '.join(generated_cache[:5])}")
    if not any(Path(rel).name.lower() in {"readme.md", "changelog.md", "installation_guide.md"} for rel in files):
        maint_score += 1
        maint_ev.append("No unrelated auxiliary docs found")
    else:
        maint_gaps.append("Unrelated auxiliary docs found")

    categories = {
        "trigger_accuracy": category(trigger_score, 20, "Trigger terms, artifacts, and misuse boundaries.", trigger_ev, trigger_gaps),
        "workflow_executability": category(workflow_score, 20, "Targeting, scoped edits, and closeout loop.", workflow_ev, workflow_gaps),
        "evaluation_separation": category(separation_score, 15, "Baseline, role separation, and manual review reporting.", separation_ev, separation_gaps),
        "validation_integrity": category(validation_score, 15, "Structural checks, executable checks, and fixture assertions.", validation_ev, validation_gaps),
        "progressive_disclosure": category(disclosure_score, 10, "Concise always-loaded body plus connected references.", disclosure_ev, disclosure_gaps),
        "resource_design": category(resource_score, 10, "Rubric, scorer, dashboard, self-test, and metadata resources.", resource_ev, resource_gaps),
        "output_usefulness": category(output_score, 5, "Before/after report and action prioritization.", output_ev, output_gaps),
        "maintainability": category(maint_score, 5, "References, generated files, and auxiliary clutter.", maint_ev, maint_gaps),
    }

    for key, item in categories.items():
        if item["score"] <= item["max"] * 0.5:
            name, _ = CATEGORIES[key]
            findings.append(Finding("P2", f"Weak {name}", "; ".join(item["gaps"]) or "low score", f"Improve {name}."))

    total = sum(item["score"] for item in categories.values())
    grade = (
        "Production-ready skill improvement workflow" if total >= 90 else
        "Strong workflow with small reliability gaps" if total >= 80 else
        "Usable with targeted fixes" if total >= 70 else
        "Risky for autonomous edits" if total >= 60 else
        "Needs redesign"
    )
    actions = make_actions(categories, findings)
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target": str(skill.resolve()),
        "score": total,
        "grade": grade,
        "mode": "heuristic baseline; manual review required",
        "categories": categories,
        "findings": [finding.__dict__ for finding in findings],
        "risks": [{"severity": f.severity, "risk": f.title, "evidence": f.evidence} for f in findings],
        "extraction_gaps": [
            gap
            for item in categories.values()
            for gap in item["gaps"]
            if has_any(gap, ["missing", "not found", "unclear", "thin", "weak"])
        ],
        "actions": actions,
    }


def make_actions(categories: dict[str, dict[str, Any]], findings: list[Finding]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for key, item in categories.items():
        gap = item["max"] - item["score"]
        if gap <= 0:
            continue
        priority = round((gap / item["max"]) * 100)
        actions.append({
            "priority": priority,
            "effort": "S" if gap <= 3 else "M",
            "impact": "H" if priority >= 45 else "M",
            "action": f"Improve {CATEGORIES[key][0]}: {item['gaps'][0] if item['gaps'] else 'add stronger evidence'}",
        })
    for finding in findings:
        if finding.severity == "P1":
            actions.append({"priority": 100, "effort": "S", "impact": "H", "action": finding.fix})
    return sorted(actions, key=lambda item: item["priority"], reverse=True)[:5]


def markdown(result: dict[str, Any]) -> str:
    lines = [f"**Score**\n{result['score']}/100 - {result['grade']}", "\n**Rubric Breakdown**"]
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

