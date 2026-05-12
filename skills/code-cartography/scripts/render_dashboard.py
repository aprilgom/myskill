#!/usr/bin/env python3
"""Render code-cartography JSON into a single-file HTML dashboard."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


REQUIRED_FIELDS = {
    "actions",
    "categories",
    "generated_at",
    "grade",
    "hotspots",
    "metrics",
    "mode",
    "risks",
    "score",
    "target",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def category_rows(data: dict[str, object]) -> str:
    rows = []
    for category in data["categories"]:
        points = int(category["points"])
        score = int(category["score"])
        pct = 0 if points == 0 else round((score / points) * 100)
        evidence = "; ".join(f"{item['path']}: {item['detail']}" for item in category.get("evidence", [])[:3])
        gaps = "; ".join(category.get("gaps", [])[:2])
        rows.append(
            "<tr>"
            f"<td><strong>{esc(category['id'])}</strong></td>"
            f"<td>{esc(category['name'])}<div class=\"muted\">{esc(category['rationale'])}</div></td>"
            f"<td class=\"num\">{score}/{points}</td>"
            f"<td><div class=\"bar\"><span style=\"width:{pct}%\"></span></div></td>"
            f"<td>{esc(evidence or gaps or 'No notable scanner evidence.')}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def risk_rows(data: dict[str, object]) -> str:
    risks = data.get("risks", [])
    if not risks:
        return "<tr><td colspan=\"3\">No material risks detected.</td></tr>"
    return "\n".join(
        "<tr>"
        f"<td><span class=\"pill {esc(item['severity'])}\">{esc(item['severity'])}</span></td>"
        f"<td>{esc(item['title'])}</td>"
        f"<td>{esc(item['evidence'])}</td>"
        "</tr>"
        for item in risks
    )


def action_rows(data: dict[str, object]) -> str:
    actions = data.get("actions", [])
    if not actions:
        return "<tr><td colspan=\"5\">No ROI actions generated.</td></tr>"
    return "\n".join(
        "<tr>"
        f"<td class=\"num\">{esc(item['priority'])}</td>"
        f"<td>{esc(item['effort'])}</td>"
        f"<td>{esc(item['impact'])}</td>"
        f"<td>{esc(item['action'])}</td>"
        f"<td>{esc(item['evidence'])}</td>"
        "</tr>"
        for item in actions
    )


def hotspot_rows(data: dict[str, object]) -> str:
    hotspots = data.get("hotspots", [])
    if not hotspots:
        return "<tr><td colspan=\"4\">No hotspots above threshold.</td></tr>"
    rows = []
    for item in hotspots[:20]:
        metrics = item.get("metrics", {})
        metric_text = (
            f"LOC {metrics.get('loc', 0)}, imports {metrics.get('imports', 0)}, "
            f"fan-in {metrics.get('fan_in', 0)}, debt {metrics.get('debt_markers', 0)}, "
            f"nearby test {metrics.get('nearby_test', False)}"
        )
        rows.append(
            "<tr>"
            f"<td class=\"num\">{esc(item['risk_score'])}</td>"
            f"<td><code>{esc(item['path'])}</code></td>"
            f"<td>{esc('; '.join(item.get('reasons', [])[:4]))}</td>"
            f"<td>{esc(metric_text)}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def gap_rows(data: dict[str, object]) -> str:
    gaps = data.get("extraction_gaps", [])
    if not gaps:
        return "<tr><td colspan=\"2\">No extraction gaps.</td></tr>"
    return "\n".join(
        "<tr>"
        f"<td><code>{esc(item['path'])}</code></td>"
        f"<td>{esc(item['reason'])}</td>"
        "</tr>"
        for item in gaps
    )


def metrics_cards(data: dict[str, object]) -> str:
    metrics = data["metrics"]
    cards = [
        ("Files", metrics.get("code_files_scanned", 0)),
        ("Source", metrics.get("source_files", 0)),
        ("Tests", metrics.get("test_files", 0)),
        ("Source LOC", metrics.get("source_loc", 0)),
        ("Test Ratio", metrics.get("test_to_source_ratio", 0)),
        ("Test Proximity", metrics.get("source_test_proximity", 0)),
        ("Debt Markers", metrics.get("debt_markers", 0)),
        ("Duplicate Lines", metrics.get("duplicate_normalized_lines", 0)),
    ]
    return "\n".join(
        f"<div class=\"metric\"><span>{esc(label)}</span><strong>{esc(value)}</strong></div>"
        for label, value in cards
    )


def render(data: dict[str, object], template: str) -> str:
    missing = sorted(REQUIRED_FIELDS - data.keys())
    if missing:
        raise KeyError(f"score JSON missing required fields: {', '.join(missing)}")
    replacements = {
        "{{TARGET}}": esc(data["target"]),
        "{{GENERATED_AT}}": esc(data["generated_at"]),
        "{{SCORE}}": esc(data["score"]),
        "{{GRADE}}": esc(data["grade"]),
        "{{MODE}}": esc(data["mode"]),
        "{{CATEGORY_ROWS}}": category_rows(data),
        "{{RISK_ROWS}}": risk_rows(data),
        "{{ACTION_ROWS}}": action_rows(data),
        "{{HOTSPOT_ROWS}}": hotspot_rows(data),
        "{{GAP_ROWS}}": gap_rows(data),
        "{{METRICS_CARDS}}": metrics_cards(data),
    }
    output = template
    for placeholder, value in replacements.items():
        output = output.replace(placeholder, value)
    unresolved = [token for token in remainders(output) if token.startswith("{{")]
    if unresolved:
        raise ValueError(f"unresolved template placeholders: {', '.join(unresolved[:5])}")
    return output


def remainders(text: str) -> list[str]:
    parts = []
    start = 0
    while True:
        index = text.find("{{", start)
        if index == -1:
            return parts
        end = text.find("}}", index)
        if end == -1:
            parts.append(text[index:])
            return parts
        parts.append(text[index : end + 2])
        start = end + 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a code-cartography HTML dashboard.")
    parser.add_argument("score_json", help="Path to code-score.json")
    parser.add_argument("--template", required=True, help="Path to template.html")
    parser.add_argument("--out", required=True, help="Path to write code-map.html")
    args = parser.parse_args()

    data = json.loads(Path(args.score_json).read_text(encoding="utf-8"))
    template = Path(args.template).read_text(encoding="utf-8")
    html_body = render(data, template)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_body, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
