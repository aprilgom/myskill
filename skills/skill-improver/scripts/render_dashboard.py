#!/usr/bin/env python3
"""Render a single-file HTML dashboard from skill-improver score JSON."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ["schema_version", "target", "score", "grade", "categories", "actions"]


def require(data: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        raise KeyError(f"Missing required field(s): {', '.join(missing)}")


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render(data: dict[str, Any], template: str) -> str:
    require(data)
    category_rows = []
    for key, item in data["categories"].items():
        pct = round((item["score"] / max(1, item["max"])) * 100)
        evidence = "; ".join(item.get("evidence", [])[:2]) or "No positive evidence captured."
        gaps = "; ".join(item.get("gaps", [])[:2]) or "No gaps captured."
        category_rows.append(
            f"<section class='category'><div><h2>{esc(key.replace('_', ' ').title())}</h2>"
            f"<p>{esc(item.get('rationale', ''))}</p></div><strong>{item['score']}/{item['max']}</strong>"
            f"<div class='bar'><span style='width:{pct}%'></span></div>"
            f"<p><b>Evidence:</b> {esc(evidence)}</p><p><b>Gaps:</b> {esc(gaps)}</p></section>"
        )
    actions = data.get("actions", [])
    action_rows = "".join(
        f"<li><b>P{esc(action.get('priority', ''))}</b> {esc(action.get('action', ''))} "
        f"<span>{esc(action.get('effort', '?'))}/{esc(action.get('impact', '?'))}</span></li>"
        for action in actions
    ) or "<li>No actions emitted.</li>"
    risks = data.get("risks", [])
    risk_rows = "".join(
        f"<li><b>{esc(risk.get('severity', ''))}</b> {esc(risk.get('risk', ''))}: {esc(risk.get('evidence', ''))}</li>"
        for risk in risks
    ) or "<li>No risks emitted.</li>"
    gaps = data.get("extraction_gaps", [])
    gap_rows = "".join(f"<li>{esc(gap)}</li>" for gap in gaps) or "<li>No extraction gaps emitted.</li>"
    replacements = {
        "{{TARGET}}": esc(data["target"]),
        "{{SCORE}}": esc(data["score"]),
        "{{GRADE}}": esc(data["grade"]),
        "{{MODE}}": esc(data.get("mode", "")),
        "{{CATEGORY_ROWS}}": "\n".join(category_rows),
        "{{ACTION_ROWS}}": action_rows,
        "{{RISK_ROWS}}": risk_rows,
        "{{GAP_ROWS}}": gap_rows,
    }
    output = template
    for token, value in replacements.items():
        output = output.replace(token, value)
    unresolved = [token for token in output.split() if "{{" in token or "}}" in token]
    if unresolved:
        raise ValueError(f"Unresolved template placeholder(s): {', '.join(unresolved[:3])}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", type=Path)
    parser.add_argument("output_html", type=Path)
    parser.add_argument("--template", type=Path, default=Path(__file__).resolve().parents[1] / "assets" / "template.html")
    args = parser.parse_args()
    data = json.loads(args.json_path.read_text(encoding="utf-8"))
    template = args.template.read_text(encoding="utf-8")
    html_output = render(data, template)
    args.output_html.parent.mkdir(parents=True, exist_ok=True)
    args.output_html.write_text(html_output, encoding="utf-8")
    if not html_output.strip():
        raise ValueError("Rendered HTML is empty")
    print(f"Rendered {args.output_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

