#!/usr/bin/env python3
"""Render GitHub monetization score JSON into a single HTML dashboard."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {"score", "grade", "mode", "categories", "risks", "actions", "extraction_gaps"}


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def bar(category: dict[str, Any]) -> str:
    pct = 0 if not category["points"] else round(category["score"] / category["points"] * 100)
    evidence = "".join(
        f"<li><code>{esc(item.get('path', ''))}</code> - {esc(item.get('detail', ''))}</li>"
        for item in category.get("evidence", [])[:4]
    ) or "<li>No direct evidence captured.</li>"
    gaps = "".join(f"<li>{esc(gap)}</li>" for gap in category.get("gaps", [])) or "<li>No scanner gap for this category.</li>"
    return f"""
    <section class="category">
      <div class="category-head">
        <h3>{esc(category['id'])}. {esc(category['name'])}</h3>
        <strong>{esc(category['score'])}/{esc(category['points'])}</strong>
      </div>
      <div class="track"><span style="width:{pct}%"></span></div>
      <p>{esc(category.get('rationale', ''))}</p>
      <div class="cols">
        <div><h4>Evidence</h4><ul>{evidence}</ul></div>
        <div><h4>Gaps</h4><ul>{gaps}</ul></div>
      </div>
    </section>
    """


def render(template: str, data: dict[str, Any]) -> str:
    missing = REQUIRED_KEYS - set(data)
    if missing:
        raise ValueError(f"score JSON missing required keys: {sorted(missing)}")

    risks = "".join(
        f"<li><strong>{esc(r.get('severity', 'risk'))}</strong>: {esc(r.get('title', ''))}<br><span>{esc(r.get('evidence', ''))}</span></li>"
        for r in data["risks"]
    ) or "<li>No major risks detected by scanner.</li>"
    actions = "".join(
        f"<li><strong>{esc(a.get('priority', ''))}</strong> <span>{esc(a.get('effort', ''))}/{esc(a.get('impact', ''))}</span> - {esc(a.get('action', ''))}</li>"
        for a in data["actions"]
    ) or "<li>No actions generated.</li>"
    gaps = "".join(
        f"<li><code>{esc(g.get('path', ''))}</code> - {esc(g.get('reason', ''))}</li>"
        for g in data["extraction_gaps"]
    ) or "<li>No extraction gaps reported.</li>"
    categories = "".join(bar(category) for category in data["categories"])
    signals = "".join(
        f"<li><span>{esc(key)}</span><strong>{'yes' if value else 'no'}</strong></li>"
        for key, value in sorted(data.get("signals", {}).items())
    )
    inventory = "".join(
        f"<li><span>{esc(key)}</span><strong>{esc(value)}</strong></li>"
        for key, value in sorted(data.get("repo_inventory", {}).items())
    )

    html_out = template
    replacements = {
        "{{SCORE}}": esc(data["score"]),
        "{{GRADE}}": esc(data["grade"]),
        "{{MODE}}": esc(data["mode"]),
        "{{TARGET}}": esc(data.get("target", "")),
        "{{GENERATED_AT}}": esc(data.get("generated_at", "")),
        "{{MANUAL_REVIEW}}": "Required" if data.get("manual_review_required") else "Optional",
        "{{CATEGORIES}}": categories,
        "{{RISKS}}": risks,
        "{{ACTIONS}}": actions,
        "{{EXTRACTION_GAPS}}": gaps,
        "{{SIGNALS}}": signals,
        "{{INVENTORY}}": inventory,
    }
    for key, value in replacements.items():
        html_out = html_out.replace(key, value)
    unresolved = [part for part in html_out.split() if "{{" in part or "}}" in part]
    if unresolved:
        raise ValueError(f"unresolved template placeholders: {unresolved[:5]}")
    return html_out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("score_json", type=Path)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    data = json.loads(args.score_json.read_text(encoding="utf-8"))
    output = render(args.template.read_text(encoding="utf-8"), data)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
