#!/usr/bin/env python3
"""Analyze Codex Desktop session JSONL files for project token/context efficiency.

Usage:
  python3 analyze_sessions.py [--out /tmp/session_analysis.json]
  python3 analyze_sessions.py --repo /path/to/repo
  python3 analyze_sessions.py --source live|archived|all

Codex records token accounting in event_msg payloads with type=token_count.
This script sums last_token_usage for each session so session totals are not
double-counted, then computes a small efficiency rubric for one project cwd.
"""
import argparse
import glob
import json
import os
import sys
from collections import defaultdict


# Approximate OpenAI API prices, USD per 1M tokens. The defaults are intentionally
# editable because Codex subscription usage may not map 1:1 to API billing.
PRICING = {
    "gpt-5.5": {"in": 1.25, "cached": 0.125, "out": 10.0},
    "gpt-5.4": {"in": 1.25, "cached": 0.125, "out": 10.0},
    "gpt-5.4-mini": {"in": 0.25, "cached": 0.025, "out": 2.0},
    "gpt-5.3-codex": {"in": 1.25, "cached": 0.125, "out": 10.0},
    "gpt-5.3-codex-spark": {"in": 0.25, "cached": 0.025, "out": 2.0},
    "gpt-5.2": {"in": 1.25, "cached": 0.125, "out": 10.0},
    "<unknown>": {"in": 1.25, "cached": 0.125, "out": 10.0},
}
DEFAULT_PRICE = PRICING["<unknown>"]


def codex_home():
    return os.path.expanduser("~/.codex")


def session_key(path):
    basename = os.path.basename(path).replace(".jsonl", "")
    marker = "-019"
    idx = basename.find(marker)
    if idx >= 0:
        return basename[idx + 1 :]
    return basename


def load_session_index(path=None):
    index_path = os.path.expanduser(path or os.path.join(codex_home(), "session_index.jsonl"))
    titles = {}
    if not os.path.exists(index_path):
        return titles
    try:
        with open(index_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                sid = rec.get("id")
                name = rec.get("thread_name")
                if sid and name:
                    titles[sid] = name
    except Exception:
        return titles
    return titles


def discover_session_files(args):
    if args.sessions_dir:
        root = os.path.expanduser(args.sessions_dir)
        return sorted(glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True)), root

    roots = []
    if args.source in {"live", "all"}:
        roots.append(os.path.join(codex_home(), "sessions"))
    if args.source in {"archived", "all"}:
        roots.append(os.path.join(codex_home(), "archived_sessions"))

    files = []
    for root in roots:
        files.extend(glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True))
    return sorted(set(files)), ",".join(roots)


def session_cwd(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("type") == "session_meta":
                    cwd = (rec.get("payload") or {}).get("cwd")
                    return os.path.abspath(os.path.expanduser(cwd)) if cwd else None
    except Exception:
        return None
    return None


def detect_project_repo(files, current_session_file=None):
    candidates = []
    if current_session_file:
        path = os.path.abspath(os.path.expanduser(current_session_file))
        if os.path.exists(path):
            candidates.append(path)

    live_root = os.path.join(codex_home(), "sessions")
    live_files = [fp for fp in files if os.path.abspath(fp).startswith(os.path.abspath(live_root))]
    candidates.extend(sorted(live_files, key=lambda fp: os.path.getmtime(fp), reverse=True))
    candidates.extend(sorted(files, key=lambda fp: os.path.getmtime(fp), reverse=True))

    seen = set()
    for fp in candidates:
        if fp in seen:
            continue
        seen.add(fp)
        cwd = session_cwd(fp)
        if cwd:
            return cwd, fp
    return None, None


def price_for(model):
    return PRICING.get(model or "", DEFAULT_PRICE)


def content_text_len(content):
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        total = 0
        for item in content:
            if isinstance(item, dict):
                total += len(item.get("text", ""))
        return total
    return 0


def analyze_session(path, session_titles=None):
    sid = os.path.basename(path).replace(".jsonl", "")
    thread_id = session_key(path)
    thread_name = (session_titles or {}).get(thread_id)
    stats = {
        "session_id": sid,
        "thread_id": thread_id,
        "display_name": thread_name or sid,
        "file_path": path,
        "file_size": os.path.getsize(path),
        "cwd": None,
        "thread_name": thread_name,
        "originator": None,
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "total_tokens": 0,
        "cache_create_5m": 0,
        "cache_create_1h": 0,
        "cache_read": 0,
        "num_assistant_msgs": 0,
        "num_user_msgs": 0,
        "num_tool_calls": 0,
        "tool_use_counter": defaultdict(int),
        "first_ts": None,
        "last_ts": None,
        "models": set(),
        "cost_usd": 0.0,
        "image_count": 0,
        "large_output_events": 0,
        "token_events": 0,
    }

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue

                ts = rec.get("timestamp")
                if ts:
                    if stats["first_ts"] is None:
                        stats["first_ts"] = ts
                    stats["last_ts"] = ts

                rtype = rec.get("type")
                payload = rec.get("payload", {}) or {}

                if rtype == "session_meta":
                    stats["cwd"] = payload.get("cwd")
                    stats["originator"] = payload.get("originator")
                    model = payload.get("model")
                    if model:
                        stats["models"].add(model)

                elif rtype == "event_msg":
                    ptype = payload.get("type")
                    if ptype == "token_count":
                        info = payload.get("info") or {}
                        usage = info.get("last_token_usage") or {}
                        if not usage:
                            continue
                        stats["token_events"] += 1
                        inp = usage.get("input_tokens", 0) or 0
                        cached = usage.get("cached_input_tokens", 0) or 0
                        out = usage.get("output_tokens", 0) or 0
                        reasoning = usage.get("reasoning_output_tokens", 0) or 0
                        total = usage.get("total_tokens", 0) or (inp + out)

                        stats["input_tokens"] += inp
                        stats["cached_input_tokens"] += cached
                        stats["output_tokens"] += out
                        stats["reasoning_output_tokens"] += reasoning
                        stats["total_tokens"] += total
                        stats["cache_read"] += cached

                        model = payload.get("model") or next(iter(stats["models"]), "")
                        price = price_for(model)
                        uncached = max(0, inp - cached)
                        stats["cost_usd"] += (
                            uncached * price["in"] / 1e6
                            + cached * price["cached"] / 1e6
                            + out * price["out"] / 1e6
                        )

                    elif ptype == "agent_message":
                        stats["num_assistant_msgs"] += 1
                        msg = payload.get("message", "")
                        if isinstance(msg, str) and len(msg) > 50_000:
                            stats["large_output_events"] += 1

                    elif ptype == "user_message":
                        stats["num_user_msgs"] += 1
                        stats["image_count"] += len(payload.get("images") or [])
                        stats["image_count"] += len(payload.get("local_images") or [])

                    elif ptype in {"exec_command", "tool_call", "mcp_tool_call"}:
                        stats["num_tool_calls"] += 1
                        name = payload.get("tool") or payload.get("name") or ptype
                        stats["tool_use_counter"][name] += 1

                elif rtype == "response_item":
                    item = payload or {}
                    if item.get("type") == "message":
                        role = item.get("role")
                        if role == "assistant":
                            stats["num_assistant_msgs"] += 1
                        elif role == "user":
                            stats["num_user_msgs"] += 1
                    if content_text_len(item.get("content")) > 50_000:
                        stats["large_output_events"] += 1
    except Exception as e:
        stats["error"] = str(e)

    total_input = stats["input_tokens"]
    cached = stats["cached_input_tokens"]
    uncached = max(0, total_input - cached)
    stats["total_input_tokens"] = total_input
    stats["uncached_input_tokens"] = uncached
    stats["cache_hit_ratio"] = (cached / total_input) if total_input else 0.0
    stats["uncached_ratio"] = (uncached / total_input) if total_input else 0.0
    stats["output_ratio"] = (stats["output_tokens"] / total_input) if total_input else 0.0
    stats["had_image"] = stats["image_count"] > 0
    stats["redundant_reads"] = 0
    stats["unique_files_read"] = 0
    stats["total_file_reads"] = 0
    stats["models"] = sorted(list(stats["models"]))
    stats["tool_use_counter"] = dict(stats["tool_use_counter"])
    return stats


def score_session(s):
    """4-axis 0-100 scoring. Weighted: cache 45 / output 25 / context 20 / tool 10."""
    cache_score = min(100, s["cache_hit_ratio"] / 0.90 * 100)

    od = s["output_ratio"]
    if od < 0.003:
        density_score = od / 0.003 * 55
    elif od < 0.02:
        density_score = 55 + (od - 0.003) / 0.017 * 45
    elif od < 0.06:
        density_score = 100 - (od - 0.02) / 0.04 * 20
    else:
        density_score = max(40, 80 - (od - 0.06) * 200)

    # Lower uncached share means fewer repeated full-context payments.
    context_score = max(0, 100 - s["uncached_ratio"] * 180)

    out_k = max(1, s["output_tokens"] / 1000)
    tpk = s["num_tool_calls"] / out_k
    if tpk < 2:
        tool_score = 75 + tpk * 10
    elif tpk < 12:
        tool_score = 100 - (tpk - 2) * 2
    elif tpk < 24:
        tool_score = 80 - (tpk - 12) * 4
    else:
        tool_score = max(0, 32 - (tpk - 24) * 2)

    composite = (
        cache_score * 0.45
        + density_score * 0.25
        + context_score * 0.20
        + tool_score * 0.10
    )

    return {
        "cache_score": round(cache_score, 1),
        "density_score": round(density_score, 1),
        "redundancy_score": round(context_score, 1),
        "tool_score": round(tool_score, 1),
        "composite": round(composite, 1),
        "grade": grade_of(composite),
    }


def grade_of(score):
    for threshold, grade in [
        (90, "A+"), (85, "A"), (80, "A-"), (75, "B+"), (70, "B"),
        (65, "B-"), (60, "C+"), (55, "C"), (50, "C-"), (40, "D"),
    ]:
        if score >= threshold:
            return grade
    return "F"


def repo_filter(files, repo):
    if not repo:
        return files
    target = os.path.abspath(os.path.expanduser(repo))
    matched = []
    for fp in files:
        try:
            cwd = session_cwd(fp)
            if cwd and cwd == target:
                matched.append(fp)
        except Exception:
            continue
    return matched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", help="Repository path to filter by session cwd. Defaults to current/recent live session cwd.")
    ap.add_argument("--source", choices=["live", "archived", "all"], default="all", help="Session source when --sessions-dir is not set.")
    ap.add_argument("--sessions-dir", help="Direct path to a session directory. Searched recursively.")
    ap.add_argument("--session-index", help="Path to session_index.jsonl for thread names.")
    ap.add_argument("--current-session-file", help="Prefer this JSONL file when auto-detecting the project cwd.")
    ap.add_argument("--out", default="/tmp/codex_session_analysis.json", help="Output JSON path")
    args = ap.parse_args()

    files, sessions_source = discover_session_files(args)
    if not files:
        print(f"[error] no Codex session .jsonl files found in {sessions_source}", file=sys.stderr)
        sys.exit(2)

    repo = args.repo
    detected_from = None
    if not repo:
        repo, detected_from = detect_project_repo(files, args.current_session_file)
        if not repo:
            print("[error] could not auto-detect project cwd; pass --repo <path>", file=sys.stderr)
            sys.exit(2)

    files = repo_filter(files, repo)
    if not files:
        print(f"[error] no matching .jsonl files for repo {repo} in {sessions_source}", file=sys.stderr)
        sys.exit(2)

    session_titles = load_session_index(args.session_index)
    results = []
    for fp in files:
        s = analyze_session(fp, session_titles)
        if s["token_events"] == 0:
            continue
        s["scores"] = score_session(s)
        results.append(s)

    if not results:
        print("[error] matching sessions have no token_count events", file=sys.stderr)
        sys.exit(2)

    totals = {
        "sessions_dir": sessions_source,
        "source": args.source,
        "repo": os.path.abspath(os.path.expanduser(repo)),
        "detected_from": detected_from,
        "sessions": len(results),
        "input_tokens": sum(r["input_tokens"] for r in results),
        "cached_input_tokens": sum(r["cached_input_tokens"] for r in results),
        "output_tokens": sum(r["output_tokens"] for r in results),
        "reasoning_output_tokens": sum(r["reasoning_output_tokens"] for r in results),
        "cache_create_5m": 0,
        "cache_create_1h": 0,
        "cache_read": sum(r["cache_read"] for r in results),
        "cost_usd": sum(r["cost_usd"] for r in results),
        "total_input_tokens": sum(r["total_input_tokens"] for r in results),
        "total_tokens": sum(r["total_tokens"] for r in results),
        "num_tool_calls": sum(r["num_tool_calls"] for r in results),
        "redundant_reads": 0,
        "image_count": sum(r["image_count"] for r in results),
        "compact_count": 0,
        "large_output_events": sum(r["large_output_events"] for r in results),
    }
    totals["cache_hit_ratio"] = (
        totals["cached_input_tokens"] / totals["input_tokens"] if totals["input_tokens"] else 0
    )

    results.sort(key=lambda r: r["total_tokens"], reverse=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"totals": totals, "sessions": results}, f, default=str, indent=2)

    print(f"[ok] wrote {args.out}")
    print(
        f"     {len(results)} sessions, {totals['total_tokens']:,} tokens, "
        f"cached input {totals['cache_hit_ratio']*100:.1f}%"
    )


if __name__ == "__main__":
    main()
