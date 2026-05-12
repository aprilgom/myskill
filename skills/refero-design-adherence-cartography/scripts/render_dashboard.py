#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path


REQUIRED = {"score", "grade", "target", "reference", "categories", "extracted_rules", "risks", "actions"}


def esc(value):
    return html.escape(str(value), quote=True)


def ul(items, empty="None."):
    if not items:
        return f'<p class="muted">{esc(empty)}</p>'
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def render_categories(categories):
    parts = []
    for cat in categories:
        pct = round((cat["score"] / cat["points"]) * 100) if cat["points"] else 0
        ev = [f'{e.get("path", "")}: {e.get("detail", "")}' for e in cat.get("evidence", [])[:4]]
        gaps = cat.get("gaps", [])[:3]
        parts.append(f"""
        <div class="cat">
          <div class="cat-head"><span>{esc(cat['name'])}</span><span>{cat['score']}/{cat['points']}</span></div>
          <div class="bar"><span style="width:{pct}%"></span></div>
          <div class="muted">{esc(cat.get('rationale', ''))}</div>
          <div>{ul(ev, 'No direct evidence captured.')}</div>
          <div>{ul(gaps, 'No category gaps recorded.')}</div>
        </div>
        """)
    return "\n".join(parts)


def render_rules(rules):
    colors = "".join(f'<span class="pill">{esc(c["name"])} {esc(c["value"])}</span>' for c in rules.get("colors", [])[:14])
    fonts = "".join(f'<span class="pill">{esc(f["name"])}</span>' for f in rules.get("primary_fonts", []))
    components = "".join(f'<span class="pill">{esc(c)}</span>' for c in rules.get("components", []))
    radii = "".join(f'<span class="pill">{esc(r["element"])} {esc(r["value"])}</span>' for r in rules.get("radii", []))
    return f"""
    <table>
      <tr><th>Brand</th><td>{esc(rules.get('brand'))}</td></tr>
      <tr><th>Theme</th><td>{esc(rules.get('theme'))}</td></tr>
      <tr><th>Colors</th><td>{colors or '<span class="muted">None extracted.</span>'}</td></tr>
      <tr><th>Fonts</th><td>{fonts or '<span class="muted">None extracted.</span>'}</td></tr>
      <tr><th>Radii</th><td>{radii or '<span class="muted">None extracted.</span>'}</td></tr>
      <tr><th>Components</th><td>{components or '<span class="muted">None extracted.</span>'}</td></tr>
      <tr><th>Rules</th><td>{rules.get('do_count', 0)} Do / {rules.get('dont_count', 0)} Don't</td></tr>
    </table>
    """


def render_risks(risks):
    if not risks:
        return '<p class="ok">No high-confidence risks detected by source scan.</p>'
    return "<ul>" + "".join(f'<li><strong class="risk">{esc(r.get("severity", ""))}</strong>: {esc(r.get("title", ""))}<br><span class="muted">{esc(r.get("evidence", ""))}</span></li>' for r in risks) + "</ul>"


def render_actions(actions):
    if not actions:
        return '<p class="muted">No actions recorded.</p>'
    return "<ul>" + "".join(f'<li><strong>P{esc(a.get("priority", ""))}</strong> [{esc(a.get("effort", ""))}/{esc(a.get("impact", ""))}] {esc(a.get("action", ""))}<br><span class="muted">{esc(a.get("evidence", ""))}</span></li>' for a in actions[:8]) + "</ul>"


def render_gaps(result):
    gaps = [f'{g.get("area", g.get("path", ""))}: {g.get("reason", "")}' for g in result.get("manual_review_gaps", [])]
    gaps += [f'{g.get("path", "")}: {g.get("reason", "")}' for g in result.get("extraction_gaps", [])[:8]]
    return ul(gaps, "No gaps recorded.")


def main():
    parser = argparse.ArgumentParser(description="Render Refero design adherence dashboard.")
    parser.add_argument("score_json")
    parser.add_argument("--template", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    result = json.loads(Path(args.score_json).read_text(encoding="utf-8"))
    missing = REQUIRED - set(result)
    if missing:
        raise SystemExit(f"score JSON missing required fields: {', '.join(sorted(missing))}")
    template = Path(args.template).read_text(encoding="utf-8")
    ref = result["reference"]
    replacements = {
        "{{score}}": esc(result["score"]),
        "{{grade}}": esc(result["grade"]),
        "{{mode}}": esc(result.get("mode", "")),
        "{{reference_path}}": esc(ref.get("path", "")),
        "{{target}}": esc(result.get("target", "")),
        "{{generated_at}}": esc(result.get("generated_at", "")),
        "{{reference_summary}}": esc(f"{ref.get('brand', 'Unknown reference')} ({ref.get('theme', 'unknown')}), sections: {', '.join(ref.get('sections_detected', []))}"),
        "{{extracted_rules}}": render_rules(result.get("extracted_rules", {})),
        "{{categories}}": render_categories(result.get("categories", [])),
        "{{risks}}": render_risks(result.get("risks", [])),
        "{{actions}}": render_actions(result.get("actions", [])),
        "{{gaps}}": render_gaps(result),
    }
    html_text = template
    for key, value in replacements.items():
        html_text = html_text.replace(key, str(value))
    unresolved = [token for token in replacements if token in html_text]
    if unresolved:
        raise SystemExit(f"unresolved placeholders: {', '.join(unresolved)}")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_text, encoding="utf-8")


if __name__ == "__main__":
    main()
