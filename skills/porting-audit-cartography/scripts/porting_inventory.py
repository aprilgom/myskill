#!/usr/bin/env python3
"""Collect source/target porting audit evidence as JSON.

This script intentionally uses only the Python standard library. It extracts
inventory-level evidence; humans/agents still judge semantic parity.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]


RUST_PUBLIC_RE = re.compile(
    r"^\s*pub\s+"
    r"(?P<kind>struct|enum|trait|type|const|static|mod|fn)\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)
RUST_IMPL_FN_RE = re.compile(
    r"^\s*pub\s+(?:async\s+)?fn\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)
RUST_RESTRICTED_RE = re.compile(
    r"^\s*pub\((?P<scope>[^)]*)\)\s+"
    r"(?P<kind>struct|enum|trait|type|const|static|mod|fn)\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)
RUST_RESTRICTED_IMPL_FN_RE = re.compile(
    r"^\s*pub\((?P<scope>[^)]*)\)\s+(?:async\s+)?fn\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)
RUST_USE_RE = re.compile(r"^\s*use\s+([^;]+);", re.MULTILINE)
RUST_TEST_RE = re.compile(
    r"#\[(?:tokio::)?test(?:\([^]]*\))?\]\s*(?:async\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)
GO_DECL_RE = re.compile(
    r"^\s*(?:func\s+(?:\([^)]*\)\s*)?(?P<func>[A-Z][A-Za-z0-9_]*)|"
    r"type\s+(?P<type>[A-Z][A-Za-z0-9_]*)|"
    r"(?:const|var)\s+(?P<var>[A-Z][A-Za-z0-9_]*))\b",
    re.MULTILINE,
)
GO_TEST_RE = re.compile(r"^\s*func\s+(Test[A-Za-z0-9_]+)\s*\(", re.MULTILINE)
GO_PORTING_TEST_RE = re.compile(
    r"(?m)^\s*//\s*porting:\s*rust-test=([A-Za-z_][A-Za-z0-9_]*)"
)
GO_SUBTEST_RE = re.compile(r"\bt\.Run\(\s*\"([A-Za-z_][A-Za-z0-9_]*)\"")
CAMEL_TOKEN_RE = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|[0-9]+")
DEFAULT_STANDARD_REPLACEMENTS = {
    "anyhow": "go error wrapping",
    "clap": "target CLI parser or flag package",
    "dunce": "path/filepath plus target-owned Windows extended path cleanup helper",
    "pretty_assertions": "Go testing diagnostics",
    "serde": "encoding/json or typed Go structs",
    "serde_json": "encoding/json",
    "tempfile": "testing.T.TempDir or os.MkdirTemp",
    "thiserror": "Go error types",
}
TOKEN_SYNONYMS = {
    "allows": "allow",
    "allowed": "allow",
    "allowlisted": "allowlist",
    "allowlist": "allowlist",
    "blocks": "block",
    "blocked": "block",
    "blocking": "block",
    "denied": "deny",
    "denies": "deny",
    "disallowed": "deny",
    "disallows": "deny",
    "rejects": "reject",
    "rejected": "reject",
    "requires": "require",
    "required": "require",
    "fails": "error",
    "failure": "error",
    "invalid": "invalid",
    "malformed": "invalid",
    "serializes": "serialize",
    "serialized": "serialize",
    "marshal": "serialize",
    "marshals": "serialize",
    "json": "serialize",
    "timeouts": "timeout",
    "timed": "timeout",
    "times": "timeout",
    "out": "timeout",
    "shutdown": "shutdown",
    "shuts": "shutdown",
    "stops": "shutdown",
    "started": "start",
    "starts": "start",
    "running": "run",
    "runs": "run",
    "mismatched": "mismatch",
    "mismatches": "mismatch",
    "strip": "strip",
    "strips": "strip",
    "stripped": "strip",
    "supports": "support",
    "supported": "support",
    "wildcards": "wildcard",
    "globset": "matcher",
}
STOP_TOKENS = {
    "test",
    "should",
    "when",
    "with",
    "without",
    "and",
    "or",
    "is",
    "are",
    "the",
    "a",
    "an",
    "for",
    "to",
    "from",
    "on",
    "in",
    "by",
    "be",
    "as",
    "go",
    "rust",
    "runtime",
    "http",
    "proxy",
    "inner",
    "url",
    "contains",
    "credentials",
    "telemetry",
}
EDGE_PATTERNS = {
    "error": ("error", "err", "fail", "failure", "unwrap_err", "is_err"),
    "reject": ("reject", "block", "deny", "denied", "forbidden", "not_allowed"),
    "invalid": ("invalid", "missing", "malformed", "mismatch"),
    "serialization": ("json", "marshal", "serialize", "payload", "omitempty", "serde_json"),
    "http_response": ("statuscode", "status code", "http.status", ".status", "header", "x-proxy-error", "body"),
    "timeout_dns": ("timeout", "deadline", "lookupipaddr", "lookup_host", "dns"),
}
LIFECYCLE_PATTERNS = {
    "run_shutdown": ("run", "shutdown", "wait", "close", "serve", "listener"),
    "cancellation": ("context.withcancel", "withcancel", "cancel()", ".cancel", "done", "closed"),
    "concurrency": ("go func", "goroutine", "mutex", "rwmutex", "chan ", "channel"),
    "resource_cleanup": ("defer", "close", "remove", "tempdir", "sync", "fsync"),
    "platform": ("runtime.goos", "darwin", "macos", "windows", "unix", "symlink", "chmod", "0600", "socket"),
}


def rel_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    result: list[str] = []
    for path in root.rglob("*"):
        if path.is_file():
            parts = set(path.parts)
            if ".git" in parts or "target" in parts or "vendor" in parts:
                continue
            result.append(path.relative_to(root).as_posix())
    return sorted(result)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def load_toml(path: Path) -> dict[str, Any]:
    if tomllib is None or not path.exists():
        return {}
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def cargo_dependencies(source: Path) -> dict[str, list[str]]:
    data = load_toml(source / "Cargo.toml")
    sections = {
        "dependencies": data.get("dependencies", {}),
        "dev-dependencies": data.get("dev-dependencies", {}),
        "build-dependencies": data.get("build-dependencies", {}),
    }
    return {
        name: sorted(values.keys()) if isinstance(values, dict) else []
        for name, values in sections.items()
    }


def rust_items(source: Path) -> dict[str, Any]:
    public_items: list[dict[str, str]] = []
    restricted_items: list[dict[str, str]] = []
    tests: list[dict[str, str]] = []
    uses: set[str] = set()
    rust_files = list((source / "src").rglob("*.rs")) if (source / "src").exists() else []
    rust_files.extend((source / "tests").rglob("*.rs") if (source / "tests").exists() else [])
    for file in sorted(rust_files):
        text = read_text(file)
        rel = file.relative_to(source).as_posix()
        for match in RUST_PUBLIC_RE.finditer(text):
            public_items.append(
                {"file": rel, "kind": match.group("kind"), "name": match.group("name")}
            )
        for match in RUST_IMPL_FN_RE.finditer(text):
            public_items.append({"file": rel, "kind": "fn", "name": match.group("name")})
        for match in RUST_RESTRICTED_RE.finditer(text):
            restricted_items.append(
                {
                    "file": rel,
                    "scope": match.group("scope"),
                    "kind": match.group("kind"),
                    "name": match.group("name"),
                }
            )
        for match in RUST_RESTRICTED_IMPL_FN_RE.finditer(text):
            restricted_items.append(
                {"file": rel, "scope": match.group("scope"), "kind": "fn", "name": match.group("name")}
            )
        for match in RUST_TEST_RE.finditer(text):
            name = match.group(1)
            body = function_body_after(text, match.end())
            tests.append(test_record(rel, name, body))
        for match in RUST_USE_RE.finditer(text):
            uses.add(match.group(1).strip())
    return {
        "public_items": unique_dicts(public_items),
        "restricted_items": unique_dicts(restricted_items),
        "tests": unique_dicts(tests),
        "uses": sorted(uses),
        "dependencies": cargo_dependencies(source),
    }


def go_package_name(path: Path) -> str | None:
    for file in sorted(path.glob("*.go")):
        text = read_text(file)
        match = re.search(r"^\s*package\s+([A-Za-z_][A-Za-z0-9_]*)", text, re.MULTILINE)
        if match:
            return match.group(1)
    return None


def parse_go_imports(text: str) -> list[str]:
    imports: list[str] = []
    for block in re.finditer(r"import\s*\((?P<body>.*?)\)", text, re.DOTALL):
        for quoted in re.finditer(r'"([^"]+)"', block.group("body")):
            imports.append(quoted.group(1))
    for one in re.finditer(r'^\s*import\s+(?:[._A-Za-z0-9]+\s+)?"([^"]+)"', text, re.MULTILINE):
        imports.append(one.group(1))
    return imports


def go_items(target: Path) -> dict[str, Any]:
    public_items: list[dict[str, str]] = []
    tests: list[dict[str, str]] = []
    imports: set[str] = set()
    helper_candidates: list[dict[str, str]] = []
    explicit_test_mappings: list[dict[str, str]] = []
    for file in sorted(target.glob("*.go")):
        text = read_text(file)
        rel = file.relative_to(target).as_posix()
        imports.update(parse_go_imports(text))
        if not file.name.endswith("_test.go"):
            for match in GO_DECL_RE.finditer(text):
                kind = "func" if match.group("func") else "type" if match.group("type") else "var"
                name = match.group("func") or match.group("type") or match.group("var")
                public_items.append({"file": rel, "kind": kind, "name": name})
        for match in GO_TEST_RE.finditer(text):
            name = match.group(1)
            body = function_body_after(text, match.end())
            tests.append(test_record(rel, name, body))
        explicit_test_mappings.extend(go_explicit_test_mappings(text, rel))
        for match in re.finditer(r"^\s*func\s+([a-z][A-Za-z0-9_]*)\s*\(", text, re.MULTILINE):
            helper_candidates.append({"file": rel, "name": match.group(1)})
    return {
        "package": go_package_name(target),
        "public_items": unique_dicts(public_items),
        "tests": unique_dicts(tests),
        "explicit_test_mappings": unique_dicts(explicit_test_mappings),
        "imports": sorted(imports),
        "local_helper_candidates": unique_dicts(helper_candidates),
        "go_list_imports": go_list_imports(target),
    }


def function_body_after(text: str, start: int) -> str:
    open_index = text.find("{", start)
    if open_index < 0:
        return ""
    depth = 0
    in_string = ""
    escaped = False
    for index in range(open_index, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == in_string:
                in_string = ""
            continue
        if char in {'"', "'", "`"}:
            in_string = char
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[open_index + 1:index]
    return text[open_index + 1:]


def test_record(rel: str, name: str, body: str) -> dict[str, Any]:
    evidence = test_evidence(name, body)
    return {
        "file": rel,
        "name": name,
        "evidence_tags": sorted(evidence["tags"]),
        "edge_tags": sorted(evidence["edge_tags"]),
        "lifecycle_tags": sorted(evidence["lifecycle_tags"]),
    }


def test_evidence(name: str, body: str) -> dict[str, set[str]]:
    haystack = (name + "\n" + body).lower()
    edge_tags = {
        tag
        for tag, patterns in EDGE_PATTERNS.items()
        if any(pattern in haystack for pattern in patterns)
    }
    lifecycle_tags = {
        tag
        for tag, patterns in LIFECYCLE_PATTERNS.items()
        if any(pattern in haystack for pattern in patterns)
    }
    tags = set(edge_tags) | set(lifecycle_tags)
    if edge_tags:
        tags.add("edge")
    if lifecycle_tags:
        tags.add("lifecycle")
    return {"tags": tags, "edge_tags": edge_tags, "lifecycle_tags": lifecycle_tags}


def go_explicit_test_mappings(text: str, rel: str) -> list[dict[str, str]]:
    mappings: list[dict[str, str]] = []
    pending: list[str] = []
    for line in text.splitlines():
        marker = GO_PORTING_TEST_RE.match(line)
        if marker:
            pending.append(marker.group(1))
            continue
        test = re.match(r"^\s*func\s+(Test[A-Za-z0-9_]+)\s*\(", line)
        if test:
            for rust_test in pending:
                mappings.append({"file": rel, "source_test": rust_test, "target_test": test.group(1)})
            pending = []
            continue
        if line.strip() and not line.lstrip().startswith("//"):
            pending = []
    for test_match in GO_TEST_RE.finditer(text):
        test_name = test_match.group(1)
        body = function_body_after(text, test_match.end())
        for subtest in GO_SUBTEST_RE.finditer(body):
            mappings.append(
                {
                    "file": rel,
                    "source_test": subtest.group(1),
                    "target_test": test_name,
                    "method": "subtest-name",
                }
            )
    return mappings


def rust_test_go_name(name: str) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", name) if part]
    return "Test" + "".join(part[:1].upper() + part[1:] for part in parts)


def test_tokens(name: str) -> set[str]:
    raw_parts: list[str] = []
    for part in re.split(r"[^A-Za-z0-9]+", name):
        if not part:
            continue
        raw_parts.extend(token.lower() for token in CAMEL_TOKEN_RE.findall(part))
    tokens: set[str] = set()
    skip_next_out = False
    for token in raw_parts:
        if token in STOP_TOKENS:
            continue
        if token == "non":
            tokens.add("nonpublic")
            continue
        if token == "public":
            if "nonpublic" in tokens:
                continue
            tokens.add("public")
            continue
        if token == "time":
            skip_next_out = True
            tokens.add("timeout")
            continue
        if skip_next_out and token == "out":
            skip_next_out = False
            continue
        normalized = TOKEN_SYNONYMS.get(token, token)
        if normalized and normalized not in STOP_TOKENS:
            tokens.add(normalized)
    return tokens


def token_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    overlap = left & right
    precision = len(overlap) / len(right)
    recall = len(overlap) / len(left)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def test_mapping_inventory(
    source_tests: list[dict[str, str]],
    target_tests: list[dict[str, str]],
    explicit: list[dict[str, str]],
    excluded: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    excluded = excluded or []
    excluded_names = {item.get("name", "") for item in excluded if item.get("name")}
    source_tests = [item for item in source_tests if item["name"] not in excluded_names]
    source_by_name = {item["name"]: item for item in source_tests}
    target_by_name = {item["name"]: item for item in target_tests}
    mappings: list[dict[str, Any]] = []
    used_sources: set[str] = set()

    for row in explicit:
        source_name = row["source_test"]
        if source_name in excluded_names:
            continue
        target_name = row["target_test"]
        if source_name not in source_by_name or target_name not in target_by_name:
            status = "invalid"
            confidence = 0.0
        else:
            status = "matched"
            confidence = 1.0
            used_sources.add(source_name)
        mappings.append({
            "source_test": source_name,
            "target_test": target_name,
            "method": row.get("method", "explicit"),
            "confidence": confidence,
            "status": status,
            "source_edge_tags": source_by_name.get(source_name, {}).get("edge_tags", []),
            "target_edge_tags": target_by_name.get(target_name, {}).get("edge_tags", []),
            "source_lifecycle_tags": source_by_name.get(source_name, {}).get("lifecycle_tags", []),
            "target_lifecycle_tags": target_by_name.get(target_name, {}).get("lifecycle_tags", []),
        })

    for source in source_tests:
        source_name = source["name"]
        if source_name in used_sources:
            continue
        target_name = rust_test_go_name(source_name)
        if target_name not in target_by_name:
            continue
        used_sources.add(source_name)
        mappings.append({
            "source_test": source_name,
            "target_test": target_name,
            "method": "rust-name-pascal",
            "confidence": 1.0,
            "status": "matched",
            "source_edge_tags": source.get("edge_tags", []),
            "target_edge_tags": target_by_name.get(target_name, {}).get("edge_tags", []),
            "source_lifecycle_tags": source.get("lifecycle_tags", []),
            "target_lifecycle_tags": target_by_name.get(target_name, {}).get("lifecycle_tags", []),
        })

    target_tokens = {
        item["name"]: test_tokens(item["name"])
        for item in target_tests
    }
    for source in source_tests:
        source_name = source["name"]
        if source_name in used_sources:
            continue
        source_tokens = test_tokens(source_name)
        best_name = ""
        best_score = 0.0
        for target_name, tokens in target_tokens.items():
            score = token_similarity(source_tokens, tokens)
            if score > best_score:
                best_name = target_name
                best_score = score
        if best_name and best_score >= 0.55:
            mappings.append({
                "source_test": source_name,
                "target_test": best_name,
                "method": "name-similarity",
                "confidence": round(best_score, 3),
                "status": "matched" if best_score >= 0.72 else "weak",
                "source_edge_tags": source.get("edge_tags", []),
                "target_edge_tags": target_by_name.get(best_name, {}).get("edge_tags", []),
                "source_lifecycle_tags": source.get("lifecycle_tags", []),
                "target_lifecycle_tags": target_by_name.get(best_name, {}).get("lifecycle_tags", []),
            })
            used_sources.add(source_name)

    unmatched = [
        {"file": item["file"], "name": item["name"]}
        for item in source_tests
        if item["name"] not in used_sources
    ]
    return {
        "mappings": mappings,
        "matched_source_count": len(used_sources),
        "source_count": len(source_tests),
        "target_count": len(target_tests),
        "unmatched_source_tests": unmatched,
        "excluded_source_tests": excluded,
    }


def go_list_imports(target: Path) -> list[str]:
    try:
        proc = subprocess.run(
            ["go", "list", "-f", "{{join .Imports \"\\n\"}}"],
            cwd=target,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return []
    if proc.returncode != 0:
        return []
    return sorted(line for line in proc.stdout.splitlines() if line.strip())


def unique_dicts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def dependency_grade(repo: Path, package: str | None) -> dict[str, Any]:
    doc = repo / "docs" / "dependency-grade.md"
    if not package or not doc.exists():
        return {}
    text = read_text(doc)
    current_grade: str | None = None
    for line in text.splitlines():
        heading = re.match(r"^##\s+(.+)$", line)
        if heading:
            current_grade = heading.group(1)
            continue
        if current_grade and f"`{package}`" in line:
            return {"grade": current_grade, "line": line.strip()}
    return {}


def dependency_grades(repo: Path) -> dict[str, int]:
    doc = repo / "docs" / "dependency-grade.md"
    if not doc.exists():
        return {}
    grades: dict[str, int] = {}
    current_rank: int | None = None
    for line in read_text(doc).splitlines():
        heading = re.match(r"^##\s+(.+)$", line)
        if heading:
            rank_match = re.search(r"(\d+)", heading.group(1))
            current_rank = int(rank_match.group(1)) if rank_match else None
            continue
        if current_rank is None:
            continue
        if not line.startswith("- "):
            continue
        match = re.search(r"`([^`]+)`", line)
        if match:
            grades[match.group(1)] = current_rank
    return grades


def module_path(repo: Path) -> str:
    mod = repo / "go.mod"
    if not mod.exists():
        return ""
    for line in read_text(mod).splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[0] == "module":
            return fields[1]
    return ""


def load_dependency_registry(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError:
        return {}


def default_andex_registry(repo: Path) -> dict[str, Any]:
    module = module_path(repo) or "andex-go2"
    return {
        "rust_to_go": {
            "andex-utils-absolute-path": f"{module}/utils/absolute-path",
            "andex-utils-cache": f"{module}/utils/cache",
            "andex-utils-elapsed": f"{module}/utils/elapsed",
            "andex-utils-home-dir": f"{module}/utils/home-dir",
            "andex-utils-image": f"{module}/utils/image",
            "andex-utils-path-utils": f"{module}/utils/path-utils",
            "andex-utils-pty": f"{module}/utils/pty",
            "andex-utils-readiness": f"{module}/utils/readiness",
            "andex-utils-stream-parser": f"{module}/utils/stream-parser",
            "andex-utils-string": f"{module}/utils/string",
            "andex-utils-template": f"{module}/utils/template",
            "andex-protocol": f"{module}/protocol",
            "andex-execpolicy": f"{module}/execpolicy",
            "andex-file-watcher": f"{module}/file-watcher",
            "andex-stdio-to-uds": f"{module}/stdio-to-uds",
            "andex-uds": f"{module}/uds",
        },
        "standard_replacements": DEFAULT_STANDARD_REPLACEMENTS,
        "external_replacements": {},
        "allowed_local_reimplementations": {},
    }


def merge_registry(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = dict(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    return merged


def selected_api_mappings(registry: dict[str, Any], package_rel: str | None) -> dict[str, Any]:
    by_package = registry.get("api_mappings_by_package", {})
    if isinstance(by_package, dict) and package_rel:
        scoped = by_package.get(package_rel, {})
        if isinstance(scoped, dict) and scoped:
            return scoped
    global_mappings = registry.get("api_mappings", {})
    return global_mappings if isinstance(global_mappings, dict) else {}


def selected_excluded_tests(registry: dict[str, Any], package_rel: str | None) -> list[dict[str, str]]:
    by_package = registry.get("excluded_tests_by_package", {})
    if not isinstance(by_package, dict) or not package_rel:
        return []
    rows = by_package.get(package_rel, [])
    if not isinstance(rows, list):
        return []
    selected = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("name"):
            continue
        selected.append({
            "file": str(row.get("file", "")),
            "name": str(row["name"]),
            "reason": str(row.get("reason", "")),
        })
    return selected


def source_dependency_map(source_deps: dict[str, list[str]], target_imports: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for section, deps in source_deps.items():
        for dep in deps:
            matched = ""
            dep_candidates = dependency_name_candidates(dep)
            for imp in target_imports:
                import_candidates = import_name_candidates(imp)
                if dep_candidates & import_candidates:
                    matched = imp
                    break
            rows.append(
                {
                    "source_section": section,
                    "source_dependency": dep,
                    "target_import_guess": matched,
                    "handling": "candidate import" if matched else "unmatched",
                }
            )
    return rows


def deterministic_dependency_audit(
    source_deps: dict[str, list[str]],
    target_imports: list[str],
    package_rel: str | None,
    repo: Path,
    registry: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rust_to_go = registry.get("rust_to_go", {}) if isinstance(registry.get("rust_to_go"), dict) else {}
    standard = registry.get("standard_replacements", {}) if isinstance(registry.get("standard_replacements"), dict) else {}
    external = registry.get("external_replacements", {}) if isinstance(registry.get("external_replacements"), dict) else {}
    allowed_local = (
        registry.get("allowed_local_reimplementations", {})
        if isinstance(registry.get("allowed_local_reimplementations"), dict)
        else {}
    )
    grade_map = dependency_grades(repo)
    package_grade = grade_map.get(package_rel or "")

    for section, deps in source_deps.items():
        for dep in deps:
            expected = rust_to_go.get(dep, "")
            handling = "unknown mapping"
            evidence: dict[str, Any] = {"source_section": section}
            if expected:
                if expected in target_imports:
                    handling = "correct import"
                    evidence["target_import"] = expected
                elif dep in allowed_local.get(package_rel or "", []):
                    handling = "allowed local reimplementation"
                    evidence["allowlist"] = True
                else:
                    handling = "missing dependency"
                    evidence["expected_target_import"] = expected
                expected_rel = import_to_repo_rel(expected, module_path(repo))
                expected_grade = grade_map.get(expected_rel)
                if (
                    handling == "correct import"
                    and package_grade is not None
                    and expected_grade is not None
                    and expected_grade > package_grade
                ):
                    handling = "upward dependency violation"
                    evidence["package_grade"] = package_grade
                    evidence["dependency_grade"] = expected_grade
            elif dep in standard:
                handling = "standard-library replacement allowed"
                evidence["replacement"] = standard[dep]
            elif dep in external:
                handling = "external replacement allowed"
                evidence["replacement"] = external[dep]
            rows.append(
                {
                    "source_dependency": dep,
                    "expected_target_import": expected,
                    "handling": handling,
                    "evidence": evidence,
                }
            )

    for imp in target_imports:
        rel = import_to_repo_rel(imp, module_path(repo))
        imp_grade = grade_map.get(rel)
        if package_grade is None or imp_grade is None:
            continue
        if imp_grade > package_grade:
            rows.append(
                {
                    "source_dependency": "",
                    "expected_target_import": imp,
                    "handling": "upward dependency violation",
                    "evidence": {
                        "package": package_rel,
                        "package_grade": package_grade,
                        "target_import": imp,
                        "dependency_grade": imp_grade,
                    },
                }
            )
    return rows


def import_to_repo_rel(imp: str, module: str) -> str:
    if module and imp.startswith(module + "/"):
        return imp[len(module) + 1 :]
    return imp


def compact_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def dependency_name_candidates(dep: str) -> set[str]:
    candidates = {compact_name(dep)}
    if dep.startswith("andex-"):
        stripped = dep.removeprefix("andex-")
        candidates.add(compact_name(stripped))
        if stripped.startswith("utils-"):
            candidates.add(compact_name("utils/" + stripped.removeprefix("utils-")))
    return candidates


def import_name_candidates(imp: str) -> set[str]:
    parts = imp.split("/")
    candidates = {compact_name(imp), compact_name(parts[-1])}
    if len(parts) >= 2:
        candidates.add(compact_name("/".join(parts[-2:])))
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Source package root, e.g. Rust crate")
    parser.add_argument("--target", required=True, help="Target package root, e.g. Go package")
    parser.add_argument("--repo", default=".", help="Target repository root")
    parser.add_argument(
        "--dependency-registry",
        help="JSON file with rust_to_go, standard_replacements, external_replacements, and allowed_local_reimplementations",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    target = Path(args.target).expanduser().resolve()
    repo = Path(args.repo).expanduser().resolve()
    registry_override = load_dependency_registry(
        Path(args.dependency_registry).expanduser().resolve()
        if args.dependency_registry
        else None
    )
    registry = merge_registry(default_andex_registry(repo), registry_override)

    source_rust = rust_items(source)
    target_go = go_items(target)
    package_rel = os.path.relpath(target, repo) if target.exists() else None
    excluded_tests = selected_excluded_tests(registry, package_rel)
    test_mapping = test_mapping_inventory(
        source_rust.get("tests", []),
        target_go.get("tests", []),
        target_go.get("explicit_test_mappings", []),
        excluded_tests,
    )

    payload = {
        "source": {
            "root": str(source),
            "files": rel_files(source),
            "rust": source_rust,
        },
        "target": {
            "root": str(target),
            "files": rel_files(target),
            "go": target_go,
            "dependency_grade": dependency_grade(repo, package_rel),
        },
        "dependency_map": source_dependency_map(
            source_rust.get("dependencies", {}),
            target_go.get("imports", []),
        ),
        "deterministic_dependency_audit": deterministic_dependency_audit(
            source_rust.get("dependencies", {}),
            target_go.get("imports", []),
            package_rel,
            repo,
            registry,
        ),
        "test_mapping": test_mapping,
        "registry": {
            "api_mappings": selected_api_mappings(registry, package_rel),
            "excluded_tests": excluded_tests,
        },
        "notes": [
            "Regex-based extraction is evidence inventory, not semantic proof.",
            "deterministic_dependency_audit is registry-driven; unknown mapping means the registry must be extended before making a dependency-boundary claim.",
            "test_mapping prefers explicit // porting: rust-test=<name> comments and falls back to normalized test-name similarity.",
            "Review local_helper_candidates for possible copied dependency responsibilities after deterministic dependency findings.",
        ],
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
