#!/usr/bin/env python3
"""Architecture Cartography - repository architecture signal scanner.

Usage:
    python score.py /path/to/repo --json architecture-score.json
    python score.py /path/to/repo --markdown

The scorer is intentionally heuristic. It collects repeatable evidence and
produces a baseline that should be manually reviewed with the rubric.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


IGNORE_DIRS = {
    ".git", "node_modules", ".next", "dist", "build", "coverage", ".turbo",
    ".cache", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    "target", "out", ".idea", ".vscode", "vendor",
}
SOURCE_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".kt", ".cs", ".rb", ".php", ".swift"}
TEST_HINTS = ("test", "tests", "spec", "__tests__", "e2e", "integration")
CONTRACT_HINTS = ("openapi", "swagger", "graphql", "schema", "proto", "dto", "contract", "validator", "zod", "pydantic")
RUNTIME_FILES = ("Dockerfile", "docker-compose.yml", "compose.yml", "Procfile", "serverless.yml", "terraform.tf")
ARCH_DOC_NAMES = ("ARCHITECTURE.md", "architecture.md", "ARCHITECTURE.adoc")
GENERIC_DIRS = {"common", "shared", "utils", "helpers", "lib", "libs", "core"}
LAYER_WORDS = {
    "ui": {"ui", "view", "views", "component", "components", "frontend", "client", "page", "pages"},
    "api": {"api", "route", "routes", "controller", "controllers", "handler", "handlers"},
    "domain": {"domain", "model", "models", "entity", "entities", "usecase", "usecases", "service", "services"},
    "data": {"db", "database", "repo", "repository", "repositories", "dao", "orm", "migration", "migrations"},
    "infra": {"infra", "infrastructure", "adapter", "adapters", "provider", "providers", "config"},
}

IMPORT_PATTERNS = [
    re.compile(r"^\s*import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", re.MULTILINE),
    re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]", re.MULTILINE),
    re.compile(r"^\s*from\s+([A-Za-z0-9_\.]+)\s+import\s+", re.MULTILINE),
    re.compile(r"^\s*import\s+([A-Za-z0-9_\.]+)", re.MULTILINE),
    re.compile(r"^\s*use\s+([A-Za-z0-9_:]+)", re.MULTILINE),
    re.compile(r"^\s*import\s+([A-Za-z0-9_./*]+);", re.MULTILINE),
]


@dataclass
class CategoryScore:
    name: str
    score: int
    max: int
    evidence: dict[str, Any] = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)


@dataclass
class Action:
    title: str
    category: str
    effort: str
    effort_hours: float
    impact: str
    impact_score: int
    priority: float


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def walk_files(repo: Path) -> list[Path]:
    out: list[Path] = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        for file_name in files:
            out.append(Path(root) / file_name)
    return out


def rel(repo: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo))
    except ValueError:
        return str(path)


def line_count(path: Path) -> int:
    text = read_text(path)
    if not text:
        return 0
    return len(text.splitlines())


def git_branch(repo: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def grade(total: int) -> tuple[str, str]:
    if total >= 90:
        return "Architecture-Native", "green"
    if total >= 75:
        return "Architecture-Ready", "green"
    if total >= 60:
        return "Architecture-Assisted", "amber"
    if total >= 40:
        return "Architecture-Fragile", "amber"
    return "Architecture-Hostile", "red"


def add_action(actions: list[Action], title: str, category: str, effort: str, hours: float, impact: str, impact_score: int) -> None:
    actions.append(Action(title, category, effort, hours, impact, impact_score, round(impact_score / hours, 2)))


def core_modules(repo: Path, source_files: list[Path]) -> list[dict[str, Any]]:
    candidates: set[Path] = set()
    for src in source_files:
        parts = src.relative_to(repo).parts
        if len(parts) >= 3 and parts[0] in {"apps", "packages", "services", "libs"}:
            candidates.add(repo / parts[0] / parts[1])
        elif len(parts) >= 2:
            candidates.add(repo / parts[0])
    modules: list[dict[str, Any]] = []
    for path in sorted(candidates):
        if not path.is_dir() or path.name in IGNORE_DIRS:
            continue
        count = sum(1 for f in source_files if path in f.parents)
        if count:
            modules.append({"path": rel(repo, path), "source_files": count})
    return modules


def extract_imports(path: Path) -> list[str]:
    text = read_text(path)
    imports: list[str] = []
    for pattern in IMPORT_PATTERNS:
        imports.extend(match.group(1) for match in pattern.finditer(text))
    return imports


def layer_for_path(path: Path) -> str | None:
    parts = {part.lower() for part in path.parts}
    for layer, words in LAYER_WORDS.items():
        if parts & words:
            return layer
    return None


def score(repo: Path) -> dict[str, Any]:
    files = walk_files(repo)
    source_files = [p for p in files if p.suffix in SOURCE_EXTS]
    test_files = [p for p in files if p.suffix in SOURCE_EXTS and any(h in p.name.lower() or h in {part.lower() for part in p.parts} for h in TEST_HINTS)]
    modules = core_modules(repo, source_files)
    actions: list[Action] = []

    large_files = sorted(
        [{"path": rel(repo, p), "lines": line_count(p)} for p in source_files if line_count(p) >= 300],
        key=lambda item: item["lines"],
        reverse=True,
    )
    very_large = [item for item in large_files if item["lines"] >= 600]
    generic_modules = [m for m in modules if Path(m["path"]).name.lower() in GENERIC_DIRS]

    import_edges: list[dict[str, str]] = []
    fan_out: dict[str, int] = {}
    fan_in: dict[str, int] = {}
    deep_relative = 0
    cross_layer: list[dict[str, str]] = []
    for path in source_files:
        imports = extract_imports(path)
        fan_out[rel(repo, path)] = len(imports)
        src_layer = layer_for_path(path.relative_to(repo))
        for target in imports:
            if target.startswith("../"):
                deep_relative += target.count("../")
            normalized = target.strip(".").split("/")[0].split(".")[0]
            if normalized:
                fan_in[normalized] = fan_in.get(normalized, 0) + 1
            dst_layer = None
            for layer, words in LAYER_WORDS.items():
                if any(word in target.lower() for word in words):
                    dst_layer = layer
                    break
            if src_layer and dst_layer and src_layer != dst_layer:
                cross_layer.append({"from": rel(repo, path), "from_layer": src_layer, "target": target, "target_layer": dst_layer})
            import_edges.append({"from": rel(repo, path), "target": target})

    top_fan_out = sorted(fan_out.items(), key=lambda item: item[1], reverse=True)[:10]
    top_fan_in = sorted(fan_in.items(), key=lambda item: item[1], reverse=True)[:10]

    contract_files = [
        p for p in files
        if any(h in p.name.lower() or h in str(p.parent).lower() for h in CONTRACT_HINTS)
        or p.suffix in {".proto", ".graphql", ".gql"}
    ]
    migration_files = [p for p in files if "migration" in str(p).lower() or "migrations" in {part.lower() for part in p.parts}]
    runtime_files = [p for p in files if p.name in RUNTIME_FILES or p.suffix in {".tf"} or "k8s" in str(p).lower() or "kubernetes" in str(p).lower()]
    arch_docs = [
        p for p in files
        if p.name in ARCH_DOC_NAMES or ("architecture" in p.name.lower() and p.suffix.lower() in {".md", ".adoc"})
    ]
    adr_files = [p for p in files if "adr" in {part.lower() for part in p.parts} and p.suffix.lower() in {".md", ".adoc"}]
    mermaid_docs = [p for p in files if p.suffix.lower() in {".md", ".mdx"} and "```mermaid" in read_text(p).lower()]
    config_files = [p for p in files if p.suffix.lower() in {".json", ".yaml", ".yml", ".toml", ".ini"} or p.name.startswith(".")]

    categories: dict[str, CategoryScore] = {}

    # A. Module boundaries.
    a_score = 20
    if not modules:
        a_score -= 12
    elif len(modules) == 1 and len(source_files) > 30:
        a_score -= 5
    a_score -= min(5, len(generic_modules))
    a_score -= min(5, len(very_large))
    a_findings = []
    if generic_modules:
        a_findings.append(f"generic shared modules: {', '.join(m['path'] for m in generic_modules[:5])}")
    if very_large:
        a_findings.append(f"very large source files: {', '.join(item['path'] for item in very_large[:3])}")
    categories["A"] = CategoryScore(
        "Module Boundaries & Ownership",
        max(0, a_score),
        20,
        {"modules": modules[:20], "generic_modules": generic_modules, "large_files_600_plus": very_large[:10]},
        a_findings,
    )
    if generic_modules:
        add_action(actions, "Clarify ownership for generic shared modules", "A", "M", 2.0, "Reduces ambiguous edit scope around shared code.", 7)

    # B. Dependency direction.
    b_score = 20
    b_score -= min(6, deep_relative // 5)
    b_score -= min(6, len(cross_layer) // 10)
    b_score -= min(4, sum(1 for _, count in top_fan_out if count >= 20))
    b_findings = []
    if deep_relative:
        b_findings.append(f"deep relative import pressure: {deep_relative}")
    if cross_layer:
        b_findings.append(f"possible cross-layer imports: {len(cross_layer)}")
    categories["B"] = CategoryScore(
        "Dependency Direction & Coupling",
        max(0, b_score),
        20,
        {"import_edges": len(import_edges), "deep_relative_score": deep_relative, "cross_layer_examples": cross_layer[:20], "top_fan_out": top_fan_out, "top_fan_in": top_fan_in},
        b_findings,
    )
    if cross_layer:
        add_action(actions, "Review top cross-layer imports and document accepted directions", "B", "S", 0.75, "Prevents accidental bidirectional dependencies in frequent-change paths.", 8)

    # C. Contracts.
    c_score = 6
    if contract_files:
        c_score += 5
    if migration_files:
        c_score += 2
    if any("schema" in p.name.lower() for p in contract_files):
        c_score += 2
    c_findings = []
    if not contract_files:
        c_findings.append("no obvious API/data contract files found")
        add_action(actions, "Add a discoverable contract index for API and data shapes", "C", "M", 2.5, "Cuts implementation search time for contract-sensitive changes.", 7)
    categories["C"] = CategoryScore(
        "API & Data Contract Clarity",
        min(15, c_score),
        15,
        {"contract_files": [rel(repo, p) for p in contract_files[:30]], "migration_files": len(migration_files)},
        c_findings,
    )

    # D. Runtime shape.
    d_score = 3 + min(5, len(runtime_files) * 2)
    if any(p.name == ".env.example" or p.name == ".env.sample" for p in files):
        d_score += 2
    d_findings = []
    if not runtime_files:
        d_findings.append("no obvious runtime/deployment files found")
    categories["D"] = CategoryScore(
        "Runtime & Deployment Shape",
        min(10, d_score),
        10,
        {"runtime_files": [rel(repo, p) for p in runtime_files[:30]]},
        d_findings,
    )

    # E. Testability.
    test_ratio = len(test_files) / max(1, len(source_files))
    e_score = min(10, round(test_ratio * 40))
    if any("integration" in str(p).lower() or "e2e" in str(p).lower() for p in test_files):
        e_score += 3
    if any(p.name.lower() in {"package.json", "pyproject.toml", "go.mod", "cargo.toml"} for p in files):
        e_score += 2
    e_findings = []
    if test_ratio < 0.15:
        e_findings.append(f"low test-to-source ratio: {len(test_files)}/{len(source_files)}")
        add_action(actions, "Add boundary tests around the highest fan-out module", "E", "M", 3.0, "Creates local evidence before refactoring coupled code.", 8)
    categories["E"] = CategoryScore(
        "Testability & Change Isolation",
        min(15, e_score),
        15,
        {"source_files": len(source_files), "test_files": len(test_files), "test_ratio": round(test_ratio, 3)},
        e_findings,
    )

    # F. Docs.
    f_score = 0
    if arch_docs:
        f_score += 5
    if adr_files:
        f_score += 3
    if mermaid_docs:
        f_score += 2
    f_findings = []
    if not arch_docs:
        f_findings.append("no architecture document found")
        add_action(actions, "Create a one-page architecture map for current module and runtime boundaries", "F", "S", 1.0, "Gives future changes a shared orientation point.", 9)
    categories["F"] = CategoryScore(
        "Architecture Documentation & Decisions",
        min(10, f_score),
        10,
        {"architecture_docs": [rel(repo, p) for p in arch_docs], "adr_files": [rel(repo, p) for p in adr_files[:20]], "mermaid_docs": [rel(repo, p) for p in mermaid_docs[:20]]},
        f_findings,
    )

    # G. Evolution risk.
    g_score = 10
    g_score -= min(4, len(large_files) // 5)
    g_score -= min(3, max(0, len(config_files) - 20) // 10)
    g_score -= min(3, len([m for m in modules if Path(m["path"]).name.lower() in GENERIC_DIRS]))
    g_findings = []
    if large_files:
        g_findings.append(f"large files >=300 lines: {len(large_files)}")
    if len(config_files) > 20:
        g_findings.append(f"config file count: {len(config_files)}")
    categories["G"] = CategoryScore(
        "Evolution Risk & Complexity Hotspots",
        max(0, g_score),
        10,
        {"large_files": large_files[:20], "config_files": len(config_files)},
        g_findings,
    )
    if large_files:
        add_action(actions, "Split the largest file by externally visible responsibility", "G", "L", 6.0, "Reduces review and regression risk in the largest hotspot.", 6)

    total = sum(cat.score for cat in categories.values())
    grade_name, grade_color = grade(total)
    actions.sort(key=lambda action: action.priority, reverse=True)
    weakest = sorted(categories.items(), key=lambda item: item[1].score / item[1].max)[:2]

    return {
        "meta": {
            "repo": repo.name,
            "path": str(repo.resolve()),
            "scored_at": datetime.now(timezone.utc).isoformat(),
            "branch": git_branch(repo),
            "files_total": len(files),
            "source_files": len(source_files),
            "modules_total": len(modules),
            "score_mode": "heuristic baseline; manual review recommended",
        },
        "total": total,
        "grade": grade_name,
        "grade_color": grade_color,
        "categories": {key: asdict(value) for key, value in categories.items()},
        "insights": [
            f"Weakest category: {weakest[0][1].name} ({weakest[0][1].score}/{weakest[0][1].max})" if weakest else "No categories scored.",
            f"Second weakest: {weakest[1][1].name} ({weakest[1][1].score}/{weakest[1][1].max})" if len(weakest) > 1 else "",
        ],
        "actions": [asdict(action) for action in actions],
        "extras": {
            "large_files": large_files[:20],
            "top_fan_out": top_fan_out,
            "top_fan_in": top_fan_in,
            "contract_files": [rel(repo, p) for p in contract_files[:50]],
            "runtime_files": [rel(repo, p) for p in runtime_files[:50]],
        },
    }


def print_markdown(report: dict[str, Any]) -> None:
    print(f"# Architecture Cartography: {report['meta']['repo']}")
    print()
    print(f"Score: **{report['total']}/100 - {report['grade']}**")
    print()
    for key, category in report["categories"].items():
        print(f"- {key}. {category['name']}: {category['score']}/{category['max']}")
        for finding in category.get("findings", [])[:2]:
            print(f"  - {finding}")
    print()
    print("## Top ROI Actions")
    for action in report["actions"][:5]:
        print(f"- [{action['effort']}, priority {action['priority']}] {action['title']} - {action['impact']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    report = score(repo)
    if args.json_path:
        output = Path(args.json_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.markdown or not args.json_path:
        print_markdown(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
