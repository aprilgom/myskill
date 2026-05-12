#!/usr/bin/env python3
"""Detect common Codex session inefficiency patterns.

Usage:
  python3 detect_patterns.py --repo /path/to/repo --out /tmp/codex_pattern_analysis.json
"""
import argparse
import glob
import json
import os
import sys


def resolve_sessions_dir(args):
    return os.path.expanduser(args.sessions_dir or "~/.codex/archived_sessions")


def repo_matches(path, repo):
    if not repo:
        return True
    target = os.path.abspath(os.path.expanduser(repo))
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            rec = json.loads(f.readline())
        cwd = (rec.get("payload") or {}).get("cwd")
        return bool(cwd and os.path.abspath(os.path.expanduser(cwd)) == target)
    except Exception:
        return False


def content_len(content):
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(len(i.get("text", "")) for i in content if isinstance(i, dict))
    return 0


def empty_pattern(evidence):
    return {"triggered": False, "waste_tokens": 0, "waste_usd": 0.0, "evidence": evidence}


def analyze_session(path):
    sid = os.path.basename(path).replace(".jsonl", "")
    cwd = None
    token_turns = []
    large_outputs = []
    tool_calls = 0
    assistant_messages = 0
    total_tokens = 0

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for idx, line in enumerate(f):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue

            rtype = rec.get("type")
            payload = rec.get("payload") or {}
            if rtype == "session_meta":
                cwd = payload.get("cwd")
            elif rtype == "event_msg":
                ptype = payload.get("type")
                if ptype == "token_count":
                    usage = ((payload.get("info") or {}).get("last_token_usage") or {})
                    if usage:
                        inp = usage.get("input_tokens", 0) or 0
                        cached = usage.get("cached_input_tokens", 0) or 0
                        out = usage.get("output_tokens", 0) or 0
                        total = usage.get("total_tokens", 0) or (inp + out)
                        token_turns.append({"idx": idx, "input": inp, "cached": cached, "output": out, "total": total})
                        total_tokens += total
                elif ptype == "agent_message":
                    assistant_messages += 1
                    msg_len = len(payload.get("message") or "")
                    if msg_len >= 50_000:
                        large_outputs.append({"idx": idx, "chars": msg_len})
                elif ptype in {"exec_command", "tool_call", "mcp_tool_call"}:
                    tool_calls += 1

            elif rtype == "response_item":
                size = content_len(payload.get("content"))
                if size >= 50_000:
                    large_outputs.append({"idx": idx, "chars": size})

    if not token_turns:
        return None

    findings = {}
    max_input = max(t["input"] for t in token_turns)
    low_cache = [t for t in token_turns if t["input"] > 30_000 and (t["cached"] / t["input"] if t["input"] else 0) < 0.50]
    high_context = [t for t in token_turns if t["input"] > 100_000]
    high_reasoning = [t for t in token_turns if t["output"] > 8_000]
    tool_per_output = tool_calls / max(1, sum(t["output"] for t in token_turns) / 1000)

    findings["context_bloat"] = (
        {
            "triggered": True,
            "waste_tokens": sum(max(0, t["input"] - 80_000) for t in high_context),
            "waste_usd": 0.0,
            "evidence": f"{len(high_context)} token_count events above 100k input tokens",
        }
        if high_context else empty_pattern(f"max input tokens {max_input:,}")
    )

    findings["giant_tool_outputs"] = (
        {
            "triggered": True,
            "waste_tokens": sum(o["chars"] // 4 for o in large_outputs),
            "waste_usd": 0.0,
            "evidence": f"{len(large_outputs)} response/tool outputs above 50k chars",
        }
        if large_outputs else empty_pattern("no response/tool output above 50k chars")
    )

    findings["poor_cache_util"] = (
        {
            "triggered": True,
            "waste_tokens": sum(t["input"] - t["cached"] for t in low_cache),
            "waste_usd": 0.0,
            "evidence": f"{len(low_cache)} token_count events with cache hit <50% at input >30k",
        }
        if low_cache else empty_pattern("no large low-cache token_count events")
    )

    findings["duplicate_tools"] = empty_pattern("Codex logs do not expose stable tool input hashes consistently")

    findings["subagent_overuse"] = (
        {
            "triggered": True,
            "waste_tokens": int((tool_per_output - 20) * 1000),
            "waste_usd": 0.0,
            "evidence": f"{tool_calls} tool calls, {tool_per_output:.1f} calls per 1k output tokens",
        }
        if tool_per_output > 20 else empty_pattern(f"{tool_per_output:.1f} tool calls per 1k output tokens")
    )

    findings["reasoning_spikes"] = (
        {
            "triggered": True,
            "waste_tokens": sum(max(0, t["output"] - 8_000) for t in high_reasoning),
            "waste_usd": 0.0,
            "evidence": f"{len(high_reasoning)} events above 8k output tokens",
        }
        if high_reasoning else empty_pattern("no large output-token spikes")
    )

    return {
        "session_id": sid,
        "cwd": cwd,
        "total_tokens": total_tokens,
        "tool_calls": tool_calls,
        "assistant_messages": assistant_messages,
        "patterns": findings,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", help="Repo path to filter by session cwd")
    ap.add_argument("--sessions-dir", help="Direct path to ~/.codex/archived_sessions/")
    ap.add_argument("--out", default="/tmp/codex_pattern_analysis.json")
    args = ap.parse_args()

    sessions_dir = resolve_sessions_dir(args)
    files = sorted(glob.glob(os.path.join(sessions_dir, "*.jsonl")))
    files = [fp for fp in files if repo_matches(fp, args.repo)]
    if not files:
        print(f"[error] no matching .jsonl files in {sessions_dir}", file=sys.stderr)
        sys.exit(2)

    sessions = [s for fp in files if (s := analyze_session(fp))]
    if not sessions:
        print("[error] no token_count events found", file=sys.stderr)
        sys.exit(2)

    pattern_keys = ["context_bloat", "giant_tool_outputs", "poor_cache_util", "duplicate_tools", "subagent_overuse", "reasoning_spikes"]
    totals = {
        "sessions_total": len(sessions),
        "sessions_with_any_pattern": 0,
        "total_waste_tokens": 0,
        "total_waste_usd": 0.0,
        "patterns": {},
    }
    for key in pattern_keys:
        affected = [s for s in sessions if s["patterns"][key]["triggered"]]
        waste = sum(s["patterns"][key]["waste_tokens"] for s in affected)
        totals["patterns"][key] = {
            "affected_sessions": len(affected),
            "total_waste_tokens": waste,
            "total_waste_usd": 0.0,
        }
        totals["total_waste_tokens"] += waste

    totals["sessions_with_any_pattern"] = sum(
        1 for s in sessions if any(p["triggered"] for p in s["patterns"].values())
    )

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"totals": totals, "sessions": sessions}, f, indent=2)

    print(f"[ok] wrote {args.out}")
    print(f"     {totals['sessions_total']} sessions, {totals['total_waste_tokens']:,} estimated waste tokens")


if __name__ == "__main__":
    main()
