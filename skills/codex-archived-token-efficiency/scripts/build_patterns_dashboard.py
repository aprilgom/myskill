#!/usr/bin/env python3
"""Render Codex inefficiency pattern JSON as HTML."""
import argparse
import html
import json


PATTERN_LABELS = {
    "context_bloat": "Context bloat",
    "giant_tool_outputs": "Giant outputs",
    "poor_cache_util": "Poor cache utilization",
    "duplicate_tools": "Duplicate tools",
    "subagent_overuse": "Tool overuse",
    "reasoning_spikes": "Output spikes",
}


def fmt_int(x):
    return f"{int(x):,}" if x else "0"


def build_html(data):
    totals = data["totals"]
    sessions = data["sessions"]
    pattern_rows = "\n".join(
        f"<tr><td>{html.escape(PATTERN_LABELS.get(k, k))}</td><td class='num'>{v['affected_sessions']}</td><td class='num'>{fmt_int(v.get('total_waste_tokens'))}</td></tr>"
        for k, v in totals["patterns"].items()
    )
    session_rows = "\n".join(
        f"<tr><td><code>{html.escape(s['session_id'][:24])}</code><div class='muted'>{html.escape(s.get('cwd') or '')}</div></td><td class='num'>{fmt_int(s.get('total_tokens'))}</td><td>{html.escape(', '.join(k for k,p in s['patterns'].items() if p['triggered']) or 'none')}</td></tr>"
        for s in sorted(sessions, key=lambda x: x.get("total_tokens", 0), reverse=True)[:30]
    )
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Codex inefficiency patterns</title>
<style>
body {{ margin:0; font:14px/1.5 -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif; color:#172033; background:#f6f7f9; }}
main {{ max-width:1100px; margin:0 auto; padding:32px 20px; }}
.grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin:20px 0; }}
.card, table {{ background:white; border:1px solid #e4e7ec; border-radius:8px; }}
.card {{ padding:16px; }}
.label {{ color:#687386; font-size:12px; text-transform:uppercase; letter-spacing:.04em; }}
.value {{ font-size:26px; font-weight:700; }}
table {{ width:100%; border-collapse:collapse; overflow:hidden; margin:14px 0 24px; }}
th,td {{ padding:10px 12px; border-bottom:1px solid #edf0f4; text-align:left; vertical-align:top; }}
th {{ background:#fbfcfd; color:#475467; font-size:12px; }}
.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.muted {{ color:#687386; font-size:12px; }}
code {{ background:#f0f2f5; padding:1px 4px; border-radius:4px; }}
</style>
</head>
<body><main>
<h1>Codex inefficiency patterns</h1>
<section class="grid">
  <div class="card"><div class="label">Sessions</div><div class="value">{totals['sessions_total']}</div></div>
  <div class="card"><div class="label">Sessions with patterns</div><div class="value">{totals['sessions_with_any_pattern']}</div></div>
  <div class="card"><div class="label">Estimated waste tokens</div><div class="value">{fmt_int(totals['total_waste_tokens'])}</div></div>
</section>
<h2>Pattern summary</h2>
<table><thead><tr><th>Pattern</th><th class="num">Affected sessions</th><th class="num">Waste tokens</th></tr></thead><tbody>{pattern_rows}</tbody></table>
<h2>Top sessions</h2>
<table><thead><tr><th>Session</th><th class="num">Tokens</th><th>Patterns</th></tr></thead><tbody>{session_rows}</tbody></table>
</main></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="/tmp/codex_pattern_analysis.json")
    ap.add_argument("--out", default="/tmp/codex_patterns_report.html")
    args = ap.parse_args()
    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(build_html(data))
    print(f"[ok] wrote {args.out}")


if __name__ == "__main__":
    main()
