#!/usr/bin/env python3
"""Generate deterministic dependency grade maps.

Grades are computed on strongly connected components. A component with no
in-scope dependencies is grade 0. Otherwise its grade is one plus the maximum
grade of the components it depends on.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


CRATE_REF_RE = re.compile(r"\bcrate::([A-Za-z_][A-Za-z0-9_]*)")
MOD_DECL_RE = re.compile(r"^\s*(?:pub\s+)?mod\s+([A-Za-z_][A-Za-z0-9_]*)\s*;", re.MULTILINE)


def run_cargo_metadata(root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        ["cargo", "metadata", "--no-deps", "--format-version", "1"],
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise SystemExit(f"cargo metadata failed:\n{proc.stderr}")
    return json.loads(proc.stdout)


def workspace_graph(root: Path, include_dev: bool) -> tuple[dict[str, set[str]], dict[str, dict[str, str]]]:
    metadata = run_cargo_metadata(root)
    packages = metadata.get("packages", [])
    workspace_ids = set(metadata.get("workspace_members", []))
    by_id = {pkg["id"]: pkg for pkg in packages if pkg.get("id") in workspace_ids}
    by_name = {pkg["name"]: pkg for pkg in by_id.values()}
    graph: dict[str, set[str]] = {pkg["name"]: set() for pkg in by_id.values()}
    labels: dict[str, dict[str, str]] = {}
    for pkg in by_id.values():
        manifest = Path(pkg["manifest_path"])
        rel_dir = os.path.relpath(manifest.parent, root)
        labels[pkg["name"]] = {"name": pkg["name"], "path": "." if rel_dir == "." else rel_dir}
        for dep in pkg.get("dependencies", []):
            if dep.get("name") not in by_name:
                continue
            if dep.get("kind") == "dev" and not include_dev:
                continue
            graph[pkg["name"]].add(dep["name"])
    return graph, labels


def module_name_for_file(src: Path, file: Path) -> str:
    rel = file.relative_to(src)
    if rel.name == "mod.rs":
        return rel.parent.as_posix().replace("/", "::")
    stem = rel.with_suffix("").as_posix()
    return stem.replace("/", "::")


def rust_module_graph(root: Path, include_tests: bool) -> tuple[dict[str, set[str]], dict[str, dict[str, str]]]:
    src = root / "src"
    if not src.exists():
        raise SystemExit(f"Rust source directory not found: {src}")

    files = [p for p in src.rglob("*.rs") if include_tests or not p.name.endswith("_tests.rs")]
    modules = {module_name_for_file(src, p): p for p in files}
    top_level = {name.split("::", 1)[0] for name in modules}
    graph: dict[str, set[str]] = {name: set() for name in modules}
    labels = {
        name: {"name": name, "path": path.relative_to(root).as_posix()}
        for name, path in modules.items()
    }

    for name, path in modules.items():
        text = path.read_text(errors="replace")
        refs = set(CRATE_REF_RE.findall(text))
        if path.name == "lib.rs":
            refs.update(MOD_DECL_RE.findall(text))
        for ref in refs:
            if ref in top_level:
                for candidate in modules:
                    if candidate == ref or candidate.startswith(ref + "::"):
                        graph[name].add(candidate)
        graph[name].discard(name)
    return graph, labels


def strongly_connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    index = 0
    stack: list[str] = []
    indexes: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    on_stack: set[str] = set()
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indexes[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for dep in graph.get(node, set()):
            if dep not in indexes:
                visit(dep)
                lowlinks[node] = min(lowlinks[node], lowlinks[dep])
            elif dep in on_stack:
                lowlinks[node] = min(lowlinks[node], indexes[dep])
        if lowlinks[node] == indexes[node]:
            component: list[str] = []
            while True:
                item = stack.pop()
                on_stack.remove(item)
                component.append(item)
                if item == node:
                    break
            components.append(sorted(component))

    for node in sorted(graph):
        if node not in indexes:
            visit(node)
    return components


def grade_graph(graph: dict[str, set[str]]) -> dict[str, Any]:
    components = strongly_connected_components(graph)
    component_of = {node: i for i, comp in enumerate(components) for node in comp}
    component_deps: dict[int, set[int]] = {i: set() for i in range(len(components))}
    for node, deps in graph.items():
        src = component_of[node]
        for dep in deps:
            dst = component_of.get(dep)
            if dst is not None and dst != src:
                component_deps[src].add(dst)

    visiting: set[int] = set()
    memo: dict[int, int] = {}

    def grade(component: int) -> int:
        if component in memo:
            return memo[component]
        if component in visiting:
            raise RuntimeError("component graph unexpectedly contains a cycle")
        visiting.add(component)
        deps = component_deps[component]
        value = 0 if not deps else 1 + max(grade(dep) for dep in deps)
        visiting.remove(component)
        memo[component] = value
        return value

    grades = {i: grade(i) for i in range(len(components))}
    return {
        "components": components,
        "component_dependencies": {str(k): sorted(v) for k, v in component_deps.items()},
        "component_grades": {str(k): v for k, v in grades.items()},
        "node_grades": {node: grades[component_of[node]] for node in graph},
        "cycles": [comp for comp in components if len(comp) > 1],
    }


def render_markdown(title: str, root: Path, mode: str, graph: dict[str, set[str]], labels: dict[str, dict[str, str]], graded: dict[str, Any]) -> str:
    node_grades = graded["node_grades"]
    max_grade = max(node_grades.values(), default=0)
    by_grade: dict[int, list[str]] = defaultdict(list)
    for node, grade in node_grades.items():
        by_grade[grade].append(node)

    lines = [
        f"# {title}",
        "",
        f"기준: `{root}`에서 `{mode}` 의존성을 정적 추출해 계산했습니다.",
        "",
        "- 0단계: 범위 내부의 다른 항목에 의존하지 않는 항목",
        "- n단계: 자신이 의존하는 내부 항목들의 최대 단계가 n-1인 항목",
        "- 서로 순환 참조하는 항목들은 하나의 컴포넌트로 묶었습니다.",
        "",
        "## Summary",
        "",
        f"- 대상 항목: {len(graph)}",
        f"- 컴포넌트: {len(graded['components'])}",
        f"- 최대 단계: {max_grade}",
    ]
    if graded["cycles"]:
        lines.append("- 순환 컴포넌트:")
        for comp in graded["cycles"]:
            lines.append(f"  - `{ '`, `'.join(comp) }`")
    else:
        lines.append("- 순환 컴포넌트: 없음")

    for grade in range(max_grade + 1):
        lines.extend(["", f"## {grade}단계", ""])
        for node in sorted(by_grade.get(grade, [])):
            label = labels.get(node, {"name": node, "path": node})
            deps = sorted(graph.get(node, set()))
            display = label["path"] if label["path"] != "." else label["name"]
            lines.append(f"- `{display}` (`{label['name']}`)")
            lines.append(f"  - 의존: {', '.join(f'`{d}`' for d in deps) if deps else '없음'}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)

    workspace = sub.add_parser("workspace")
    workspace.add_argument("--root", required=True, type=Path)
    workspace.add_argument("--include-dev", action="store_true")
    workspace.add_argument("--markdown", type=Path)
    workspace.add_argument("--json", type=Path)
    workspace.add_argument("--title", default="Dependency Grade")

    modules = sub.add_parser("rust-modules")
    modules.add_argument("--root", required=True, type=Path)
    modules.add_argument("--include-tests", action="store_true")
    modules.add_argument("--markdown", type=Path)
    modules.add_argument("--json", type=Path)
    modules.add_argument("--title", default="Rust Module Dependency Grade")

    args = parser.parse_args()
    root = args.root.resolve()
    if args.mode == "workspace":
        graph, labels = workspace_graph(root, args.include_dev)
    else:
        graph, labels = rust_module_graph(root, args.include_tests)
    graded = grade_graph(graph)
    payload = {
        "mode": args.mode,
        "root": str(root),
        "graph": {k: sorted(v) for k, v in sorted(graph.items())},
        "labels": labels,
        **graded,
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(args.title, root, args.mode, graph, labels, graded))
    if not args.json and not args.markdown:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
