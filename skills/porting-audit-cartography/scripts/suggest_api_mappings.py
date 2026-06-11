#!/usr/bin/env python3
"""Suggest dependency-registry api_mappings from source/target inventory.

The output is a registry JSON object. Existing registry keys are preserved, and
existing api_mappings are not replaced unless --replace-existing is supplied.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from porting_inventory import (
    go_items,
    load_dependency_registry,
    merge_registry,
    module_path,
    rust_items,
    token_similarity,
)


CAMEL_TOKEN_RE = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|[0-9]+")


def rust_export_name(name: str) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", name) if part]
    if not parts:
        return name
    return "".join(part[:1].upper() + part[1:] for part in parts)


def api_tokens(name: str) -> set[str]:
    raw_parts: list[str] = []
    for part in re.split(r"[^A-Za-z0-9]+", name):
        if not part:
            continue
        raw_parts.extend(token.lower() for token in CAMEL_TOKEN_RE.findall(part))
    return {token for token in raw_parts if token}


def best_candidate(source_name: str, go_names: list[str]) -> dict[str, Any] | None:
    pascal = rust_export_name(source_name)
    upper = source_name.upper()
    if source_name in go_names:
        return {"target": source_name, "status": "mapped", "confidence": 1.0, "method": "exact"}
    if pascal in go_names:
        return {"target": pascal, "status": "mapped", "confidence": 1.0, "method": "snake-to-pascal"}
    if upper in go_names:
        return {"target": upper, "status": "mapped", "confidence": 1.0, "method": "upper-constant"}

    source_tokens = api_tokens(source_name)
    best_name = ""
    best_score = 0.0
    for go_name in go_names:
        score = token_similarity(source_tokens, api_tokens(go_name))
        if score > best_score:
            best_name = go_name
            best_score = score
    if not best_name or best_score < 0.55:
        return None
    return {
        "target": best_name,
        "status": "mapped" if best_score >= 0.88 else "partial",
        "confidence": round(best_score, 3),
        "method": "token-similarity",
    }


def suggest_mappings(source: Path, target: Path, include_unmatched: bool) -> dict[str, Any]:
    rust_public = rust_items(source).get("public_items", [])
    go_public = go_items(target).get("public_items", [])
    go_names = sorted({item.get("name", "") for item in go_public if item.get("name")})

    suggestions: dict[str, Any] = {}
    for item in rust_public:
        source_name = item.get("name", "")
        if not source_name or source_name in suggestions:
            continue
        candidate = best_candidate(source_name, go_names)
        if candidate is None:
            if not include_unmatched:
                continue
            candidate = {"target": "", "status": "partial", "confidence": 0.0, "method": "unmatched"}
        suggestions[source_name] = {
            "target": candidate["target"],
            "status": candidate["status"],
            "source": f"{item.get('file', '')}:{item.get('kind', '')}",
            "confidence": candidate["confidence"],
            "method": candidate["method"],
        }
    return suggestions


def write_json(path: Path | None, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path is None:
        sys.stdout.write(text)
        return
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Source package root, e.g. Rust crate")
    parser.add_argument("--target", required=True, help="Target package root, e.g. Go package")
    parser.add_argument("--repo", default=".", help="Target repository root")
    parser.add_argument("--dependency-registry", help="Existing registry JSON to read")
    parser.add_argument("--out", help="Write merged registry JSON to this path")
    parser.add_argument("--in-place", action="store_true", help="Rewrite --dependency-registry in place")
    parser.add_argument("--replace-existing", action="store_true", help="Replace existing api_mappings entries")
    parser.add_argument("--include-unmatched", action="store_true", help="Emit partial review rows for unmapped source APIs")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    target = Path(args.target).expanduser().resolve()
    repo = Path(args.repo).expanduser().resolve()
    registry_path = Path(args.dependency_registry).expanduser().resolve() if args.dependency_registry else None
    out_path = Path(args.out).expanduser().resolve() if args.out else None

    if args.in_place and registry_path is None:
        parser.error("--in-place requires --dependency-registry")
    if args.in_place and out_path is not None:
        parser.error("--in-place and --out are mutually exclusive")

    registry = load_dependency_registry(registry_path)
    if not registry:
        registry = {"rust_to_go": {}, "standard_replacements": {}, "external_replacements": {}, "allowed_local_reimplementations": {}}
    if "module" not in registry:
        module = module_path(repo)
        if module:
            registry = merge_registry(registry, {"module": module})

    api_mappings = registry.get("api_mappings", {})
    if not isinstance(api_mappings, dict):
        api_mappings = {}
    merged_mappings = dict(api_mappings)
    suggestions = suggest_mappings(source, target, args.include_unmatched)
    for name, row in suggestions.items():
        if args.replace_existing or name not in merged_mappings:
            merged_mappings[name] = row

    registry["api_mappings"] = dict(sorted(merged_mappings.items()))
    destination = registry_path if args.in_place else out_path
    write_json(destination, registry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
