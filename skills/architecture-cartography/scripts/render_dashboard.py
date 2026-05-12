#!/usr/bin/env python3
"""Render Architecture Cartography JSON into the bundled HTML template."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def color_class(score: int, maximum: int) -> str:
    ratio = score / max(1, maximum)
    if ratio >= 0.85:
        return "good"
    if ratio >= 0.6:
        return "warn"
    return "bad"


def render_category_bars(categories: dict[str, dict[str, Any]]) -> str:
    rows: list[str] = []
    for key, category in categories.items():
        score = int(category.get("score", 0))
        maximum = int(category.get("max", 1))
        width = round(score / max(1, maximum) * 100)
        rows.append(
            '<div class="bar-row">'
            f'<div class="bar-label">{esc(key)}. {esc(category.get("name", ""))}</div>'
            f'<div class="track"><div class="fill {color_class(score, maximum)}" style="--w: {width}%"></div></div>'
            f'<div class="bar-score">{score}/{maximum}</div>'
            "</div>"
        )
    return "\n".join(rows)


def render_hotspots(report: dict[str, Any]) -> str:
    rows: list[str] = []
    for key, category in report.get("categories", {}).items():
        for finding in category.get("findings", [])[:3]:
            rows.append(
                "<tr>"
                f'<td class="mono">{esc(key)}</td>'
                f"<td>{esc(finding)}</td>"
                "</tr>"
            )
    if not rows:
        rows.append('<tr><td colspan="2">No major architecture hotspots found by the scanner.</td></tr>')
    return '<table><thead><tr><th>Cat</th><th>Finding</th></tr></thead><tbody>' + "\n".join(rows) + "</tbody></table>"


def render_actions(actions: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for action in actions[:8]:
        rows.append(
            "<tr>"
            f'<td class="mono">{esc(action.get("effort", ""))}</td>'
            f"<td>{esc(action.get('title', ''))}<br><span class=\"mono\">priority {esc(action.get('priority', ''))}</span></td>"
            f"<td>{esc(action.get('impact', ''))}</td>"
            "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="3">No ROI actions generated.</td></tr>')
    return '<table><thead><tr><th>Effort</th><th>Action</th><th>Impact</th></tr></thead><tbody>' + "\n".join(rows) + "</tbody></table>"


def evidence_notes(report: dict[str, Any]) -> str:
    meta = report.get("meta", {})
    extras = report.get("extras", {})
    notes = [
        f"Scanned {meta.get('source_files', 0)} source files across {meta.get('modules_total', 0)} detected modules.",
        f"Runtime files: {len(extras.get('runtime_files', []))}; contract files: {len(extras.get('contract_files', []))}.",
        f"Score mode: {meta.get('score_mode', 'heuristic baseline')}.",
    ]
    return "\n".join(f"<li>{esc(note)}</li>" for note in notes)


def render(report: dict[str, Any], template: str) -> str:
    meta = report.get("meta", {})
    insights = [item for item in report.get("insights", []) if item]
    summary = " ".join(insights) or "Heuristic architecture baseline generated from repository structure and dependency signals."
    replacements = {
        "{{REPO_NAME}}": esc(meta.get("repo", "repository")),
        "{{DATE}}": esc(meta.get("scored_at", "")),
        "{{BRANCH}}": esc(meta.get("branch", "unknown")),
        "{{MODULE_COUNT}}": esc(meta.get("modules_total", 0)),
        "{{FILE_COUNT}}": esc(meta.get("files_total", 0)),
        "{{TOTAL}}": esc(report.get("total", 0)),
        "{{GRADE}}": esc(report.get("grade", "Unknown")),
        "{{SUMMARY}}": esc(summary),
        "{{CATEGORY_BARS}}": render_category_bars(report.get("categories", {})),
        "{{HOTSPOTS_TABLE}}": render_hotspots(report),
        "{{ACTIONS_TABLE}}": render_actions(report.get("actions", [])),
        "{{EVIDENCE_NOTES}}": evidence_notes(report),
    }
    html_out = template
    for placeholder, value in replacements.items():
        html_out = html_out.replace(placeholder, value)
    return html_out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("score_json")
    parser.add_argument("--template", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    report = json.loads(Path(args.score_json).read_text(encoding="utf-8"))
    template = Path(args.template).read_text(encoding="utf-8")
    output = render(report, template)
    if "{{" in output or "}}" in output:
        raise SystemExit("unresolved template placeholder remains")
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
