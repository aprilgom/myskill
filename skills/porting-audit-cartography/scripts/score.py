#!/usr/bin/env python3
"""Score a porting inventory JSON with evidence, gaps, findings, and ROI actions."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from suggest_api_mappings import suggest_mappings


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "scripts" / "porting_inventory.py"

CATEGORIES = {
    "api_surface_parity": ("API surface parity", 15),
    "core_behavior_parity": ("Core behavior parity", 25),
    "edge_cases_error_semantics": ("Edge cases and error semantics", 15),
    "lifecycle_concurrency_platform": ("Lifecycle, concurrency, and platform semantics", 12),
    "dependency_responsibility_boundary": ("Dependency and responsibility boundary fidelity", 13),
    "test_coverage": ("Test coverage ported from source behavior", 12),
    "integration_build_quality": ("Integration/build quality", 8),
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_inventory(args: argparse.Namespace) -> dict[str, Any]:
    command = [
        sys.executable,
        str(INVENTORY),
        "--source",
        str(args.source),
        "--target",
        str(args.target),
        "--repo",
        str(args.repo),
    ]
    if args.dependency_registry:
        command.extend(["--dependency-registry", str(args.dependency_registry)])
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)
    return json.loads(proc.stdout)


def package_arg_for_go_command(target: Path, repo: Path) -> str:
    try:
        rel = target.expanduser().resolve().relative_to(repo.expanduser().resolve())
    except ValueError:
        return str(target)
    rel_text = rel.as_posix()
    if rel_text in {"", "."}:
        return "."
    return "./" + rel_text


def run_verification_command(command: list[str], repo: Path) -> dict[str, Any]:
    proc = subprocess.run(
        command,
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    output = "\n".join(part for part in [proc.stdout.strip(), proc.stderr.strip()] if part)
    return {
        "status": "pass" if proc.returncode == 0 else "fail",
        "command": " ".join(command),
        "exit_code": proc.returncode,
        "summary": output[-4000:],
    }


def collect_verification(args: argparse.Namespace) -> dict[str, Any]:
    if not args.target:
        raise SystemExit("--collect-verification requires --target")
    repo = args.repo.expanduser().resolve()
    package_arg = package_arg_for_go_command(args.target, repo)
    lint_command = args.lint_command or f"golangci-lint run {package_arg}"
    commands = {
        "go_test_package": ["go", "test", package_arg],
        "go_test_all": ["go", "test", "./..."],
        "porting_rules": ["make", "check-porting-rules"],
        "lint": shlex.split(lint_command),
    }
    return {key: run_verification_command(command, repo) for key, command in commands.items()}


def update_api_mappings_registry(args: argparse.Namespace) -> dict[str, Any]:
    if not args.dependency_registry:
        raise SystemExit("--update-api-mappings requires --dependency-registry")
    if not args.source or not args.target:
        raise SystemExit("--update-api-mappings requires --source and --target")

    registry_path = args.dependency_registry.expanduser().resolve()
    repo = args.repo.expanduser().resolve()
    target = args.target.expanduser().resolve()
    package_rel = os.path.relpath(target, repo) if target.exists() else target.name
    registry = read_json(registry_path) if registry_path.exists() else {}
    by_package = registry.get("api_mappings_by_package", {})
    if not isinstance(by_package, dict):
        by_package = {}
    existing = by_package.get(package_rel, {})
    if not isinstance(existing, dict):
        existing = {}

    suggestions = suggest_mappings(
        args.source.expanduser().resolve(),
        args.target.expanduser().resolve(),
        bool(args.include_unmatched_api_mappings),
    )
    merged = dict(existing)
    added = 0
    replaced = 0
    preserved = 0
    for name, row in suggestions.items():
        if name in merged and not args.replace_existing_api_mappings:
            preserved += 1
            continue
        if name in merged:
            replaced += 1
        else:
            added += 1
        merged[name] = row

    by_package[package_rel] = dict(sorted(merged.items()))
    registry["api_mappings_by_package"] = dict(sorted(by_package.items()))
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "path": str(registry_path),
        "package": package_rel,
        "suggested": len(suggestions),
        "added": added,
        "replaced": replaced,
        "preserved": preserved,
        "total": len(merged),
    }


def category(score: int, max_score: int, rationale: str, evidence: list[str], gaps: list[str]) -> dict[str, Any]:
    return {
        "score": max(0, min(score, max_score)),
        "max": max_score,
        "rationale": rationale,
        "evidence": evidence,
        "gaps": gaps,
    }


def evidence_coverage(mappings: list[dict[str, Any]], source_key: str, target_key: str) -> dict[str, Any]:
    relevant = [
        row for row in mappings
        if row.get("status") in {"matched", "weak"} and row.get(source_key)
    ]
    covered = [
        row for row in relevant
        if set(row.get(source_key, [])) & set(row.get(target_key, []))
    ]
    source_tags = sorted({tag for row in relevant for tag in row.get(source_key, [])})
    target_tags = sorted({tag for row in covered for tag in row.get(target_key, [])})
    ratio = len(covered) / max(1, len(relevant)) if relevant else 0.0
    return {
        "relevant": len(relevant),
        "covered": len(covered),
        "ratio": ratio,
        "source_tags": source_tags,
        "target_tags": target_tags,
    }


def mapping_weight(row: dict[str, Any]) -> float:
    status = row.get("status")
    if status == "matched":
        return 1.0
    if status == "weak":
        return 0.7
    return 0.0


def core_mapping_metrics(mappings: list[dict[str, Any]], source_count: int) -> dict[str, Any]:
    denominator = max(1, source_count)
    valid = [row for row in mappings if row.get("status") in {"matched", "weak"}]
    weighted = sum(mapping_weight(row) for row in valid)
    explicit = [row for row in valid if row.get("method") == "explicit"]
    high_confidence = [
        row
        for row in valid
        if row.get("method") == "explicit" or float(row.get("confidence") or 0.0) >= 0.9
    ]

    quality_weight = 0.0
    for row in valid:
        if row.get("method") == "explicit":
            quality_weight += 1.0
        elif float(row.get("confidence") or 0.0) >= 0.9:
            quality_weight += 1.0
        elif row.get("status") == "matched":
            quality_weight += 0.8
        elif row.get("status") == "weak":
            quality_weight += 0.5

    diversity_relevant = 0
    diversity_covered = 0.0
    for row in valid:
        source_edge = set(row.get("source_edge_tags", []))
        source_lifecycle = set(row.get("source_lifecycle_tags", []))
        if not source_edge and not source_lifecycle:
            continue
        diversity_relevant += 1
        edge_ok = not source_edge or bool(source_edge & set(row.get("target_edge_tags", [])))
        lifecycle_ok = not source_lifecycle or bool(source_lifecycle & set(row.get("target_lifecycle_tags", [])))
        if edge_ok and lifecycle_ok:
            diversity_covered += mapping_weight(row)

    return {
        "source_count": source_count,
        "valid_count": len(valid),
        "explicit_count": len(explicit),
        "high_confidence_count": len(high_confidence),
        "weighted_coverage": weighted,
        "coverage_ratio": min(1.0, weighted / denominator),
        "quality_ratio": min(1.0, quality_weight / denominator),
        "diversity_relevant": diversity_relevant,
        "diversity_covered": diversity_covered,
        "diversity_ratio": min(1.0, diversity_covered / max(1, diversity_relevant)) if diversity_relevant else 1.0,
    }


def core_dependency_ratio(missing: list[Any], upward: list[Any], unknown: list[Any]) -> float:
    penalty = len(missing) * 0.35 + len(upward) * 0.5 + len(unknown) * 0.2
    return max(0.0, 1.0 - min(1.0, penalty))


def verification_score(verification: dict[str, Any] | None) -> dict[str, Any]:
    if not verification:
        return {
            "score": 5,
            "evidence": ["inventory JSON produced successfully"],
            "gaps": ["Focused go test, source test, and lint results are not embedded unless supplied externally"],
        }
    required = {
        "go_test_package": 2,
        "go_test_all": 2,
        "porting_rules": 2,
        "lint": 2,
    }
    score = 0
    evidence: list[str] = []
    gaps: list[str] = []
    for key, points in required.items():
        row = verification.get(key, {})
        status = str(row.get("status", "")).lower()
        command = row.get("command", key)
        if status == "pass":
            score += points
            evidence.append(f"{key}: pass ({command})")
        else:
            gaps.append(f"{key}: missing or not passing")
    return {"score": score, "evidence": evidence or ["verification JSON supplied"], "gaps": gaps}


def api_mapping_score(inv: dict[str, Any], rust_public: list[dict[str, Any]], go_public: list[dict[str, Any]]) -> dict[str, Any] | None:
    registry = inv.get("registry", {})
    mappings = registry.get("api_mappings", {}) if isinstance(registry, dict) else {}
    if not isinstance(mappings, dict) or not mappings:
        return None
    mapped = 0.0
    total = max(1, len(rust_public))
    statuses: dict[str, int] = {}
    for source_item in rust_public:
        name = source_item.get("name", "")
        row = mappings.get(name)
        if isinstance(row, str):
            row = {"target": row, "status": "mapped"}
        if not isinstance(row, dict):
            continue
        status = str(row.get("status", "mapped"))
        statuses[status] = statuses.get(status, 0) + 1
        if status in {"mapped", "merged", "internal_equivalent", "not_applicable"}:
            mapped += 1.0
        elif status == "partial":
            mapped += 0.5
    ratio = min(1.0, mapped / total)
    return {
        "ratio": ratio,
        "mapped": mapped,
        "total": total,
        "statuses": statuses,
    }


def score_inventory(inv: dict[str, Any], verification: dict[str, Any] | None = None) -> dict[str, Any]:
    source = inv.get("source", {})
    target = inv.get("target", {})
    rust = source.get("rust", {})
    go = target.get("go", {})
    rust_public = rust.get("public_items", [])
    go_public = go.get("public_items", [])
    rust_tests = rust.get("tests", [])
    go_tests = go.get("tests", [])
    dep_rows = inv.get("deterministic_dependency_audit", [])
    helper_candidates = go.get("local_helper_candidates", [])
    test_mapping = inv.get("test_mapping", {})
    mappings = test_mapping.get("mappings", []) if isinstance(test_mapping.get("mappings", []), list) else []

    findings: list[dict[str, str]] = []

    api_mapping = api_mapping_score(inv, rust_public, go_public)
    if api_mapping:
        api_ratio = api_mapping["ratio"]
        api_evidence = [
            f"mapped API items: {api_mapping['mapped']:.1f}/{api_mapping['total']}",
            f"mapping statuses: {api_mapping['statuses']}",
        ]
        api_rationale = "Scores Rust public API against explicit api_mappings from the dependency registry."
        api_gaps = [] if api_ratio >= 0.85 else ["API mapping coverage below 85%"]
    else:
        api_ratio = min(1.0, len(go_public) / max(1, len(rust_public)))
        api_evidence = [f"source public items: {len(rust_public)}", f"target public items: {len(go_public)}"]
        api_rationale = "Compares extracted source public items against target exported API count; manual review required for exact mapping."
        api_gaps = [] if api_ratio >= 0.85 else [f"Target exports {len(go_public)} items for {len(rust_public)} source public items"]
    api = category(
        round(15 * api_ratio),
        15,
        api_rationale,
        api_evidence,
        api_gaps,
    )

    matched_tests = int(test_mapping.get("matched_source_count", 0) or 0)
    mapped_source_tests = int(test_mapping.get("source_count", 0) or 0)
    if mapped_source_tests:
        test_ratio = min(1.0, matched_tests / max(1, mapped_source_tests))
        test_evidence = [
            f"source tests: {len(rust_tests)}",
            f"target tests: {len(go_tests)}",
            f"matched source tests: {matched_tests}/{mapped_source_tests}",
        ]
        test_rationale = "Scores source tests matched to target tests using explicit porting comments first, then normalized test-name similarity."
        test_gaps = [] if test_ratio >= 1.0 else ["Source tests remain unmatched in test_mapping"]
    else:
        test_ratio = min(1.0, len(go_tests) / max(1, len(rust_tests)))
        test_evidence = [f"source tests: {len(rust_tests)}", f"target tests: {len(go_tests)}"]
        test_rationale = "Compares source and target test inventory as a proxy; manual behavior mapping still required."
        test_gaps = [] if test_ratio >= 1.0 else ["Target has fewer extracted tests than source"]
    tests = category(
        round(12 * test_ratio),
        12,
        test_rationale,
        test_evidence,
        test_gaps,
    )

    correct = [row for row in dep_rows if row.get("handling") == "correct import"]
    missing = [row for row in dep_rows if row.get("handling") == "missing dependency"]
    upward = [row for row in dep_rows if row.get("handling") == "upward dependency violation"]
    unknown = [row for row in dep_rows if row.get("handling") == "unknown mapping"]
    allowed = [
        row
        for row in dep_rows
        if str(row.get("handling", "")).endswith("allowed")
        or row.get("handling") == "allowed local reimplementation"
    ]
    dep_score = 13
    dep_score -= min(8, len(missing) * 3 + len(upward) * 5)
    dep_score -= min(4, len(unknown))
    dep_gaps = []
    if missing:
        dep_gaps.append("Registered Rust dependencies are missing expected target imports")
    if upward:
        dep_gaps.append("Target imports higher-stage package according to dependency-grade parsing")
    if unknown:
        dep_gaps.append("Registry has unknown dependency mappings; manual review required")
    dep = category(
        dep_score,
        13,
        "Uses deterministic_dependency_audit from registry, Go imports, and dependency-grade evidence.",
        [f"correct imports: {len(correct)}", f"allowed replacements: {len(allowed)}"],
        dep_gaps,
    )

    core_metrics = core_mapping_metrics(mappings, mapped_source_tests or len(rust_tests))
    core_dep_ratio = core_dependency_ratio(missing, upward, unknown)
    core_parts = {
        "mapped_source_tests": round(10 * core_metrics["coverage_ratio"]),
        "mapping_quality": round(5 * core_metrics["quality_ratio"]),
        "public_api": round(4 * api_ratio),
        "dependency_cleanliness": round(3 * core_dep_ratio),
        "evidence_diversity": round(3 * core_metrics["diversity_ratio"]),
    }
    core_score = sum(core_parts.values())
    core_gaps = []
    if core_metrics["coverage_ratio"] < 0.9:
        core_gaps.append(
            f"Mapped source-test coverage is {core_metrics['weighted_coverage']:.1f}/{core_metrics['source_count']} after weak-match weighting"
        )
    if core_metrics["quality_ratio"] < 0.9:
        core_gaps.append(
            f"High-confidence/explicit mapping quality is {core_metrics['high_confidence_count']}/{core_metrics['source_count']} source tests"
        )
    if api_ratio < 0.85:
        core_gaps.append(f"Public API ratio is {len(go_public)}/{max(1, len(rust_public))}")
    if core_dep_ratio < 1.0:
        core_gaps.append(
            f"Dependency boundary has missing={len(missing)}, upward={len(upward)}, unknown={len(unknown)}"
        )
    if core_metrics["diversity_ratio"] < 0.9:
        core_gaps.append(
            f"Behavior evidence diversity is {core_metrics['diversity_covered']:.1f}/{core_metrics['diversity_relevant']} tagged source mappings"
        )
    core = category(
        core_score,
        25,
        "Behavior-slice score from mapped source-test coverage (10), high-confidence/explicit mapping quality (5), public API ratio (4), dependency cleanliness (3), and edge/lifecycle evidence diversity (3).",
        [
            f"core subscores: mapped_source_tests={core_parts['mapped_source_tests']}/10, mapping_quality={core_parts['mapping_quality']}/5, public_api={core_parts['public_api']}/4, dependency_cleanliness={core_parts['dependency_cleanliness']}/3, evidence_diversity={core_parts['evidence_diversity']}/3",
            f"mapping coverage: {core_metrics['weighted_coverage']:.1f}/{core_metrics['source_count']} weighted source tests; valid mappings={core_metrics['valid_count']}, explicit={core_metrics['explicit_count']}, high-confidence={core_metrics['high_confidence_count']}",
            f"dependency boundary blockers: missing={len(missing)}, upward={len(upward)}, unknown={len(unknown)}",
            f"tag diversity coverage: {core_metrics['diversity_covered']:.1f}/{core_metrics['diversity_relevant']}",
        ],
        core_gaps or ["Manual review must still confirm semantic equivalence beyond mapped evidence"],
    )

    edge_cov = evidence_coverage(mappings, "source_edge_tags", "target_edge_tags")
    edge_score = round(15 * edge_cov["ratio"]) if edge_cov["relevant"] else (9 if len(go_tests) else 3)
    edge_gaps = [] if edge_cov["ratio"] >= 0.9 else ["Source edge/error tests lack matched target edge evidence"]
    edge = category(
        edge_score,
        15,
        "Scores mapped source edge/error tests whose target tests contain corresponding assertion or failure-mode evidence tags.",
        [
            f"edge evidence coverage: {edge_cov['covered']}/{edge_cov['relevant']}",
            f"source edge tags: {', '.join(edge_cov['source_tags'][:10]) or 'none'}",
            f"target edge tags: {', '.join(edge_cov['target_tags'][:10]) or 'none'}",
        ],
        edge_gaps,
    )

    lifecycle_cov = evidence_coverage(mappings, "source_lifecycle_tags", "target_lifecycle_tags")
    lifecycle_score = round(12 * lifecycle_cov["ratio"]) if lifecycle_cov["relevant"] else (8 if len(go_tests) else 4)
    lifecycle_gaps = [] if lifecycle_cov["ratio"] >= 0.9 else ["Source lifecycle/platform tests lack matched target lifecycle evidence"]
    lifecycle = category(
        lifecycle_score,
        12,
        "Scores mapped source lifecycle/platform tests whose target tests contain corresponding run/shutdown/concurrency/resource/platform evidence tags.",
        [
            f"lifecycle evidence coverage: {lifecycle_cov['covered']}/{lifecycle_cov['relevant']}",
            f"source lifecycle tags: {', '.join(lifecycle_cov['source_tags'][:10]) or 'none'}",
            f"target lifecycle tags: {', '.join(lifecycle_cov['target_tags'][:10]) or 'none'}",
            f"local helper candidates: {len(helper_candidates)}",
        ],
        lifecycle_gaps,
    )

    verification_result = verification_score(verification)
    integration = category(
        verification_result["score"],
        8,
        "Scores supplied verification evidence for focused tests, full tests, porting-rule checks, and lint.",
        verification_result["evidence"],
        verification_result["gaps"],
    )

    if missing:
        findings.append({
            "severity": "P1",
            "title": "Missing registered target dependency",
            "evidence": ", ".join(row.get("source_dependency", "") for row in missing[:5]),
            "fix": "Import the expected ported package or add a narrow registry exception with evidence.",
        })
    if upward:
        findings.append({
            "severity": "P1",
            "title": "Upward dependency violation",
            "evidence": ", ".join(row.get("expected_target_import", "") for row in upward[:5]),
            "fix": "Move behavior downward or depend only on allowed lower-stage packages.",
        })
    if unknown:
        findings.append({
            "severity": "P2",
            "title": "Unknown dependency mapping",
            "evidence": ", ".join(row.get("source_dependency", "") for row in unknown[:5]),
            "fix": "Extend the dependency registry before claiming dependency-boundary parity.",
        })

    categories = {
        "api_surface_parity": api,
        "core_behavior_parity": core,
        "edge_cases_error_semantics": edge,
        "lifecycle_concurrency_platform": lifecycle,
        "dependency_responsibility_boundary": dep,
        "test_coverage": tests,
        "integration_build_quality": integration,
    }
    score = sum(item["score"] for item in categories.values())
    grade = (
        "near complete" if score >= 90 else
        "substantially ported" if score >= 75 else
        "usable partial port" if score >= 50 else
        "skeleton or narrow slice" if score >= 25 else
        "effectively unported"
    )
    actions = make_actions(categories, findings)
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source.get("root", ""),
        "target": target.get("root", ""),
        "score": score,
        "grade": grade,
        "mode": "heuristic baseline; manual-review gap remains for semantic parity",
        "categories": categories,
        "findings": findings,
        "risks": [{"severity": f["severity"], "risk": f["title"], "evidence": f["evidence"]} for f in findings],
        "extraction_gaps": [
            gap for item in categories.values() for gap in item["gaps"]
            if "Manual review" in gap or "unknown" in gap.lower() or "not embedded" in gap
        ],
        "actions": actions,
        "verification": verification or {},
        "inventory": inv,
    }


def make_actions(categories: dict[str, dict[str, Any]], findings: list[dict[str, str]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for key, item in categories.items():
        gap = item["max"] - item["score"]
        if gap <= 0:
            continue
        actions.append({
            "priority": round((gap / max(1, item["max"])) * 100),
            "effort": "S" if gap <= 3 else "M",
            "impact": "H" if key in {"dependency_responsibility_boundary", "core_behavior_parity"} else "M",
            "action": f"Improve {CATEGORIES[key][0]}: {(item['gaps'] or ['add evidence'])[0]}",
        })
    for finding in findings:
        if finding["severity"] == "P1":
            actions.append({"priority": 100, "effort": "M", "impact": "H", "action": finding["fix"]})
    return sorted(actions, key=lambda row: row["priority"], reverse=True)[:8]


def markdown(result: dict[str, Any]) -> str:
    lines = [f"**Score**\n{result['score']}/100 - {result['grade']}", "\n**Rubric Breakdown**"]
    for key, item in result["categories"].items():
        lines.append(f"- {CATEGORIES[key][0]}: {item['score']}/{item['max']}")
    if result.get("registry_update"):
        update = result["registry_update"]
        lines.append(
            "\n**Registry Update**\n"
            f"- api_mappings: +{update['added']} added, {update['replaced']} replaced, "
            f"{update['preserved']} preserved, {update['total']} total"
        )
    if result["findings"]:
        lines.append("\n**Findings**")
        for idx, finding in enumerate(result["findings"][:7], 1):
            lines.append(f"{idx}. [{finding['severity']}] {finding['title']} - {finding['fix']}")
    if result["actions"]:
        lines.append("\n**Top Actions**")
        for idx, action in enumerate(result["actions"][:3], 1):
            lines.append(f"{idx}. [{action['effort']}, priority {action['priority']}] {action['action']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, help="Existing porting_inventory JSON")
    parser.add_argument("--source", type=Path, help="Source package root")
    parser.add_argument("--target", type=Path, help="Target package root")
    parser.add_argument("--repo", type=Path, default=Path("."), help="Target repository root")
    parser.add_argument("--dependency-registry", type=Path)
    parser.add_argument("--verification", type=Path, help="JSON evidence for go tests, lint, and porting checks")
    parser.add_argument(
        "--collect-verification",
        action="store_true",
        help="Run Go tests, porting rules, and lint from --repo and embed verification evidence",
    )
    parser.add_argument(
        "--verification-out",
        type=Path,
        help="Optional path to write collected verification JSON",
    )
    parser.add_argument(
        "--lint-command",
        help="Command to use for --collect-verification lint evidence; default: golangci-lint run <target package>",
    )
    parser.add_argument("--json", dest="json_path", type=Path)
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument(
        "--update-api-mappings",
        action="store_true",
        help="Update dependency-registry api_mappings before inventory and scoring",
    )
    parser.add_argument(
        "--replace-existing-api-mappings",
        action="store_true",
        help="With --update-api-mappings, replace existing api_mappings entries",
    )
    parser.add_argument(
        "--include-unmatched-api-mappings",
        action="store_true",
        help="With --update-api-mappings, add partial review rows for unmapped source APIs",
    )
    args = parser.parse_args()

    registry_update = None
    if args.update_api_mappings:
        if args.inventory:
            raise SystemExit("--update-api-mappings cannot be used with --inventory")
        registry_update = update_api_mappings_registry(args)

    if args.inventory:
        inventory = read_json(args.inventory)
    elif args.source and args.target:
        inventory = run_inventory(args)
    else:
        raise SystemExit("--inventory or both --source and --target are required")

    if args.verification and args.collect_verification:
        raise SystemExit("--verification and --collect-verification are mutually exclusive")
    if args.collect_verification:
        verification = collect_verification(args)
        if args.verification_out:
            args.verification_out.parent.mkdir(parents=True, exist_ok=True)
            args.verification_out.write_text(json.dumps(verification, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        verification = read_json(args.verification) if args.verification else None
    result = score_inventory(inventory, verification)
    if registry_update:
        result["registry_update"] = registry_update
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.markdown or not args.json_path:
        print(markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
