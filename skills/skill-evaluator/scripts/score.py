#!/usr/bin/env python3
"""Skill Evaluator - deterministic checks for Codex/Claude-style skills.

Usage:
    python score.py /path/to/skill --json out.json
    python score.py /path/to/skill --markdown

The script intentionally scores only evidence that can be checked from files.
LLM/manual review should refine subjective categories after reading the JSON.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


RUBRIC_MAX = {
    "trigger_accuracy": 20,
    "workflow_executability": 20,
    "progressive_disclosure": 15,
    "resource_design": 15,
    "validation_integrity": 15,
    "maintainability": 10,
    "output_usefulness": 5,
}

UNWANTED_DOCS = {
    "README.md",
    "INSTALLATION_GUIDE.md",
    "QUICK_REFERENCE.md",
    "CHANGELOG.md",
}

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
BACKTICK_PATH_RE = re.compile(r"`((?:references|scripts|assets|agents)/[^`]+)`")
WORKFLOW_RE = re.compile(r"^##\s+(Workflow|Process|Steps|Usage|동작 흐름)", re.IGNORECASE | re.MULTILINE)
VALIDATION_RE = re.compile(r"\b(validate|verify|test|check|검증|확인|evidence)\b", re.IGNORECASE)
SCRIPT_RE = re.compile(r"\b(scripts?/[^`\s)]+|python3?\s+[^`\n]+\.py)\b")


@dataclass
class Finding:
    priority: str
    category: str
    issue: str
    evidence: str
    fix: str


@dataclass
class Action:
    title: str
    category: str
    effort: str
    effort_hours: float
    impact: str
    impact_score: int
    priority: float


@dataclass
class Category:
    score: int
    max: int
    mode: str
    evidence: dict[str, Any] = field(default_factory=dict)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data, body


def linked_paths(body: str) -> list[str]:
    out: list[str] = []
    for match in MARKDOWN_LINK_RE.finditer(body):
        raw = match.group(1) or ""
        if raw.startswith(("http://", "https://", "#")):
            continue
        out.append(raw)
    for match in BACKTICK_PATH_RE.finditer(body):
        out.append(match.group(1))
    return out


def line_count(text: str) -> int:
    return len(text.splitlines())


def grade(total: int) -> str:
    if total >= 90:
        return "Production-ready"
    if total >= 80:
        return "Strong"
    if total >= 70:
        return "Usable with targeted fixes"
    if total >= 60:
        return "Risky"
    return "Needs redesign"


def add_action(actions: list[Action], title: str, category: str, effort: str, hours: float, impact: str, impact_score: int) -> None:
    actions.append(Action(title, category, effort, hours, impact, impact_score, round(impact_score / hours, 2)))


def evaluate(skill_dir: Path) -> dict[str, Any]:
    skill_md = skill_dir / "SKILL.md"
    findings: list[Finding] = []
    actions: list[Action] = []

    if not skill_md.exists():
        return {
            "meta": {"path": str(skill_dir.resolve()), "error": "SKILL.md not found"},
            "total": 0,
            "grade": "Needs redesign",
            "categories": {},
            "findings": [asdict(Finding("P1", "workflow_executability", "SKILL.md is missing", str(skill_md), "Create a SKILL.md with frontmatter and executable workflow."))],
            "actions": [],
        }

    text = read_text(skill_md)
    front, body = parse_frontmatter(text)
    desc = front.get("description", "")
    name = front.get("name", "")
    categories: dict[str, Category] = {}

    # 1. Trigger accuracy - deterministic proxy.
    trigger_score = 20
    trigger_evidence = {
        "has_name": bool(name),
        "has_description": bool(desc),
        "description_chars": len(desc),
        "mentions_artifacts": any(term in desc.lower() for term in ("skill", "skill.md", "metadata", "folder")),
        "mentions_actions": any(term in desc.lower() for term in ("review", "audit", "score", "evaluate", "compare", "improve")),
    }
    if not name:
        trigger_score -= 5
        findings.append(Finding("P1", "trigger_accuracy", "Frontmatter is missing name.", "SKILL.md frontmatter", "Add a stable name field."))
    if len(desc) < 120:
        trigger_score -= 5
        findings.append(Finding("P2", "trigger_accuracy", "Description may be too short for reliable triggering.", f"{len(desc)} chars", "Add task verbs, artifact names, and common user phrases."))
    if len(desc) > 700:
        trigger_score -= 3
        findings.append(Finding("P3", "trigger_accuracy", "Description is long enough to become noisy.", f"{len(desc)} chars", "Trim to the highest-signal trigger phrases."))
    if not trigger_evidence["mentions_artifacts"]:
        trigger_score -= 4
    if not trigger_evidence["mentions_actions"]:
        trigger_score -= 4
    categories["trigger_accuracy"] = Category(max(0, trigger_score), 20, "auto", trigger_evidence)

    # 2. Workflow executability.
    workflow_score = 20
    workflow_evidence = {
        "has_workflow_heading": bool(WORKFLOW_RE.search(body)),
        "ordered_steps": len(re.findall(r"^\d+\.\s+", body, re.MULTILINE)),
        "script_commands": len(SCRIPT_RE.findall(body)),
    }
    if not workflow_evidence["has_workflow_heading"]:
        workflow_score -= 6
        findings.append(Finding("P2", "workflow_executability", "No clear workflow section found.", "missing ## Workflow/Process/Steps", "Add an ordered workflow with decisions and fallbacks."))
    if workflow_evidence["ordered_steps"] < 3:
        workflow_score -= 5
    if workflow_evidence["script_commands"] == 0 and (skill_dir / "scripts").exists():
        workflow_score -= 3
    categories["workflow_executability"] = Category(max(0, workflow_score), 20, "auto+manual", workflow_evidence)

    # 3. Progressive disclosure.
    refs = linked_paths(body)
    broken_refs = [p for p in refs if not (skill_dir / p).exists()]
    body_lines = line_count(body)
    progressive_score = 15
    progressive_evidence = {
        "body_lines": body_lines,
        "linked_references": refs,
        "broken_references": broken_refs,
    }
    if body_lines > 220:
        progressive_score -= 4
    if body_lines > 400:
        progressive_score -= 5
    if broken_refs:
        progressive_score -= min(6, len(broken_refs) * 2)
        findings.append(Finding("P1", "progressive_disclosure", "Referenced files are missing.", ", ".join(broken_refs[:5]), "Create the files or remove stale references."))
    categories["progressive_disclosure"] = Category(max(0, progressive_score), 15, "auto+manual", progressive_evidence)

    # 4. Resource design.
    scripts = sorted((skill_dir / "scripts").glob("*")) if (skill_dir / "scripts").exists() else []
    references = sorted((skill_dir / "references").glob("*")) if (skill_dir / "references").exists() else []
    assets = sorted((skill_dir / "assets").glob("*")) if (skill_dir / "assets").exists() else []
    non_exec_scripts = [
        str(p.relative_to(skill_dir))
        for p in scripts
        if p.is_file() and p.suffix in {".py", ".sh"} and not (p.stat().st_mode & stat.S_IXUSR)
    ]
    resource_score = 15
    resource_evidence = {
        "scripts": [str(p.relative_to(skill_dir)) for p in scripts],
        "references": [str(p.relative_to(skill_dir)) for p in references],
        "assets": [str(p.relative_to(skill_dir)) for p in assets],
        "non_executable_scripts": non_exec_scripts,
    }
    if scripts and not SCRIPT_RE.search(body):
        resource_score -= 4
        findings.append(Finding("P2", "resource_design", "Scripts exist but are not connected from SKILL.md.", ", ".join(resource_evidence["scripts"][:5]), "Document when and how to run each script."))
    if non_exec_scripts:
        resource_score -= min(4, len(non_exec_scripts) * 2)
        findings.append(Finding("P3", "resource_design", "Executable scripts lack user execute bit.", ", ".join(non_exec_scripts[:5]), "Run chmod +x or document invocation through python/sh."))
    categories["resource_design"] = Category(max(0, resource_score), 15, "auto+manual", resource_evidence)

    # 5. Validation integrity.
    validation_score = 15
    validation_evidence = {
        "validation_terms": len(VALIDATION_RE.findall(body)),
        "mentions_evidence": "evidence" in body.lower() or "증거" in body,
        "mentions_subagents": "subagent" in body.lower() or "agent" in body.lower(),
    }
    if validation_evidence["validation_terms"] < 2:
        validation_score -= 6
        findings.append(Finding("P2", "validation_integrity", "Validation guidance is thin.", f"{validation_evidence['validation_terms']} validation terms", "Add concrete checks and evidence requirements."))
    if not validation_evidence["mentions_evidence"]:
        validation_score -= 3
    categories["validation_integrity"] = Category(max(0, validation_score), 15, "manual", validation_evidence)

    # 6. Maintainability.
    unwanted = [str(p.relative_to(skill_dir)) for p in skill_dir.iterdir() if p.name in UNWANTED_DOCS]
    hidden_junk = [str(p.relative_to(skill_dir)) for p in skill_dir.rglob(".DS_Store")]
    maintain_score = 10
    maintain_evidence = {
        "unwanted_docs": unwanted,
        "hidden_junk": hidden_junk,
        "top_level_files": sorted(str(p.relative_to(skill_dir)) for p in skill_dir.iterdir() if p.is_file()),
    }
    if unwanted:
        maintain_score -= min(4, len(unwanted) * 2)
        findings.append(Finding("P3", "maintainability", "Skill contains auxiliary docs that skill-creator discourages.", ", ".join(unwanted), "Move essential content into SKILL.md or references and delete clutter."))
    if hidden_junk:
        maintain_score -= 2
    categories["maintainability"] = Category(max(0, maintain_score), 10, "auto", maintain_evidence)

    # 7. Output usefulness.
    output_score = 5
    output_evidence = {
        "has_output_format": "output format" in body.lower() or "what to produce" in body.lower(),
        "mentions_findings": "findings" in body.lower(),
        "mentions_actions": "action" in body.lower() or "patch plan" in body.lower(),
    }
    if not output_evidence["has_output_format"]:
        output_score -= 2
    if not output_evidence["mentions_actions"]:
        output_score -= 1
    categories["output_usefulness"] = Category(max(0, output_score), 5, "auto+manual", output_evidence)

    # ROI actions from findings and low scores.
    for key, cat in categories.items():
        ratio = cat.score / cat.max
        if ratio >= 0.8:
            continue
        if key == "trigger_accuracy":
            add_action(actions, "Tighten trigger metadata", key, "S", 0.5, "Reduces missed and false skill invocation.", 9)
        elif key == "workflow_executability":
            add_action(actions, "Rewrite SKILL.md as ordered executable workflow", key, "S", 1.0, "Cuts agent guesswork during use.", 8)
        elif key == "progressive_disclosure":
            add_action(actions, "Repair references and move detail out of SKILL.md", key, "S", 1.0, "Lowers context cost and stale-reference risk.", 7)
        elif key == "resource_design":
            add_action(actions, "Connect bundled resources to workflow", key, "S", 0.75, "Makes scripts/assets discoverable at the right step.", 7)
        elif key == "validation_integrity":
            add_action(actions, "Add evidence-based validation checks", key, "M", 2.0, "Improves trust in generated outputs.", 8)
        elif key == "maintainability":
            add_action(actions, "Remove clutter and isolate volatile details", key, "S", 0.5, "Makes future edits safer.", 5)
        elif key == "output_usefulness":
            add_action(actions, "Define final report shape and prioritization", key, "S", 0.5, "Makes results immediately actionable.", 6)

    actions.sort(key=lambda a: a.priority, reverse=True)
    total = sum(cat.score for cat in categories.values())

    return {
        "meta": {
            "skill": name or skill_dir.name,
            "path": str(skill_dir.resolve()),
            "score_mode": "auto baseline; manual review should refine subjective categories",
        },
        "total": total,
        "grade": grade(total),
        "categories": {k: asdict(v) for k, v in categories.items()},
        "findings": [asdict(f) for f in findings],
        "actions": [asdict(a) for a in actions],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Skill Evaluation · {payload['meta'].get('skill', 'unknown')}",
        "",
        f"**Score:** {payload['total']}/100 · **Grade:** {payload['grade']}",
        f"**Mode:** {payload['meta'].get('score_mode')}",
        "",
        "## Rubric Breakdown",
    ]
    for key, cat in payload["categories"].items():
        lines.append(f"- {key}: **{cat['score']}/{cat['max']}** ({cat['mode']})")
    lines.append("")
    if payload["findings"]:
        lines.append("## Findings")
        for item in payload["findings"]:
            lines.append(f"- [{item['priority']}] {item['category']}: {item['issue']} Evidence: {item['evidence']} Fix: {item['fix']}")
        lines.append("")
    if payload["actions"]:
        lines.append("## ROI Actions")
        for idx, action in enumerate(payload["actions"][:8], 1):
            lines.append(f"{idx}. [{action['category']}] {action['title']} - {action['effort']} ({action['effort_hours']}h), priority {action['priority']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("skill_dir", help="path to a skill folder")
    parser.add_argument("--json", dest="json_out", help="write JSON scorecard")
    parser.add_argument("--markdown", action="store_true", help="print markdown report")
    parser.add_argument("--quiet", action="store_true", help="suppress stdout")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    payload = evaluate(skill_dir)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        if args.markdown or not args.json_out:
            print(render_markdown(payload))
        else:
            print(f"{payload['meta'].get('skill', skill_dir.name)}: {payload['total']}/100 · {payload['grade']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
