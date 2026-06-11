#!/usr/bin/env python3
"""Render a porting audit score JSON file to a single HTML dashboard."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ["schema_version", "source", "target", "score", "grade", "categories", "findings", "actions"]


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def load_report(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    missing = [field for field in REQUIRED_FIELDS if field not in report]
    if missing:
        raise KeyError(f"missing required report fields: {', '.join(missing)}")
    return report


def category_rows(report: dict[str, Any]) -> str:
    rows: list[str] = []
    for key, item in report["categories"].items():
        score = int(item.get("score", 0))
        maximum = int(item.get("max", 1))
        pct = max(0, min(100, round((score / max(1, maximum)) * 100)))
        evidence = item.get("evidence") or []
        gaps = item.get("gaps") or []
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


def list_items(items: list[dict[str, Any]], empty: str, action_mode: bool = False) -> str:
    if not items:
        return f"<li>{esc(empty)}</li>"
    rows: list[str] = []
    for item in items[:8]:
        if action_mode:
            rows.append(
                f"<li><strong>Priority {esc(item.get('priority', '?'))} · {esc(item.get('effort', '?'))}/{esc(item.get('impact', '?'))}</strong>"
                f"<span>{esc(item.get('action', ''))}</span></li>"
            )
        else:
            rows.append(
                f"<li><strong>{esc(item.get('severity', 'P?'))}: {esc(item.get('title', 'Finding'))}</strong>"
                f"<span>{esc(item.get('evidence', ''))}</span><em>{esc(item.get('fix', ''))}</em></li>"
            )
    return "\n".join(rows)


def render(report: dict[str, Any], template: str) -> str:
    replacements = {
        "__SOURCE__": esc(report["source"]),
        "__TARGET__": esc(report["target"]),
        "__GENERATED_AT__": esc(report.get("generated_at", "")),
        "__SCORE__": esc(report["score"]),
        "__GRADE__": esc(report["grade"]),
        "__CATEGORY_ROWS__": category_rows(report),
        "__FINDINGS__": list_items(report.get("findings") or [], "No material findings recorded."),
        "__ACTIONS__": list_items(report.get("actions") or [], "No ROI actions recorded.", True),
    }
    output = template
    for token, value in replacements.items():
        output = output.replace(token, value)
    unresolved = [token for token in replacements if token in output]
    if unresolved:
        raise ValueError(f"unresolved template tokens: {', '.join(unresolved)}")
    if "{{" in output or "}}" in output:
        raise ValueError("unresolved placeholder braces remain in rendered HTML")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("score_json", type=Path)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = load_report(args.score_json)
    html_text = render(report, args.template.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
