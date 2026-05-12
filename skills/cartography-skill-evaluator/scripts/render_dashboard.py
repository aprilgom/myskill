#!/usr/bin/env python3
"""Render a cartography skill evaluation JSON file to a single HTML map."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ["schema_version", "target", "score", "grade", "categories", "findings", "actions"]


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def load_report(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    missing = [field for field in REQUIRED_FIELDS if field not in report]
    if missing:
        raise KeyError(f"missing required report fields: {', '.join(missing)}")
    return report


def category_rows(report: dict[str, Any]) -> str:
    rows = []
    for key, item in report["categories"].items():
        score = int(item.get("score", 0))
        maximum = int(item.get("max", 1))
        pct = max(0, min(100, round((score / max(1, maximum)) * 100)))
        gaps = item.get("gaps") or []
        evidence = item.get("evidence") or []
        rows.append(
            "<tr>"
            f"<td><strong>{esc(key.replace('_', ' ').title())}</strong><span>{esc(item.get('rationale', ''))}</span></td>"
            f"<td>{score}/{maximum}</td>"
            f"<td><div class=\"bar\"><i style=\"width:{pct}%\"></i></div></td>"
            f"<td>{esc(evidence[0] if evidence else 'No evidence recorded')}</td>"
            f"<td>{esc(gaps[0] if gaps else 'No material gap recorded')}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def finding_items(report: dict[str, Any]) -> str:
    findings = report.get("findings") or []
    if not findings:
        return "<li>No material findings recorded.</li>"
    return "\n".join(
        f"<li><strong>{esc(item.get('severity', 'P?'))}: {esc(item.get('title', 'Finding'))}</strong>"
        f"<span>{esc(item.get('evidence', ''))}</span><em>{esc(item.get('fix', ''))}</em></li>"
        for item in findings[:8]
    )


def action_items(report: dict[str, Any]) -> str:
    actions = report.get("actions") or []
    if not actions:
        return "<li>No ROI actions recorded.</li>"
    return "\n".join(
        f"<li><strong>Priority {esc(item.get('priority', '?'))} · {esc(item.get('effort', '?'))}/{esc(item.get('impact', '?'))}</strong>"
        f"<span>{esc(item.get('action', ''))}</span></li>"
        for item in actions[:8]
    )


def render(report: dict[str, Any], template: str) -> str:
    replacements = {
        "__TARGET__": esc(report["target"]),
        "__GENERATED_AT__": esc(report.get("generated_at", "")),
        "__SCORE__": esc(report["score"]),
        "__GRADE__": esc(report["grade"]),
        "__MODE__": esc(report.get("mode", "")),
        "__CATEGORY_ROWS__": category_rows(report),
        "__FINDINGS__": finding_items(report),
        "__ACTIONS__": action_items(report),
    }
    html_text = template
    for token, value in replacements.items():
        html_text = html_text.replace(token, value)
    unresolved = [token for token in replacements if token in html_text]
    if unresolved:
        raise ValueError(f"unresolved template tokens: {', '.join(unresolved)}")
    if "{{" in html_text or "}}" in html_text:
        raise ValueError("unresolved placeholder braces remain in rendered HTML")
    return html_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("score_json", type=Path)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = load_report(args.score_json)
    template = args.template.read_text(encoding="utf-8")
    html_text = render(report, template)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
