#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path


REQUIRED = {"target", "generated_at", "score", "grade", "mode", "categories", "risks", "actions", "extraction_gaps"}


def esc(value):
    return html.escape(str(value), quote=True)


def render_categories(categories):
    chunks = []
    for item in categories:
        width = 0 if item["points"] == 0 else round((item["score"] / item["points"]) * 100)
        evidence = item.get("evidence") or []
        gaps = item.get("gaps") or []
        evidence_html = "".join(f"<li>{esc(e.get('path', ''))}: {esc(e.get('detail', ''))}</li>" for e in evidence[:2])
        gaps_html = "".join(f"<li>{esc(g)}</li>" for g in gaps[:2])
        chunks.append(
            '<article class="panel">'
            f'<div class="category-title"><span>{esc(item["id"])}. {esc(item["name"])}</span><span>{esc(item["score"])}/{esc(item["points"])}</span></div>'
            f'<div class="bar"><div class="fill" style="--w:{width}%"></div></div>'
            f'<p>{esc(item.get("rationale", ""))}</p>'
            f'<ul>{evidence_html}{gaps_html}</ul>'
            '</article>'
        )
    return "\n".join(chunks)


def render_table(items, columns, empty):
    if not items:
        return f"<p>{esc(empty)}</p>"
    head = "".join(f"<th>{esc(label)}</th>" for _, label in columns)
    rows = []
    for item in items:
        cells = "".join(f"<td>{esc(item.get(key, ''))}</td>" for key, _ in columns)
        rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def render_gaps(gaps):
    if not gaps:
        return "<p>No extraction gaps reported.</p>"
    return "<ul>" + "".join(f"<li>{esc(gap.get('path', ''))}: {esc(gap.get('reason', ''))}</li>" for gap in gaps) + "</ul>"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("score_json")
    parser.add_argument("--template", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    data = json.loads(Path(args.score_json).read_text(encoding="utf-8"))
    missing = REQUIRED - set(data)
    if missing:
        raise SystemExit(f"score JSON missing required fields: {', '.join(sorted(missing))}")

    template = Path(args.template).read_text(encoding="utf-8")
    replacements = {
        "{{TARGET}}": esc(data["target"]),
        "{{GENERATED_AT}}": esc(data["generated_at"]),
        "{{MODE}}": esc(data["mode"]),
        "{{SCORE}}": esc(data["score"]),
        "{{GRADE}}": esc(data["grade"]),
        "{{CATEGORY_CARDS}}": render_categories(data["categories"]),
        "{{RISKS_TABLE}}": render_table(data["risks"], [("severity", "Severity"), ("title", "Risk"), ("evidence", "Evidence")], "No major risks reported."),
        "{{ACTIONS_TABLE}}": render_table(data["actions"], [("priority", "Priority"), ("effort", "Effort"), ("impact", "Impact"), ("action", "Action"), ("evidence", "Evidence")], "No actions reported."),
        "{{GAPS_LIST}}": render_gaps(data["extraction_gaps"]),
    }
    html_out = template
    for key, value in replacements.items():
        html_out = html_out.replace(key, value)
    if "{{" in html_out or "}}" in html_out:
        raise SystemExit("unresolved template placeholders remain")
    Path(args.out).write_text(html_out, encoding="utf-8")


if __name__ == "__main__":
    main()
