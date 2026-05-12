#!/usr/bin/env python3
"""Render Codex token analysis JSON as a self-contained HTML report."""
import argparse
import html
import json


def fmt_int(x):
    return f"{int(x):,}" if x else "0"


def fmt_usd(x):
    return f"${x:,.2f}"


def pct(x):
    return f"{x * 100:.1f}%"


def recommendation_candidates(totals, sessions):
    session_count = max(1, len(sessions))
    cache_ratio = totals.get("cache_hit_ratio", 0)
    large_outputs = totals.get("large_output_events", 0)
    total_tokens = totals.get("total_tokens", 0)
    tool_calls = totals.get("num_tool_calls", 0)
    output_tokens = totals.get("output_tokens", 0)
    tool_density = tool_calls / max(1, output_tokens / 1000)
    top_session = sessions[0] if sessions else {}
    top_share = (top_session.get("total_tokens", 0) / total_tokens) if total_tokens else 0
    low_cache_sessions = sum(1 for s in sessions if s.get("input_tokens", 0) >= 30_000 and s.get("cache_hit_ratio", 0) < 0.50)
    high_tool_sessions = sum(
        1
        for s in sessions
        if s.get("num_tool_calls", 0) / max(1, s.get("output_tokens", 0) / 1000) > 20
    )

    return [
        (
            100 if cache_ratio < 0.50 else 45 if low_cache_sessions else 0,
            "Stabilize cache inputs",
            f"Cached input is {pct(cache_ratio)}; {low_cache_sessions} large sessions are below 50%. Keep long instructions and large assets stable within a task.",
        ),
        (
            min(98, 85 + large_outputs * 10) if large_outputs else 0,
            "Bound large outputs",
            f"{fmt_int(large_outputs)} large output events were found. Prefer targeted `rg`, `head`, and file ranges so command output does not inflate later turns.",
        ),
        (
            90 if top_share >= 0.35 else 55 if top_share >= 0.20 else 0,
            "Split dominant sessions",
            f"The largest session uses {pct(top_share)} of all tokens. Start a fresh session when the goal or repo area changes.",
        ),
        (
            97 if tool_density > 20 else 50 if high_tool_sessions else 0,
            "Reduce tool-call thrash",
            f"Tool-call density is {tool_density:.1f} calls per 1k output tokens; {high_tool_sessions} sessions exceed 20. Batch independent reads and narrow repeated probes.",
        ),
        (
            35,
            "Keep current session shape",
            f"Across {fmt_int(session_count)} sessions, average cache and tool metrics are the main signals to preserve while watching top-token sessions.",
        ),
    ]


def build_recommendations(totals, sessions):
    ranked = sorted(recommendation_candidates(totals, sessions), key=lambda item: item[0], reverse=True)
    cards = []
    for idx, (_, title, body) in enumerate(ranked[:3], start=1):
        cards.append(
            f'<div class="card"><h3>{idx}. {html.escape(title)}</h3><p>{html.escape(body)}</p></div>'
        )
    return "\n    ".join(cards)


def build_html(data, repo_name):
    totals = data["totals"]
    sessions = data["sessions"]
    top = sessions[:20]
    avg_score = sum(s["scores"]["composite"] for s in sessions) / max(1, len(sessions))
    est_cost = totals.get("cost_usd", 0.0)
    recommendations = build_recommendations(totals, sessions)

    rows = "\n".join(
        f"""
        <tr>
          <td><code>{html.escape(s['session_id'][:24])}</code><div class="muted">{html.escape(s.get('cwd') or '')}</div></td>
          <td class="num">{fmt_int(s.get('total_tokens'))}</td>
          <td class="num">{pct(s.get('cache_hit_ratio', 0))}</td>
          <td class="num">{fmt_int(s.get('output_tokens'))}</td>
          <td class="num">{s['scores']['composite']:.1f}</td>
          <td class="num">{s['scores']['grade']}</td>
        </tr>
        """
        for s in top
    )

    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(repo_name)} - Codex token efficiency</title>
<style>
body {{ margin:0; font:14px/1.5 -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif; color:#172033; background:#f6f7f9; }}
main {{ max-width:1180px; margin:0 auto; padding:32px 20px; }}
h1 {{ margin:0 0 4px; font-size:28px; }}
.muted {{ color:#687386; font-size:12px; }}
.grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:22px 0; }}
.card {{ background:white; border:1px solid #e4e7ec; border-radius:8px; padding:16px; }}
.label {{ color:#687386; font-size:12px; text-transform:uppercase; letter-spacing:.04em; }}
.value {{ font-size:26px; font-weight:700; margin-top:4px; }}
.good {{ color:#087443; }}
.warn {{ color:#b54708; }}
table {{ width:100%; border-collapse:collapse; background:white; border:1px solid #e4e7ec; border-radius:8px; overflow:hidden; }}
th,td {{ padding:10px 12px; border-bottom:1px solid #edf0f4; text-align:left; vertical-align:top; }}
th {{ background:#fbfcfd; color:#475467; font-size:12px; }}
.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.actions {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin:18px 0 24px; }}
.actions h3 {{ margin:0 0 8px; font-size:16px; }}
code {{ background:#f0f2f5; padding:1px 4px; border-radius:4px; }}
@media (max-width: 800px) {{ .grid,.actions {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<main>
  <h1>Codex token efficiency report</h1>
  <div class="muted">{html.escape(repo_name)} · {html.escape(totals.get('sessions_dir', ''))}</div>

  <section class="grid">
    <div class="card"><div class="label">Sessions</div><div class="value">{fmt_int(totals['sessions'])}</div></div>
    <div class="card"><div class="label">Total tokens</div><div class="value">{fmt_int(totals.get('total_tokens'))}</div></div>
    <div class="card"><div class="label">Cached input</div><div class="value good">{pct(totals.get('cache_hit_ratio', 0))}</div></div>
    <div class="card"><div class="label">Avg score</div><div class="value">{avg_score:.1f}</div></div>
  </section>

  <section class="actions">
    {recommendations}
  </section>

  <section class="card">
    <div class="label">Estimated API-equivalent cost</div>
    <div class="value warn">{fmt_usd(est_cost)}</div>
    <div class="muted">Approximate only. Codex subscription accounting may not match API pricing.</div>
  </section>

  <h2>Top sessions by tokens</h2>
  <table>
    <thead><tr><th>Session</th><th class="num">Tokens</th><th class="num">Cached input</th><th class="num">Output</th><th class="num">Score</th><th class="num">Grade</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</main>
</body>
</html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="/tmp/codex_session_analysis.json")
    ap.add_argument("--out", default="/tmp/codex_efficiency_report.html")
    ap.add_argument("--repo-name", default="Codex sessions")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    html_doc = build_html(data, args.repo_name)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html_doc)
    print(f"[ok] wrote {args.out}")


if __name__ == "__main__":
    main()
