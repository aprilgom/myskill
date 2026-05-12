#!/usr/bin/env python3
"""Polyglot maintainability risk scanner for code-cartography."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


SCHEMA_VERSION = "1.0"
MODE = "heuristic baseline + manual maintainability review"

CODE_EXTENSIONS = {
    ".c",
    ".cc",
    ".clj",
    ".cljs",
    ".cpp",
    ".cs",
    ".cxx",
    ".dart",
    ".erl",
    ".ex",
    ".exs",
    ".fs",
    ".fsx",
    ".go",
    ".h",
    ".hpp",
    ".hrl",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".lua",
    ".m",
    ".mm",
    ".php",
    ".py",
    ".r",
    ".rb",
    ".rs",
    ".scala",
    ".sh",
    ".sql",
    ".svelte",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
}

SKIP_DIRS = {
    ".cache",
    ".git",
    ".hg",
    ".mypy_cache",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "bin",
    "bower_components",
    "build",
    "coverage",
    "deps",
    "dist",
    "generated",
    "node_modules",
    "obj",
    "out",
    "pkg",
    "target",
    "vendor",
    "vendors",
    "venv",
}

LOCK_OR_MANIFEST_FILES = {
    "cargo.lock",
    "composer.lock",
    "go.sum",
    "package-lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "yarn.lock",
}

GENERATED_MARKERS = {
    ".g.dart",
    ".generated.",
    ".pb.",
    ".pb2.",
    ".schema.",
    ".snap",
    "_generated.",
    "generated",
}

TEST_MARKERS = {
    "__specs__",
    "__tests__",
    "spec",
    "specs",
    "test",
    "tests",
}

DEBT_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX|workaround|temporary|legacy|deprecated)\b", re.I)
BRANCH_RE = re.compile(
    r"\b(if|elif|else\s+if|for|foreach|while|switch|case|catch|except|rescue|match|when|guard|unless)\b|&&|\|\|"
)
FUNCTION_RE = re.compile(
    r"^\s*(def\s+\w+|function\s+\w+|class\s+\w+|func\s+\w+|fn\s+\w+|"
    r"(public|private|protected|static|async|export)\s+.*\([^)]*\)\s*[{=:]|"
    r"const\s+\w+\s*=\s*(async\s*)?\([^)]*\)\s*=>)"
)
IMPORT_PATTERNS = [
    re.compile(r"^\s*import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]"),
    re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]"),
    re.compile(r"\brequire\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"),
    re.compile(r"^\s*from\s+([.\w]+)\s+import\b"),
    re.compile(r"^\s*import\s+([.\w]+)\b"),
    re.compile(r"^\s*use\s+([\w:]+)"),
    re.compile(r"^\s*import\s+([\w.]+);"),
    re.compile(r"^\s*#\s*include\s+[<\"]([^>\"]+)[>\"]"),
    re.compile(r"^\s*require\s+['\"]([^'\"]+)['\"]"),
]

CONCERNS = {
    "async": {"event", "job", "lock", "message", "publish", "queue", "subscribe", "thread", "worker"},
    "auth": {"auth", "password", "permission", "role", "session", "token"},
    "config": {"config", "env", "flag", "setting"},
    "notification": {"email", "mail", "notify", "push", "sms"},
    "persistence": {"database", "db", "load", "migration", "model", "orm", "query", "repo", "repository", "save", "sql", "store"},
    "transport": {"api", "client", "controller", "graphql", "grpc", "http", "request", "response", "route", "server"},
    "ui": {"button", "component", "css", "html", "page", "props", "render", "screen", "view"},
    "validation": {"normalize", "parse", "sanitize", "schema", "validate"},
}

SIDE_EFFECT_RE = re.compile(
    r"\b(write|save|update|delete|insert|exec|spawn|fetch|request|open|connect|send|publish|commit|transaction|sql|http|db|queue|socket)\b",
    re.I,
)
ERROR_RE = re.compile(
    r"\b(try|catch|except|rescue|finally|throw|raise|panic|error|err|guard|defer|ensure|Result|Either|Option)\b"
)
COMMENT_PREFIXES = ("#", "//", "/*", "*", "--")
MAX_TEXT_BYTES = 1_000_000


@dataclass
class CodeFile:
    path: Path
    rel_path: str
    text: str
    is_test: bool
    loc: int = 0
    comment_lines: int = 0
    import_targets: list[str] = field(default_factory=list)
    branch_count: int = 0
    max_nesting: int = 0
    long_blocks: int = 0
    todo_count: int = 0
    error_markers: int = 0
    side_effect_markers: int = 0
    concerns: list[str] = field(default_factory=list)
    duplicate_line_hits: int = 0
    has_nearby_test: bool = False
    fan_in: int = 0
    risk_score: float = 0.0
    risk_reasons: list[str] = field(default_factory=list)

    @property
    def import_count(self) -> int:
        return len(self.import_targets)

    @property
    def branch_density(self) -> float:
        return self.branch_count / max(1, self.loc)


def is_probably_binary(raw: bytes) -> bool:
    return b"\0" in raw[:4096]


def is_code_path(path: Path) -> bool:
    if path.name.lower() in LOCK_OR_MANIFEST_FILES:
        return False
    if path.suffix.lower() not in CODE_EXTENSIONS:
        return False
    if path.name.endswith((".min.js", ".min.css")):
        return False
    lowered = str(path).lower()
    return not any(marker in lowered for marker in GENERATED_MARKERS)


def is_test_path(rel_path: str) -> bool:
    lowered = rel_path.lower()
    parts = set(Path(lowered).parts)
    name = Path(lowered).name
    if parts & TEST_MARKERS:
        return True
    return any(
        marker in name
        for marker in (
            ".test.",
            ".spec.",
            "_test.",
            "_spec.",
            "test_",
            "spec_",
        )
    )


def iter_source_files(root: Path) -> tuple[list[Path], list[dict[str, str]], int]:
    files: list[Path] = []
    gaps: list[dict[str, str]] = []
    excluded = 0
    for current, dirs, names in os.walk(root):
        current_path = Path(current)
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS and not d.startswith(".")]
        for name in names:
            path = current_path / name
            rel = path.relative_to(root)
            if path.name.lower() in LOCK_OR_MANIFEST_FILES:
                excluded += 1
                continue
            if not is_code_path(rel):
                if path.suffix.lower() in CODE_EXTENSIONS:
                    excluded += 1
                continue
            try:
                size = path.stat().st_size
            except OSError as exc:
                gaps.append({"path": str(rel), "reason": f"stat failed: {exc}"})
                continue
            if size > MAX_TEXT_BYTES:
                gaps.append({"path": str(rel), "reason": "file exceeds scanner size limit"})
                continue
            files.append(path)
    return files, gaps, excluded


def safe_read(path: Path, root: Path, gaps: list[dict[str, str]]) -> str | None:
    rel = path.relative_to(root)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        gaps.append({"path": str(rel), "reason": f"read failed: {exc}"})
        return None
    if is_probably_binary(raw):
        gaps.append({"path": str(rel), "reason": "binary content"})
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return raw.decode("latin-1")
        except UnicodeDecodeError as exc:
            gaps.append({"path": str(rel), "reason": f"text decode failed: {exc}"})
            return None


def extract_imports(lines: Iterable[str]) -> list[str]:
    imports: list[str] = []
    in_go_group = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("import ("):
            in_go_group = True
            continue
        if in_go_group:
            if stripped == ")":
                in_go_group = False
                continue
            imports.extend(re.findall(r"['\"]([^'\"]+)['\"]", stripped))
            continue
        for pattern in IMPORT_PATTERNS:
            match = pattern.search(line)
            if match:
                imports.append(match.group(1))
                break
    return imports


def estimate_nesting(lines: Iterable[str]) -> int:
    max_indent = 0
    brace_depth = 0
    max_brace = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(COMMENT_PREFIXES):
            continue
        leading = len(line) - len(line.lstrip(" "))
        max_indent = max(max_indent, leading // 4)
        for char in line:
            if char == "{":
                brace_depth += 1
                max_brace = max(max_brace, brace_depth)
            elif char == "}":
                brace_depth = max(0, brace_depth - 1)
    return max(max_indent, max_brace)


def count_long_blocks(lines: list[str]) -> int:
    starts = [i for i, line in enumerate(lines) if FUNCTION_RE.search(line)]
    if not starts:
        return 1 if len([line for line in lines if line.strip()]) > 120 else 0
    spans: list[int] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(lines)
        span = len([line for line in lines[start:end] if line.strip()])
        spans.append(span)
    return sum(1 for span in spans if span > 80)


def find_concerns(rel_path: str, text: str) -> list[str]:
    haystack = f"{rel_path}\n{text[:20000]}".lower()
    found = []
    for name, words in CONCERNS.items():
        if any(re.search(rf"\b{re.escape(word)}\b", haystack) for word in words):
            found.append(name)
    return found


def analyze_file(path: Path, root: Path, text: str) -> CodeFile:
    rel_path = str(path.relative_to(root))
    lines = text.splitlines()
    code_lines = []
    comment_lines = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(COMMENT_PREFIXES):
            comment_lines += 1
        else:
            code_lines.append(line)
    code = "\n".join(code_lines)
    return CodeFile(
        path=path,
        rel_path=rel_path,
        text=text,
        is_test=is_test_path(rel_path),
        loc=len(code_lines),
        comment_lines=comment_lines,
        import_targets=extract_imports(lines),
        branch_count=len(BRANCH_RE.findall(code)),
        max_nesting=estimate_nesting(lines),
        long_blocks=count_long_blocks(lines),
        todo_count=len(DEBT_RE.findall(text)),
        error_markers=len(ERROR_RE.findall(text)),
        side_effect_markers=len(SIDE_EFFECT_RE.findall(text)),
        concerns=find_concerns(rel_path, text),
    )


TEST_NAME_SUFFIXES = (
    "tests",
    "test",
    "specs",
    "spec",
)

SOURCE_ROOT_MARKERS = {
    "app",
    "apps",
    "assets",
    "cmd",
    "editor",
    "features",
    "lib",
    "main",
    "pkg",
    "runtime",
    "scripts",
    "src",
    "source",
}

TEST_ROOT_MARKERS = TEST_MARKERS | {
    "editmode",
    "playmode",
    "testing",
}


def normalized_test_stem(path: str) -> str:
    name = Path(path).stem.lower()
    for token in (".test", ".spec", "_test", "_spec"):
        name = name.replace(token, "")
    for prefix in ("test_", "spec_"):
        if name.startswith(prefix):
            name = name[len(prefix) :]
    for suffix in TEST_NAME_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            name = name[: -len(suffix)]
    return name


def normalized_path_parts(path: str) -> tuple[str, ...]:
    return tuple(part.lower() for part in Path(path).with_suffix("").parts)


def comparable_path_tail(path: str, is_test: bool) -> tuple[str, ...]:
    parts = list(normalized_path_parts(path))
    if not parts:
        return tuple()

    parts[-1] = normalized_test_stem(path)
    ignored = TEST_ROOT_MARKERS if is_test else SOURCE_ROOT_MARKERS
    filtered = [part for part in parts if part not in ignored]

    # Keep the tail only. This makes common mirrored layouts comparable:
    # src/domain/foo.py <-> tests/domain/test_foo.py
    # Assets/Scripts/Editor/Foo.cs <-> Assets/Tests/EditMode/FooTests.cs
    return tuple(filtered[-3:])


def path_tails_match(source_tail: tuple[str, ...], test_tail: tuple[str, ...]) -> bool:
    if not source_tail or not test_tail:
        return False
    max_len = min(len(source_tail), len(test_tail))
    for length in range(max_len, 0, -1):
        if source_tail[-length:] == test_tail[-length:]:
            return True
    return False


def mark_test_proximity(files: list[CodeFile]) -> None:
    test_stems = {normalized_test_stem(f.rel_path) for f in files if f.is_test}
    test_dirs = {str(Path(f.rel_path).parent) for f in files if f.is_test}
    test_tails = [comparable_path_tail(f.rel_path, is_test=True) for f in files if f.is_test]
    for file in files:
        if file.is_test:
            file.has_nearby_test = True
            continue
        stem = normalized_test_stem(file.rel_path)
        parent = str(Path(file.rel_path).parent)
        source_tail = comparable_path_tail(file.rel_path, is_test=False)
        file.has_nearby_test = (
            stem in test_stems
            or parent in test_dirs
            or any(path_tails_match(source_tail, test_tail) for test_tail in test_tails)
        )


def module_key(path: str) -> str:
    rel = Path(path)
    return str(rel.with_suffix("")).replace(os.sep, "/").lower()


def import_key(target: str) -> str:
    cleaned = target.strip().strip("'\"").replace("\\", "/")
    cleaned = re.sub(r"^(\./|\.\./)+", "", cleaned)
    cleaned = cleaned.split("?")[0]
    return str(Path(cleaned).with_suffix("")).replace(os.sep, "/").lower()


def mark_fan_in(files: list[CodeFile]) -> None:
    keys = {module_key(f.rel_path): f for f in files}
    stems = {Path(key).name: f for key, f in keys.items()}
    fan_in: dict[str, int] = {f.rel_path: 0 for f in files}
    for file in files:
        for target in file.import_targets:
            key = import_key(target)
            target_file = keys.get(key) or stems.get(Path(key).name)
            if target_file and target_file.rel_path != file.rel_path:
                fan_in[target_file.rel_path] += 1
    for file in files:
        file.fan_in = fan_in[file.rel_path]


def normalized_code_line(line: str) -> str:
    stripped = line.strip()
    stripped = re.sub(r"(['\"])(?:\\.|(?!\1).)*\1", '""', stripped)
    stripped = re.sub(r"\b\d+(\.\d+)?\b", "0", stripped)
    stripped = re.sub(r"\s+", " ", stripped)
    return stripped


def mark_duplication(files: list[CodeFile]) -> int:
    owners: dict[str, set[str]] = {}
    for file in files:
        if file.is_test:
            continue
        for line in file.text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(COMMENT_PREFIXES) or len(stripped) < 20:
                continue
            normalized = normalized_code_line(stripped)
            if normalized in {"{", "}", ");", "};"}:
                continue
            owners.setdefault(normalized, set()).add(file.rel_path)
    duplicated = {line: paths for line, paths in owners.items() if len(paths) > 1}
    for file in files:
        file.duplicate_line_hits = sum(1 for paths in duplicated.values() if file.rel_path in paths)
    return len(duplicated)


def add_reason(file: CodeFile, score: float, reason: str) -> float:
    file.risk_reasons.append(reason)
    return score


def mark_risk_scores(files: list[CodeFile]) -> None:
    for file in files:
        if file.is_test:
            continue
        risk = 0.0
        if file.loc > 600:
            risk += add_reason(file, 24, f"very large file ({file.loc} LOC)")
        elif file.loc > 300:
            risk += add_reason(file, 18, f"large file ({file.loc} LOC)")
        elif file.loc > 120:
            risk += add_reason(file, 9, f"moderate file size ({file.loc} LOC)")
        branch_risk = min(22, file.branch_density * 100)
        if file.branch_count >= 3 and branch_risk >= 8:
            risk += add_reason(file, branch_risk, f"branch density {file.branch_density:.2f}")
        import_risk = min(15, file.import_count * 1.5)
        if file.import_count >= 4:
            risk += add_reason(file, import_risk, f"broad import surface ({file.import_count})")
        elif file.import_count:
            risk += import_risk
        if file.todo_count:
            risk += add_reason(file, min(18, file.todo_count * 6), f"debt markers ({file.todo_count})")
        if not file.has_nearby_test:
            risk += add_reason(file, 15, "no nearby test by path/name convention")
        if len(file.concerns) >= 3:
            risk += add_reason(file, 12, "mixed responsibility signals: " + ", ".join(file.concerns[:4]))
        if file.side_effect_markers and file.error_markers == 0:
            risk += add_reason(file, 10, "side-effect markers without visible failure handling")
        if file.duplicate_line_hits:
            risk += add_reason(file, min(10, file.duplicate_line_hits), f"duplicated normalized lines ({file.duplicate_line_hits})")
        if file.max_nesting > 5:
            risk += add_reason(file, 8, f"deep nesting candidate ({file.max_nesting})")
        if file.long_blocks:
            risk += add_reason(file, min(12, file.long_blocks * 8), f"long block candidates ({file.long_blocks})")
        if file.fan_in > 5:
            risk += add_reason(file, min(12, file.fan_in), f"high rough fan-in ({file.fan_in})")
        file.risk_score = min(100.0, risk)


def evidence(path: str, detail: str) -> dict[str, str]:
    return {"path": path, "detail": detail}


def category_score(points: int, penalty: float) -> int:
    return max(0, min(points, round(points - penalty)))


def ratio_penalty(points: int, weighted_bad: float, total: int, factor: float = 1.0) -> float:
    if total <= 0:
        return 0.0
    return min(points, (weighted_bad / max(1.0, total)) * points * factor)


def category_result(cat_id: str, name: str, points: int, score: int, rationale: str, ev: list[dict[str, str]], gaps: list[str]) -> dict[str, object]:
    return {
        "id": cat_id,
        "name": name,
        "points": points,
        "score": score,
        "rationale": rationale,
        "evidence": ev[:8],
        "gaps": gaps[:5],
    }


def build_categories(files: list[CodeFile], duplicate_lines: int, extraction_gaps: list[dict[str, str]], root: Path) -> list[dict[str, object]]:
    sources = [f for f in files if not f.is_test]
    total = len(sources)
    tests = [f for f in files if f.is_test]
    high_complexity = [f for f in sources if f.loc > 300 or f.max_nesting > 5 or f.branch_density > 0.12 or f.long_blocks]
    complexity_weight = sum(
        (2 if f.loc > 600 else 1 if f.loc > 300 else 0)
        + (1 if f.max_nesting > 5 else 0)
        + (1 if f.branch_density > 0.12 else 0)
        + min(2, f.long_blocks)
        for f in sources
    )
    a_score = category_score(20, ratio_penalty(20, complexity_weight, total, 0.75))

    mixed = [f for f in sources if len(f.concerns) >= 3]
    large_mixed = [f for f in mixed if f.loc > 120]
    shape_weight = len(mixed) + len(large_mixed) * 2 + sum(1 for f in sources if f.loc > 600)
    b_score = category_score(15, ratio_penalty(15, shape_weight, total, 0.9))

    broad_imports = [f for f in sources if f.import_count >= 12]
    high_fan_in = [f for f in sources if f.fan_in >= 6]
    deep_relative = [f for f in sources if any(target.startswith("../../") for target in f.import_targets)]
    coupling_weight = len(broad_imports) * 2 + len(high_fan_in) * 2 + len(deep_relative)
    c_score = category_score(15, ratio_penalty(15, coupling_weight, total, 0.8))

    proximity = sum(1 for f in sources if f.has_nearby_test) / max(1, total)
    test_ratio = len(tests) / max(1, total)
    d_score = round(15 * (0.55 * min(1.0, test_ratio / 0.5) + 0.45 * proximity))

    duplicate_files = [f for f in sources if f.duplicate_line_hits > 0]
    duplicate_density = duplicate_lines / max(1, sum(f.loc for f in sources))
    e_penalty = min(10, duplicate_density * 60 + ratio_penalty(10, len(duplicate_files), total, 0.5))
    e_score = category_score(10, e_penalty)

    side_effect_files = [f for f in sources if f.side_effect_markers > 0]
    side_effect_without_errors = [f for f in side_effect_files if f.error_markers == 0]
    f_penalty = ratio_penalty(10, len(side_effect_without_errors), max(1, len(side_effect_files)), 0.8)
    f_score = category_score(10, f_penalty)

    todo_total = sum(f.todo_count for f in sources)
    todo_files = [f for f in sources if f.todo_count]
    hygiene_penalty = min(
        10,
        ratio_penalty(10, len(todo_files), total, 0.6)
        + min(4, todo_total / max(1, total))
        + min(3, len(extraction_gaps)),
    )
    g_score = category_score(10, hygiene_penalty)

    context_files = find_context_files(root)
    h_score = min(5, len(context_files))
    if any("adr" in p.lower() or "architecture" in p.lower() for p in context_files):
        h_score = min(5, h_score + 1)

    return [
        category_result(
            "A",
            "Local Complexity & Readability",
            20,
            a_score,
            f"{len(high_complexity)} of {total} source files show complexity review signals.",
            [evidence(f.rel_path, f"{f.loc} LOC, nesting {f.max_nesting}, branch density {f.branch_density:.2f}, long blocks {f.long_blocks}") for f in high_complexity[:6]],
            ["Scanner estimates complexity from size, branch tokens, nesting, and block starts; confirm with language-aware review for critical files."] if high_complexity else [],
        ),
        category_result(
            "B",
            "Responsibility Focus & File Shape",
            15,
            b_score,
            f"{len(mixed)} source files include mixed responsibility keyword signals.",
            [evidence(f.rel_path, "concerns: " + ", ".join(f.concerns)) for f in mixed[:6]],
            ["Concern keywords are proxies; composition roots may be legitimate mixed-responsibility files."] if mixed else [],
        ),
        category_result(
            "C",
            "Change Coupling & Dependency Surface",
            15,
            c_score,
            f"{len(broad_imports)} broad import files, {len(high_fan_in)} rough fan-in hotspots.",
            [evidence(f.rel_path, f"imports {f.import_count}, fan-in {f.fan_in}") for f in sorted(sources, key=lambda item: item.import_count + item.fan_in, reverse=True)[:6] if f.import_count or f.fan_in],
            ["Import parsing is heuristic and rough fan-in is based on module name matching."] if sources else [],
        ),
        category_result(
            "D",
            "Test Proximity & Behavioral Safety",
            15,
            d_score,
            f"{len(tests)} test files for {total} source files; source-test proximity {proximity:.0%}.",
            [evidence(f.rel_path, "high-risk file lacks nearby test") for f in sorted([s for s in sources if not s.has_nearby_test], key=lambda item: item.risk_score, reverse=True)[:6]],
            ["Path/name proximity does not prove test quality; inspect assertions around top hotspots."] if sources else [],
        ),
        category_result(
            "E",
            "Duplication & Repetition Risk",
            10,
            e_score,
            f"{duplicate_lines} repeated normalized source lines across {len(duplicate_files)} files.",
            [evidence(f.rel_path, f"{f.duplicate_line_hits} duplicated normalized lines") for f in sorted(duplicate_files, key=lambda item: item.duplicate_line_hits, reverse=True)[:6]],
            ["Line repetition is a weak proxy; validate semantic duplication before extraction."] if duplicate_files else [],
        ),
        category_result(
            "F",
            "Error Handling & Edge Case Visibility",
            10,
            f_score,
            f"{len(side_effect_without_errors)} of {len(side_effect_files)} side-effect files lack visible failure-handling markers.",
            [evidence(f.rel_path, f"side-effect markers {f.side_effect_markers}, error markers {f.error_markers}") for f in side_effect_without_errors[:6]],
            ["Framework-level error boundaries and language idioms require manual review."] if side_effect_files else [],
        ),
        category_result(
            "G",
            "Codebase Hygiene & Volatility",
            10,
            g_score,
            f"{todo_total} debt markers across {len(todo_files)} files; {len(extraction_gaps)} extraction gaps.",
            [evidence(f.rel_path, f"{f.todo_count} debt markers") for f in sorted(todo_files, key=lambda item: item.todo_count, reverse=True)[:6]],
            [f"{gap['path']}: {gap['reason']}" for gap in extraction_gaps[:5]],
        ),
        category_result(
            "H",
            "Maintainability Context",
            5,
            h_score,
            f"{len(context_files)} maintainability context files found.",
            [evidence(path, "context signal") for path in context_files[:6]],
            ["Read context files manually before granting full credit for usefulness."] if context_files else ["No README, contributing, ownership, docs, or ADR context found by the scanner."],
        ),
    ]


def find_context_files(root: Path) -> list[str]:
    names = {
        "architecture.md",
        "codeowners",
        "contributing.md",
        "development.md",
        "readme.md",
    }
    found: list[str] = []
    for current, dirs, files in os.walk(root):
        rel_dir = Path(current).relative_to(root)
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS and not d.startswith(".")]
        if len(rel_dir.parts) > 3:
            dirs[:] = []
        for file in files:
            lowered = file.lower()
            rel = str((Path(current) / file).relative_to(root))
            if lowered in names or rel.lower().startswith("docs/") or "adr" in rel.lower():
                found.append(rel)
    return sorted(found)


def grade_for(score: int) -> str:
    if score >= 85:
        return "Maintainability-Native"
    if score >= 70:
        return "Maintainability-Ready"
    if score >= 55:
        return "Maintainability-Assisted"
    if score >= 35:
        return "Maintainability-Fragile"
    return "Maintainability-Hostile"


def build_risks(hotspots: list[dict[str, object]], categories: list[dict[str, object]], files: list[CodeFile]) -> list[dict[str, str]]:
    risks: list[dict[str, str]] = []
    for hotspot in hotspots[:5]:
        severity = "high" if float(hotspot["risk_score"]) >= 55 else "medium"
        reasons = "; ".join(hotspot["reasons"][:3])
        risks.append(
            {
                "severity": severity,
                "title": f"Maintainability hotspot: {hotspot['path']}",
                "evidence": reasons or "combined code risk signals",
            }
        )
    low_categories = [c for c in categories if int(c["score"]) / int(c["points"]) < 0.55]
    for category in low_categories[:3]:
        risks.append(
            {
                "severity": "high",
                "title": f"Low category score: {category['name']}",
                "evidence": str(category["rationale"]),
            }
        )
    if not risks and files:
        top = max(files, key=lambda item: item.risk_score)
        risks.append(
            {
                "severity": "low",
                "title": "No severe hotspots detected by heuristic scan",
                "evidence": f"Highest rough file risk is {top.rel_path} at {top.risk_score:.0f}/100.",
            }
        )
    return risks[:8]


def action(priority: int, effort: str, impact: str, text: str, evidence_text: str) -> dict[str, object]:
    return {
        "priority": priority,
        "effort": effort,
        "impact": impact,
        "action": text,
        "evidence": evidence_text,
    }


def build_actions(categories: list[dict[str, object]], hotspots: list[dict[str, object]]) -> list[dict[str, object]]:
    actions: list[dict[str, object]] = []
    by_id = {c["id"]: c for c in categories}
    top = hotspots[0] if hotspots else None
    if top:
        path = str(top["path"])
        actions.append(
            action(
                95,
                "M",
                "H",
                f"Add or strengthen behavioral tests around {path} before refactoring.",
                "Top hotspot risk should be made safer before structural edits.",
            )
        )
        if any("mixed responsibility" in reason for reason in top["reasons"]):
            actions.append(
                action(
                    88,
                    "M",
                    "H",
                    f"Split mixed responsibilities in {path} along the visible concern boundary.",
                    "; ".join(top["reasons"][:3]),
                )
            )
        if any("broad import" in reason for reason in top["reasons"]):
            actions.append(
                action(
                    82,
                    "S",
                    "M",
                    f"Reduce dependency surface in {path} by moving composition or adapters outward.",
                    "; ".join(top["reasons"][:3]),
                )
            )
    if int(by_id["A"]["score"]) < 14:
        actions.append(action(84, "M", "H", "Break down the largest complex files into scan-sized units.", str(by_id["A"]["rationale"])))
    if int(by_id["D"]["score"]) < 11:
        actions.append(action(90, "S", "H", "Create nearby tests for the highest-risk untested source files.", str(by_id["D"]["rationale"])))
    if int(by_id["E"]["score"]) < 7:
        actions.append(action(72, "M", "M", "Review repeated code lines and extract only confirmed semantic duplication.", str(by_id["E"]["rationale"])))
    if int(by_id["F"]["score"]) < 7:
        actions.append(action(76, "S", "M", "Make failure paths explicit in side-effect-heavy files.", str(by_id["F"]["rationale"])))
    if int(by_id["G"]["score"]) < 7:
        actions.append(action(70, "S", "M", "Resolve or classify TODO/FIXME/HACK markers in hotspot files.", str(by_id["G"]["rationale"])))
    if int(by_id["H"]["score"]) < 3:
        actions.append(action(55, "S", "M", "Add concise maintenance context: README, contributing notes, or CODEOWNERS.", str(by_id["H"]["rationale"])))
    deduped: dict[str, dict[str, object]] = {}
    for item in actions:
        deduped.setdefault(str(item["action"]), item)
    return sorted(deduped.values(), key=lambda item: int(item["priority"]), reverse=True)[:8]


def build_hotspots(files: list[CodeFile]) -> list[dict[str, object]]:
    hotspots = []
    for file in sorted(files, key=lambda item: item.risk_score, reverse=True):
        if file.is_test or file.risk_score < 20:
            continue
        hotspots.append(
            {
                "path": file.rel_path,
                "risk_score": round(file.risk_score, 1),
                "reasons": file.risk_reasons[:8],
                "metrics": {
                    "loc": file.loc,
                    "imports": file.import_count,
                    "fan_in": file.fan_in,
                    "branch_density": round(file.branch_density, 3),
                    "nesting": file.max_nesting,
                    "long_blocks": file.long_blocks,
                    "debt_markers": file.todo_count,
                    "duplicate_lines": file.duplicate_line_hits,
                    "nearby_test": file.has_nearby_test,
                },
            }
        )
    return hotspots[:20]


def scan(root: Path) -> dict[str, object]:
    root = root.resolve()
    paths, extraction_gaps, excluded_files = iter_source_files(root)
    files: list[CodeFile] = []
    for path in paths:
        text = safe_read(path, root, extraction_gaps)
        if text is None:
            continue
        files.append(analyze_file(path, root, text))
    mark_test_proximity(files)
    mark_fan_in(files)
    duplicate_lines = mark_duplication(files)
    mark_risk_scores(files)

    categories = build_categories(files, duplicate_lines, extraction_gaps, root)
    score = round(sum(int(category["score"]) for category in categories))
    hotspots = build_hotspots(files)
    risks = build_risks(hotspots, categories, files)
    actions = build_actions(categories, hotspots)
    source_files = [f for f in files if not f.is_test]
    test_files = [f for f in files if f.is_test]
    total_loc = sum(f.loc for f in source_files)
    data = {
        "schema_version": SCHEMA_VERSION,
        "target": str(root),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "score": score,
        "grade": grade_for(score),
        "mode": MODE,
        "categories": categories,
        "risks": risks,
        "actions": actions,
        "hotspots": hotspots,
        "extraction_gaps": extraction_gaps,
        "metrics": {
            "code_files_scanned": len(files),
            "source_files": len(source_files),
            "test_files": len(test_files),
            "source_loc": total_loc,
            "avg_source_loc": round(total_loc / max(1, len(source_files)), 1),
            "excluded_files": excluded_files,
            "duplicate_normalized_lines": duplicate_lines,
            "debt_markers": sum(f.todo_count for f in source_files),
            "test_to_source_ratio": round(len(test_files) / max(1, len(source_files)), 3),
            "source_test_proximity": round(sum(1 for f in source_files if f.has_nearby_test) / max(1, len(source_files)), 3),
        },
        "metadata": {
            "scanner": "code-cartography/scripts/score.py",
            "limitations": [
                "Complexity, fan-in, and failure handling are heuristic signals, not language-accurate proofs.",
                "Manual review should confirm whether hotspots are intentional, generated, or covered by non-local tests.",
            ],
        },
    }
    return data


def print_markdown(data: dict[str, object]) -> None:
    print(f"**Score**\n{data['score']}/100 - {data['grade']}")
    print(f"Mode: {data['mode']}\n")
    print("**Key Findings**")
    risks = data.get("risks", [])
    if risks:
        for index, risk in enumerate(risks[:2], 1):
            print(f"{index}. {risk['title']} - {risk['evidence']}")
    else:
        print("1. No material risks detected by heuristic scan.")
    print("\n**Top ROI Actions**")
    for index, item in enumerate(data.get("actions", [])[:3], 1):
        print(f"{index}. [{item['effort']}, priority {item['priority']}] {item['action']} - {item['evidence']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan a repository for code maintainability risk.")
    parser.add_argument("repo", help="Repository path to scan")
    parser.add_argument("--json", required=True, help="Path to write code-score.json")
    parser.add_argument("--markdown", action="store_true", help="Print a short Markdown report")
    args = parser.parse_args(argv)

    repo = Path(args.repo)
    if not repo.exists() or not repo.is_dir():
        parser.error(f"repo path does not exist or is not a directory: {repo}")
    data = scan(repo)
    out = Path(args.json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    if args.markdown:
        print_markdown(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
