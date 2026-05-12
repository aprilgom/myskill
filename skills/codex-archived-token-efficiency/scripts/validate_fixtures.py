#!/usr/bin/env python3
"""Deterministic smoke tests for Codex token analysis scripts."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ANALYZE = SCRIPT_DIR / "analyze_sessions.py"
BUILD_DASHBOARD = SCRIPT_DIR / "build_dashboard.py"


def write_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")


def token_event(input_tokens, cached_input_tokens, output_tokens, total_tokens, total_token_usage=None):
    info = {
        "last_token_usage": {
            "input_tokens": input_tokens,
            "cached_input_tokens": cached_input_tokens,
            "output_tokens": output_tokens,
            "reasoning_output_tokens": 0,
            "total_tokens": total_tokens,
        }
    }
    if total_token_usage:
        info["total_token_usage"] = total_token_usage
    return {"type": "event_msg", "payload": {"type": "token_count", "info": info}}


def run(cmd, expect_ok=True):
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if expect_ok and proc.returncode != 0:
        raise AssertionError(f"command failed: {' '.join(cmd)}\n{proc.stderr}\n{proc.stdout}")
    if not expect_ok and proc.returncode == 0:
        raise AssertionError(f"command unexpectedly passed: {' '.join(cmd)}\n{proc.stdout}")
    return proc


def assert_eq(actual, expected, label):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def main():
    repo_a = os.path.abspath("/tmp/codex-fixture-repo-a")
    repo_b = os.path.abspath("/tmp/codex-fixture-repo-b")
    with tempfile.TemporaryDirectory() as tmp:
        sessions_dir = Path(tmp) / "sessions"
        sessions_dir.mkdir()

        write_jsonl(
            sessions_dir / "a.jsonl",
            [
                {"type": "session_meta", "payload": {"cwd": repo_a, "model": "gpt-5.3-codex"}},
                token_event(100, 40, 10, 110, {"input_tokens": 10_000, "output_tokens": 1_000, "total_tokens": 11_000}),
                token_event(200, 100, 20, 220, {"input_tokens": 20_000, "output_tokens": 2_000, "total_tokens": 22_000}),
                *[
                    {"type": "event_msg", "payload": {"type": "exec_command", "name": "exec_command"}}
                    for _ in range(25)
                ],
                {"type": "event_msg", "payload": {"type": "agent_message", "message": "x" * 50_001}},
            ],
        )
        write_jsonl(
            sessions_dir / "b.jsonl",
            [
                {"type": "session_meta", "payload": {"cwd": repo_b, "model": "gpt-5.3-codex"}},
                token_event(1_000, 900, 100, 1_100),
            ],
        )
        write_jsonl(
            sessions_dir / "no-token.jsonl",
            [
                {"type": "session_meta", "payload": {"cwd": repo_a, "model": "gpt-5.3-codex"}},
                {"type": "event_msg", "payload": {"type": "agent_message", "message": "no token_count here"}},
            ],
        )

        out = Path(tmp) / "analysis.json"
        run([sys.executable, str(ANALYZE), "--sessions-dir", str(sessions_dir), "--repo", repo_a, "--out", str(out)])
        with open(out, encoding="utf-8") as f:
            data = json.load(f)

        totals = data["totals"]
        assert_eq(totals["sessions"], 1, "repo filtering and no-token skip")
        assert_eq(totals["input_tokens"], 300, "last_token_usage input sum")
        assert_eq(totals["cached_input_tokens"], 140, "last_token_usage cached sum")
        assert_eq(totals["output_tokens"], 30, "last_token_usage output sum")
        assert_eq(totals["total_tokens"], 330, "last_token_usage total sum")
        assert_eq(totals["large_output_events"], 1, "large output event count")

        no_match = run(
            [sys.executable, str(ANALYZE), "--sessions-dir", str(sessions_dir), "--repo", "/tmp/no-match", "--out", str(Path(tmp) / "none.json")],
            expect_ok=False,
        )
        if "no matching .jsonl files" not in no_match.stderr:
            raise AssertionError("missing repo-filter failure message")

        dashboard = Path(tmp) / "dashboard.html"
        run([sys.executable, str(BUILD_DASHBOARD), "--input", str(out), "--out", str(dashboard), "--repo-name", "fixture"])
        html = dashboard.read_text(encoding="utf-8")
        for expected in ["Bound large outputs", "Reduce tool-call thrash", "fixture"]:
            if expected not in html:
                raise AssertionError(f"dashboard missing dynamic recommendation/text: {expected}")

    print("[ok] fixture validation passed")


if __name__ == "__main__":
    main()
