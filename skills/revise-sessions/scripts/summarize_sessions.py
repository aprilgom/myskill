#!/usr/bin/env python3
"""Summarize recent Codex user prompts for repeated workflow discovery."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


KEYWORDS = {
    "ci": [r"\bci\b", r"\bworkflow\b", r"github action", r"build failed", r"실패"],
    "pr-review": [r"\bpr\b", r"pull request", r"\breview\b", r"리뷰"],
    "changelog": [r"changelog", r"release note", r"변경log", r"변경 로그"],
    "docs": [r"\bdocs\b", r"documentation", r"readme", r"agents\.md", r"문서"],
    "release": [r"\brelease\b", r"\bpublish\b", r"배포", r"릴리즈"],
    "debugging": [r"\bdebug\b", r"diagnose", r"broken", r"\berror\b", r"failing", r"버그", r"고쳐", r"깨져"],
    "test-triage": [r"\btest\b", r"cargo test", r"pytest", r"snapshot", r"triage", r"테스트"],
    "skills": [r"\bskill\b", r"스킬", r"subagent", r"\bagent\b", r"에이전트"],
}

STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "from", "내", "좀", "해줘", "만들어줘",
    "수", "있어", "어떻게", "왜", "이", "그", "저", "를", "을", "은", "는",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser.add_argument("--days", type=int, default=21)
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def cutoff_ts(days: int) -> float:
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).timestamp()


def parse_time(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def iter_jsonl(path: Path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield line_no, json.loads(line)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return


def extract_input_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") in {"input_text", "text"}:
                parts.append(str(item.get("text", "")))
        return "\n".join(part for part in parts if part)
    return ""


def history_records(codex_home: Path, since: float):
    for line_no, row in iter_jsonl(codex_home / "history.jsonl"):
        ts = parse_time(row.get("ts"))
        if ts is not None and ts < since:
            continue
        text = row.get("text", "").strip()
        if text:
            yield {
                "ts": ts,
                "session_id": row.get("session_id", "unknown"),
                "source": f"history.jsonl:{line_no}",
                "text": text,
            }


def archived_records(codex_home: Path, since: float):
    for path in sorted((codex_home / "archived_sessions").glob("*.jsonl")):
        session_id = path.stem
        for line_no, row in iter_jsonl(path):
            ts = parse_time(row.get("timestamp"))
            if ts is not None and ts < since:
                continue
            payload = row.get("payload") or {}
            if row.get("type") != "response_item":
                continue
            if payload.get("type") != "message" or payload.get("role") != "user":
                continue
            text = extract_input_text(payload.get("content")).strip()
            if text.startswith("<environment_context>") or text.startswith("# AGENTS.md instructions"):
                continue
            if text:
                yield {
                    "ts": ts,
                    "session_id": payload.get("id") or session_id,
                    "source": f"{path.name}:{line_no}",
                    "text": text,
                }


def normalize(text: str) -> str:
    lowered = re.sub(r"`[^`]+`", " ", text.lower())
    lowered = re.sub(r"https?://\S+|/[^\s]+|\b[0-9a-f]{7,}\b", " ", lowered)
    words = re.findall(r"[a-z0-9_+-]+|[가-힣]+", lowered)
    kept = [word for word in words if len(word) > 1 and word not in STOPWORDS]
    return " ".join(kept[:12])


def tags_for(text: str) -> list[str]:
    lowered = text.lower()
    tags = []
    for tag, needles in KEYWORDS.items():
        if any(re.search(needle, lowered) for needle in needles):
            tags.append(tag)
    return tags or ["other"]


def build_report(records: list[dict], limit: int) -> dict:
    seen = set()
    unique = []
    for record in records:
        key = (record["session_id"], record["text"])
        if key not in seen:
            seen.add(key)
            unique.append(record)

    by_norm = defaultdict(list)
    tag_counter = Counter()
    for record in unique:
        record["tags"] = tags_for(record["text"])
        for tag in record["tags"]:
            tag_counter[tag] += 1
        by_norm[normalize(record["text"])].append(record)

    repeated = [
        {"key": key, "count": len(items), "examples": items[:5]}
        for key, items in by_norm.items()
        if key and len(items) > 1
    ]
    repeated.sort(key=lambda item: item["count"], reverse=True)

    tagged_examples = defaultdict(list)
    for record in unique:
        for tag in record["tags"]:
            if len(tagged_examples[tag]) < 8:
                tagged_examples[tag].append(record)

    return {
        "total_prompts": len(unique),
        "tag_counts": dict(tag_counter.most_common()),
        "repeated_exactish": repeated[:20],
        "tagged_examples": dict(tagged_examples),
        "recent_examples": unique[-limit:],
    }


def print_markdown(report: dict) -> None:
    print("# Recent Codex Session Patterns")
    print()
    print(f"Prompts scanned: {report['total_prompts']}")
    print()
    print("## Topic Counts")
    for tag, count in report["tag_counts"].items():
        print(f"- {tag}: {count}")
    print()
    print("## Repeated Similar Prompts")
    if not report["repeated_exactish"]:
        print("- No exact-ish repeats found; inspect topic examples for intent-level repeats.")
    for item in report["repeated_exactish"]:
        print(f"- {item['count']}x `{item['key']}`")
        for example in item["examples"][:3]:
            print(f"  - {example['source']} {example['text'][:180]}")
    print()
    print("## Practical Topic Examples")
    for tag, examples in report["tagged_examples"].items():
        if tag == "other":
            continue
        print(f"### {tag}")
        for example in examples[:5]:
            print(f"- {example['source']} {example['text'][:220]}")


def main() -> int:
    args = parse_args()
    codex_home = Path(args.codex_home).expanduser()
    since = cutoff_ts(args.days)
    records = list(history_records(codex_home, since))
    records.extend(archived_records(codex_home, since))
    records.sort(key=lambda item: item["ts"] or 0)
    report = build_report(records, args.limit)
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_markdown(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
