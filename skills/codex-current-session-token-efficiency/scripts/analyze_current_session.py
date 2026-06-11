#!/usr/bin/env python3
"""Analyze token usage for one current Codex session JSONL.

This script intentionally avoids project-wide aggregation. It selects a single
live session by explicit --session-file, --thread-id, or newest matching repo
cwd, then ranks token events and coarse phases by total tokens.
"""
import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path


def codex_home():
    return Path.home() / ".codex"


def session_key(path):
    base = Path(path).name.removesuffix(".jsonl")
    idx = base.find("-019")
    return base[idx + 1 :] if idx >= 0 else base


def iter_jsonl(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                yield line_no, json.loads(line)
            except Exception:
                continue


def session_cwd(path):
    for _, rec in iter_jsonl(path):
        if rec.get("type") == "session_meta":
            return (rec.get("payload") or {}).get("cwd")
    return None


def live_session_files():
    root = codex_home() / "sessions"
    return sorted(glob.glob(str(root / "**" / "*.jsonl"), recursive=True))


def find_session(args):
    if args.session_file:
        path = os.path.abspath(os.path.expanduser(args.session_file))
        if not os.path.exists(path):
            raise SystemExit(f"session file not found: {path}")
        return path

    files = live_session_files()
    if args.thread_id:
        for path in files:
            if args.thread_id in path or session_key(path) == args.thread_id:
                return path
        for path in files:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    if args.thread_id in f.read():
                        return path
            except Exception:
                pass
        raise SystemExit(f"thread id not found in live sessions: {args.thread_id}")

    candidates = files
    if args.repo:
        repo = os.path.abspath(os.path.expanduser(args.repo))
        candidates = [
            path for path in files
            if session_cwd(path) and os.path.abspath(os.path.expanduser(session_cwd(path))) == repo
        ]
    if not candidates:
        raise SystemExit("no matching current live session found")
    return max(candidates, key=os.path.getmtime)


def usage_from_record(rec):
    payload = rec.get("payload") or {}
    if not isinstance(payload, dict):
        return None
    info = payload.get("info") or {}
    if isinstance(info, dict) and info.get("last_token_usage"):
        return info["last_token_usage"]
    msg = payload.get("msg")
    if isinstance(msg, dict):
        info = msg.get("info") or {}
        if isinstance(info, dict) and info.get("last_token_usage"):
            return info["last_token_usage"]
    return None


def text_from_record(rec):
    payload = rec.get("payload") or {}
    texts = []
    if isinstance(payload, dict):
        for key in ("message", "delta"):
            if isinstance(payload.get(key), str):
                texts.append(payload[key])
        msg = payload.get("msg")
        if isinstance(msg, dict):
            for key in ("message", "delta"):
                if isinstance(msg.get(key), str):
                    texts.append(msg[key])
    if isinstance(rec.get("message"), str):
        texts.append(rec["message"])
    return " ".join(texts).replace("\n", " ").strip()


def classify_phase(label):
    lower = label.lower()
    if any(s in lower for s in ("token", "토큰", "session log", "세션 로그")):
        return "token-analysis"
    if any(s in lower for s in ("완료", "complete", "freshness", "goal", "completed")):
        return "completion-and-verification"
    if any(s in lower for s in ("subagent", "위임", "worker")):
        return "subagent-review"
    if any(s in lower for s in ("go test", "wc -l", "diff", "파일 크기", "test")):
        return "tests-and-inspection"
    if any(s in lower for s in ("skill", "roi", "워크트리", "current work", "plan")):
        return "initial-scope-discovery"
    return "other"


def waste_signals(label, usage):
    signals = []
    lower = label.lower()
    if "499 sessions" in lower or "project" in lower and "current" in lower:
        signals.append("possible scope mismatch")
    if any(s in lower for s in ("rg -n", "find ", "git diff", "wc -l")):
        signals.append("broad tool-output context")
    if any(s in lower for s in ("go test ./...", "전체 테스트")):
        signals.append("broad verification")
    if any(s in lower for s in ("spawn_agent", "wait_agent", "subagent_notification", "subagent 위임")):
        signals.append("subagent overhead")
    uncached = usage["input_tokens"] - usage["cached_input_tokens"]
    if uncached > 10_000:
        signals.append("high uncached input")
    return signals


def add_totals(target, usage):
    for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "total_tokens"):
        target[key] = target.get(key, 0) + int(usage.get(key, 0) or 0)


def analyze(path):
    messages = []
    events = []
    totals = {}
    for line_no, rec in iter_jsonl(path):
        text = text_from_record(rec)
        if text:
            messages.append({"line": line_no, "text": text[:300]})
        usage = usage_from_record(rec)
        if not usage:
            continue
        normalized = {
            "input_tokens": int(usage.get("input_tokens", 0) or 0),
            "cached_input_tokens": int(usage.get("cached_input_tokens", 0) or 0),
            "output_tokens": int(usage.get("output_tokens", 0) or 0),
            "reasoning_output_tokens": int(usage.get("reasoning_output_tokens", 0) or 0),
            "total_tokens": int(usage.get("total_tokens", 0) or 0),
        }
        add_totals(totals, normalized)
        recent = [m for m in messages if m["line"] < line_no][-4:]
        label = recent[-1]["text"] if recent else f"token event at line {line_no}"
        phase = classify_phase(" ".join(m["text"] for m in recent))
        events.append({
            "line": line_no,
            "phase": phase,
            "label": label,
            "recent_messages": recent,
            "usage": normalized,
            "waste_signals": waste_signals(" ".join(m["text"] for m in recent), normalized),
        })

    phase_totals = {}
    for event in events:
        phase = event["phase"]
        phase_totals.setdefault(phase, {})
        add_totals(phase_totals[phase], event["usage"])
        phase_totals[phase]["events"] = phase_totals[phase].get("events", 0) + 1

    return {
        "session_file": path,
        "thread_id": session_key(path),
        "cwd": session_cwd(path),
        "totals": totals,
        "phase_totals": sorted(
            [{"phase": phase, **stats} for phase, stats in phase_totals.items()],
            key=lambda row: row.get("total_tokens", 0),
            reverse=True,
        ),
        "events": sorted(events, key=lambda row: row["usage"]["total_tokens"], reverse=True),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", help="Repo cwd used only to select the newest matching live session")
    parser.add_argument("--thread-id", help="Exact Codex thread/session id")
    parser.add_argument("--session-file", help="Exact session JSONL path")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout")
    args = parser.parse_args()

    path = find_session(args)
    result = analyze(path)
    data = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out == "-":
        print(data)
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(data + "\n")
        print(f"[ok] wrote {args.out}")
        print(
            f"     {result['thread_id']}: "
            f"{result['totals'].get('total_tokens', 0):,} tokens, "
            f"cached input {result['totals'].get('cached_input_tokens', 0):,}"
        )


if __name__ == "__main__":
    main()
