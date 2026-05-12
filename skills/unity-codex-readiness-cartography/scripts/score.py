#!/usr/bin/env python3
"""Unity Codex-Readiness Cartography — Unity project scorer (100 points, 7 categories).

Audits a Unity repository against the 7-category Codex-Ready rubric and emits structured
findings, ROI-ranked actions, and a JSON scorecard suitable for the dashboard
template at assets/template.html.

Usage:
    python score.py [repo_path]                # default: .
    python score.py /path/to/repo --json out.json
    python score.py . --markdown               # human-readable to stdout (default)

Pure stdlib — no external dependencies.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
IGNORE_DIRS = {
    "node_modules", ".venv", "venv", ".git", ".next", "dist", "build",
    "__pycache__", ".turbo", ".ruff_cache", ".pytest_cache", ".mypy_cache",
    "target", "out", "coverage", ".cache", ".idea", ".vscode",
    "Library", "Temp", "Obj", "Build", "Builds", "Logs", "UserSettings",
}
CODE_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".kt", ".rb", ".php", ".sql", ".swift", ".cs"}
UNITY_EXTS = {".cs", ".asmdef", ".unity", ".prefab", ".asset", ".mat", ".shader", ".cginc", ".uss", ".uxml", ".json"}
CONTEXT_FILES = ("AGENTS.md", "CODEX.md", "CLAUDE.md", "README.md")
PRIMARY_CONTEXT = ("AGENTS.md", "CODEX.md")  # Codex-native context
GENERATED_UNITY_DIRS = ("Library", "Temp", "Obj", "Build", "Builds", "Logs", "UserSettings")
EXTERNAL_ASSET_DIR_HINTS = (
    "Assets/Plugins",
    "Assets/ThirdParty",
    "Assets/Vendor",
    "Assets/Vendors",
    "Assets/External",
    "Assets/AssetStoreTools",
    "Assets/AddressableAssetsData",
    "Assets/StreamingAssets",
)

# Heuristic regex
RE_PATH_REF = re.compile(
    r"(?<![A-Za-z0-9_/])"
    r"((?:\./|[A-Za-z0-9_]+/)[A-Za-z0-9_./-]+\.(?:py|ts|tsx|js|jsx|md|sql|json|yaml|yml|toml|html|css|sh|go|rs|java|kt|rb|php|cs|asmdef|unity|prefab|asset|mat|shader|uss|uxml))"
)
RE_BASH_FENCE = re.compile(r"```(?:bash|sh|shell|zsh|console)\s*\n([\s\S]*?)```", re.IGNORECASE)
RE_NON_OBVIOUS = re.compile(r"\b(Why:|Note:|Gotcha|Warning|Don't|Caveat|Important:|반드시|주의)", re.IGNORECASE)
RE_REL_LINK = re.compile(r"\[[^\]]+\]\((?!https?://)([^)]+)\)")
RE_DEPS_HEADING = re.compile(r"^#+\s.*(depend|cross[- ]module|imports?|see also|related)", re.IGNORECASE | re.MULTILINE)
RE_PURPOSE_HEADING = re.compile(r"^#+\s.*(purpose|owns?|configures?|overview)", re.IGNORECASE | re.MULTILINE)
RE_PATTERN_HEADING = re.compile(r"^#+\s.*(pattern|how to|common change|workflow|recipe)", re.IGNORECASE | re.MULTILINE)
RE_MERMAID = re.compile(r"```mermaid", re.IGNORECASE)
RE_VERIFY_CMD = re.compile(r"\b(test|lint|typecheck|build|pytest|vitest|jest|playwright|ruff|mypy|tsc|cargo test|go test|unity|batchmode|editmode|playmode|runTests|testPlatform)\b", re.IGNORECASE)
RE_SAFETY = re.compile(r"\b(secret|env|credential|generated|vendor|third[- ]party|external asset|asset store|migration|do not|don't|never|destructive|reset --hard|checkout --|dirty worktree|\.meta|Library|Temp|Obj|Builds?|Logs|UserSettings|ProjectSettings|Addressables|StreamingAssets|packages-lock|prefab|scene|serialization)\b|비밀|환경변수|생성된|마이그레이션|외부\s*애셋|금지|주의", re.IGNORECASE)
RE_UNITY_RULE = re.compile(r"\b(Unity|Editor|batchmode|EditMode|PlayMode|scene|prefab|\.meta|asmdef|Addressables|ProjectSettings|Packages/manifest|packages-lock|serialization)\b", re.IGNORECASE)


# ----------------------------------------------------------------------------
# Data classes
# ----------------------------------------------------------------------------
@dataclass
class Module:
    path: Path
    rel: str
    code_files: int
    has_context: bool
    context_file: Path | None = None
    context_kind: str = ""  # "CLAUDE.md" | "AGENTS.md" | "README.md" | ""


@dataclass
class CategoryScore:
    name: str
    score: int
    max: int
    evidence: dict[str, Any] = field(default_factory=dict)
    sub_scores: dict[str, int] = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)


@dataclass
class Action:
    title: str
    category: str
    effort: str            # S / M / L
    effort_hours: float
    impact: str            # human-readable
    impact_score: int      # 1-10
    priority: float        # impact / effort_hours


@dataclass
class Report:
    meta: dict[str, Any]
    total: int
    grade: str
    grade_color: str
    categories: dict[str, CategoryScore]
    insights: list[str]
    actions: list[Action]
    extras: dict[str, Any]


@dataclass
class VcsInfo:
    kind: str
    branch: str
    evidence: dict[str, Any] = field(default_factory=dict)


# ----------------------------------------------------------------------------
# Discovery
# ----------------------------------------------------------------------------
def walk_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        for f in files:
            out.append(Path(r) / f)
    return out


def is_unity_project(repo: Path) -> bool:
    return (
        (repo / "Assets").is_dir()
        and (repo / "Packages" / "manifest.json").exists()
        and (repo / "ProjectSettings" / "ProjectVersion.txt").exists()
    )


def unity_version(repo: Path) -> str | None:
    p = repo / "ProjectSettings" / "ProjectVersion.txt"
    text = read_text(p)
    m = re.search(r"m_EditorVersion:\s*(.+)", text)
    return m.group(1).strip() if m else None


def find_external_asset_dirs(repo: Path) -> list[Path]:
    dirs: list[Path] = []
    for hint in EXTERNAL_ASSET_DIR_HINTS:
        p = repo / hint
        if p.is_dir():
            dirs.append(p)
    assets = repo / "Assets"
    if assets.is_dir():
        for p in assets.rglob("*"):
            if not p.is_dir() or any(seg in p.parts for seg in IGNORE_DIRS):
                continue
            name = p.name.lower()
            if any(token in name for token in ("thirdparty", "third_party", "vendor", "external")) and p not in dirs:
                dirs.append(p)
    return sorted(dirs)


def find_generated_dirs_present(repo: Path) -> list[str]:
    return [name for name in GENERATED_UNITY_DIRS if (repo / name).exists()]


def find_core_modules(repo: Path) -> list[Module]:
    """Unity-oriented code/asset-bearing dirs, with generic repo fallback."""
    candidates: list[Path] = []

    assets = repo / "Assets"
    packages = repo / "Packages"
    if assets.is_dir():
        for rel in ("Scripts", "Scenes", "Prefabs", "Editor", "Tests", "Plugins", "Resources", "Settings"):
            d = assets / rel
            if d.is_dir():
                candidates.append(d)
        for d in sorted(assets.iterdir()):
            if d.is_dir() and d.name not in IGNORE_DIRS and not d.name.startswith(".") and d not in candidates:
                candidates.append(d)
    if packages.is_dir():
        for d in sorted(packages.iterdir()):
            if d.is_dir() and d.name not in IGNORE_DIRS and not d.name.startswith("."):
                candidates.append(d)

    if not candidates:
        for d in sorted(repo.iterdir()):
            if not d.is_dir():
                continue
            if d.name in IGNORE_DIRS or d.name.startswith("."):
                continue
            candidates.append(d)

    # monorepo level
    for parent_name in ("apps", "packages", "services"):
        parent = repo / parent_name
        if parent.exists() and parent.is_dir():
            # remove the parent from candidates if there
            candidates = [c for c in candidates if c != parent]
            for d in sorted(parent.iterdir()):
                if d.is_dir() and d.name not in IGNORE_DIRS:
                    candidates.append(d)

    modules: list[Module] = []
    for d in candidates:
        code_count = 0
        for r, dirs, files in os.walk(d):
            dirs[:] = [x for x in dirs if x not in IGNORE_DIRS and not x.startswith(".")]
            for f in files:
                if Path(f).suffix in CODE_EXTS | UNITY_EXTS:
                    code_count += 1
        if code_count == 0:
            continue
        ctx_file, ctx_kind = pick_context_file(d)
        modules.append(Module(
            path=d,
            rel=str(d.relative_to(repo)),
            code_files=code_count,
            has_context=ctx_file is not None,
            context_file=ctx_file,
            context_kind=ctx_kind,
        ))
    return modules


def pick_context_file(d: Path) -> tuple[Path | None, str]:
    for name in CONTEXT_FILES:
        p = d / name
        if p.exists():
            return p, name
    return None, ""


def find_all_context_files(repo: Path) -> list[Path]:
    out: list[Path] = []
    for r, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        for f in files:
            if f in CONTEXT_FILES:
                out.append(Path(r) / f)
    return out


def find_root_codex_context(repo: Path) -> Path | None:
    for name in PRIMARY_CONTEXT:
        p = repo / name
        if p.exists():
            return p
    return None


def count_lines(p: Path) -> int:
    try:
        return len(p.read_text(errors="ignore").splitlines())
    except Exception:
        return 0


def read_text(p: Path) -> str:
    try:
        return p.read_text(errors="ignore")
    except Exception:
        return ""


def file_mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except Exception:
        return 0.0


def detect_vcs(repo: Path) -> VcsInfo:
    """Detect Git vs Unity Version Control/Plastic SCM and current branch."""
    plastic_dir = repo / ".plastic"
    if plastic_dir.exists():
        branch = "unknown"
        try:
            r = subprocess.run(
                ["cm", "status", "--header"],
                cwd=str(repo), capture_output=True, text=True, timeout=10,
            )
            header = r.stdout.strip().splitlines()[0] if r.stdout.strip() else ""
            m = re.match(r"([^@\\s]+)@", header)
            branch = m.group(1) if m else (header or "unknown")
        except Exception:
            pass
        return VcsInfo(
            kind="unity-version-control",
            branch=branch,
            evidence={
                "plastic_dir": True,
                "ignore_conf": (repo / "ignore.conf").exists(),
                "cm_cli": bool(shutil_which("cm")),
            },
        )

    if (repo / ".git").exists():
        return VcsInfo(kind="git", branch=git_branch(repo), evidence={"git_dir": True})

    return VcsInfo(kind="unknown", branch="unknown", evidence={})


def shutil_which(name: str) -> str | None:
    for part in os.environ.get("PATH", "").split(os.pathsep):
        p = Path(part) / name
        if p.exists() and os.access(p, os.X_OK):
            return str(p)
    return None


# ----------------------------------------------------------------------------
# A. Navigation Coverage
# ----------------------------------------------------------------------------
def score_a(modules: list[Module], root_context: Path | None) -> CategoryScore:
    total = max(1, len(modules))
    covered = sum(1 for m in modules if m.has_context)
    root_fallback = max(0, total - covered) * 0.5 if root_context else 0
    coverage = min(1.0, (covered + root_fallback) / total)
    pts = round(coverage * 15)
    if root_context is None:
        pts = max(0, pts - 2)
    pts = max(0, min(15, pts))

    findings: list[str] = []
    if coverage < 1.0:
        gap_modules = [m.rel for m in modules if not m.has_context]
        findings.append(f"context 미보유 핵심 module {len(gap_modules)}개: {', '.join(gap_modules[:6])}")
    if root_context is None:
        findings.append("root AGENTS.md / CODEX.md 부재 — Codex 진입점 브리핑 없음")

    return CategoryScore(
        name="Unity Navigation & Scope Coverage",
        score=pts,
        max=15,
        evidence={
            "core_modules": total,
            "covered_modules": covered,
            "root_context_fallback_modules": root_fallback,
            "coverage_ratio": round(coverage, 3),
            "root_context": str(root_context.name) if root_context else None,
        },
        findings=findings,
    )


# ----------------------------------------------------------------------------
# B. AGENTS.md / Context Quality
# ----------------------------------------------------------------------------
def score_b(context_files: list[Path], repo: Path) -> CategoryScore:
    if not context_files:
        return CategoryScore(name="AGENTS.md / Unity Context Quality", score=0, max=20,
                             evidence={"context_files": 0},
                             findings=["context file 자체가 없음"])

    n = len(context_files)
    sub: dict[str, int] = {}

    # B1 Conciseness — Unity context can be slightly longer because version/test/build
    # details matter. Score = 4 * fraction within sane band.
    line_counts = [count_lines(p) for p in context_files]
    concise = sum(1 for ln in line_counts if 10 <= ln <= 100) / n
    sub["B1_Conciseness"] = round(4 * concise)
    over_long = [(p, ln) for p, ln in zip(context_files, line_counts) if ln > 120]

    # B2 Quick Commands — bash fence plus verification vocabulary
    quick = sum(1 for p in context_files if RE_BASH_FENCE.search(read_text(p)) and RE_VERIFY_CMD.search(read_text(p))) / n
    sub["B2_QuickCommands"] = round(4 * quick)

    # B3 Key Files — 3-5 path refs ideal
    key_ratio = 0.0
    for p in context_files:
        text = read_text(p)
        refs = RE_PATH_REF.findall(text)
        uniq = len(set(refs))
        if uniq >= 3:
            key_ratio += 1
        elif uniq >= 1:
            key_ratio += 0.5
    sub["B3_KeyFiles"] = round(4 * key_ratio / n)

    # B4 Unity-specific non-obvious rules
    nonobvious = sum(1 for p in context_files if RE_NON_OBVIOUS.search(read_text(p)) or RE_UNITY_RULE.search(read_text(p))) / n
    sub["B4_UnityRules"] = round(4 * nonobvious)

    # B5 See Also / cross refs
    crossref = sum(1 for p in context_files if RE_REL_LINK.search(read_text(p))) / n
    sub["B5_CrossRefs"] = round(4 * crossref)

    pts = sum(sub.values())
    pts = max(0, min(20, pts))

    findings: list[str] = []
    if over_long:
        findings.append(
            f"conciseness 초과(>120 lines) context {len(over_long)}건: "
            + ", ".join(f"{p.relative_to(repo)} ({ln})" for p, ln in over_long[:4])
        )
    if sub["B2_QuickCommands"] < 3:
        findings.append("Unity batchmode/EditMode/PlayMode/build quick command 보강 필요")
    if sub["B3_KeyFiles"] < 3:
        findings.append("핵심 Unity 파일 경로(scene/prefab/script/asmdef) 인용 부족 — 3-5개 명시 권장")
    if sub["B4_UnityRules"] < 3:
        findings.append(".meta/scene/prefab/ProjectSettings/package lock 같은 Unity hidden rule 부족")
    if sub["B5_CrossRefs"] < 3:
        findings.append("관련 module / context 간 cross-link 부족")

    return CategoryScore(
        name="AGENTS.md / Unity Context Quality",
        score=pts,
        max=20,
        evidence={
            "context_files": n,
            "max_lines": max(line_counts),
            "min_lines": min(line_counts),
            "unity_rule_contexts": sum(1 for p in context_files if RE_UNITY_RULE.search(read_text(p))),
        },
        sub_scores=sub,
        findings=findings,
    )


# ----------------------------------------------------------------------------
# C. Local Development Workflow Clarity
# ----------------------------------------------------------------------------
def score_c(modules: list[Module], repo: Path) -> CategoryScore:
    if not modules:
        return CategoryScore(name="Local Unity Workflow Clarity", score=0, max=15)

    root_context = find_root_codex_context(repo)
    q_pass = [0, 0, 0, 0, 0]
    n = max(1, len(modules))
    for m in modules:
        context_file = m.context_file or root_context
        if not context_file:
            continue
        text = read_text(context_file)
        lower = text.lower()
        if RE_PURPOSE_HEADING.search(text) or "entry" in lower or "start" in lower:
            q_pass[0] += 1
        if "install" in lower or "setup" in lower or "bootstrap" in lower or "unity hub" in lower or "editorversion" in lower or "projectversion" in lower:
            q_pass[1] += 1
        if RE_VERIFY_CMD.search(text):
            q_pass[2] += 1
        if "known fail" in lower or "slow test" in lower or "flaky" in lower or "platform" in lower or "주의" in text:
            q_pass[3] += 1
        if "done" in lower or "complete" in lower or "final" in lower or "verification" in lower or "완료" in text:
            q_pass[4] += 1

    # Five workflow questions, 3 points each.
    sub = {
        "C1_EntryPoints": round(3 * q_pass[0] / n),
        "C2_SetupInstall": round(3 * q_pass[1] / n),
        "C3_VerificationCommands": round(3 * q_pass[2] / n),
        "C4_KnownFailures": round(3 * q_pass[3] / n),
        "C5_DoneCriteria": round(3 * q_pass[4] / n),
    }
    pts = sum(sub.values())
    pts = max(0, min(15, pts))

    findings: list[str] = []
    if q_pass[2] < n / 2:
        findings.append("변경 후 실행할 Unity EditMode/PlayMode/build 명령이 절반 이상 module에서 누락")
    if q_pass[1] < n / 2:
        findings.append("Unity version/install/package restore 절차가 충분히 문서화되지 않음")
    if q_pass[4] < n / 2:
        findings.append("Codex 작업 완료 기준과 verification evidence 규칙이 부족")

    return CategoryScore(
        name="Local Unity Workflow Clarity",
        score=pts,
        max=15,
        evidence={
            "modules_total": n,
            "entry_points": q_pass[0],
            "setup_install": q_pass[1],
            "verification_commands": q_pass[2],
            "known_failures": q_pass[3],
            "done_criteria": q_pass[4],
        },
        sub_scores=sub,
        findings=findings,
    )


# ----------------------------------------------------------------------------
# D. Cross-Module Dependency & Data Flow Mapping
# ----------------------------------------------------------------------------
def score_d(repo: Path, context_files: list[Path]) -> CategoryScore:
    has_arch = any((repo / p).exists() for p in (
        "ARCHITECTURE.md", "docs/architecture.md", "docs/ARCHITECTURE.md",
        "docs/dependency-graph.md", "docs/data-flow.md",
    ))
    has_mermaid = any(RE_MERMAID.search(read_text(p)) for p in context_files)
    has_deps_section = sum(1 for p in context_files if RE_DEPS_HEADING.search(read_text(p)))
    asmdefs = [p for p in repo.glob("Assets/**/*.asmdef") if not any(seg in p.parts for seg in IGNORE_DIRS)]
    scenes = [p for p in repo.glob("Assets/**/*.unity") if not any(seg in p.parts for seg in IGNORE_DIRS)]
    has_package_manifest = (repo / "Packages" / "manifest.json").exists()

    pts = 0
    if has_arch:
        pts += 6
    if has_mermaid:
        pts += 3
    if has_deps_section >= max(1, len(context_files) // 2):
        pts += 4
    elif has_deps_section >= 1:
        pts += 2
    if asmdefs:
        pts += 2  # assembly graph derivable
    if scenes and has_package_manifest:
        pts += 1
    pts = max(0, min(15, pts))

    findings: list[str] = []
    if not has_arch:
        findings.append("ARCHITECTURE.md / Unity scene·assembly dependency map 부재")
    if not has_mermaid:
        findings.append("mermaid 다이어그램 없음 — 시각적 의존도 표현 부재")
    if has_deps_section == 0:
        findings.append("어떤 context file에도 scene/assembly/package dependency 섹션 없음")

    return CategoryScore(
        name="Scene, Assembly & Dependency Mapping",
        score=pts,
        max=15,
        evidence={
            "architecture_doc": has_arch,
            "mermaid_diagrams": has_mermaid,
            "context_with_deps_section": has_deps_section,
            "asmdef_count": len(asmdefs),
            "scene_count": len(scenes),
            "package_manifest": has_package_manifest,
        },
        findings=findings,
    )


# ----------------------------------------------------------------------------
# E. Verification Gates & Testability
# ----------------------------------------------------------------------------
def score_e(repo: Path, context_files: list[Path], vcs: VcsInfo) -> CategoryScore:
    sub: dict[str, int] = {}

    # E1 Reference accuracy: parse all path-like refs from context, verify existence
    total_refs = 0
    bad_refs: list[tuple[Path, str]] = []
    for p in context_files:
        text = read_text(p)
        for ref in set(RE_PATH_REF.findall(text)):
            if ref.startswith("./../"):
                continue
            total_refs += 1
            # try repo-relative and context-file-relative
            candidates = [repo / ref, p.parent / ref]
            if not any(c.exists() for c in candidates):
                bad_refs.append((p, ref))
    if total_refs == 0:
        sub["E1_RefAccuracy"] = 2  # neutral — nothing to verify
    else:
        accuracy = (total_refs - len(bad_refs)) / total_refs
        sub["E1_RefAccuracy"] = round(5 * accuracy)

    # E2 Review / completion evidence infra, adapted to the detected VCS.
    if vcs.kind == "unity-version-control":
        root_text = "\n".join(read_text(p) for p in (repo / "AGENTS.md", repo / "CODEX.md") if p.exists())
        has_codeowners = bool(re.search(r"\bowner|review|reviewer|검토|소유", root_text, re.IGNORECASE))
        has_pr_template = bool(re.search(r"\bcheckin|changeset|cm status|cm checkin|verification", root_text, re.IGNORECASE))
    else:
        has_codeowners = any((repo / p).exists() for p in (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS"))
        has_pr_template = any((repo / p).exists() for p in (
            ".github/pull_request_template.md", ".github/PULL_REQUEST_TEMPLATE.md",
        ))
    e2 = 0
    if has_codeowners:
        e2 += 2
    if has_pr_template:
        e2 += 2
    sub["E2_ReviewEvidence"] = e2

    # E3 Unity task validation commands actually exist
    have_pkg_json = (repo / "package.json").exists()
    have_pyproject = (repo / "pyproject.toml").exists() or (repo / "apps/api/pyproject.toml").exists() or any(repo.glob("**/pyproject.toml"))
    have_make = (repo / "Makefile").exists()
    have_unity_project = is_unity_project(repo)
    have_tests = any(repo.glob("Assets/**/Tests/**/*.cs")) or any(repo.glob("Assets/**/*Tests*.asmdef"))
    have_editor_tests = any("Editor" in p.parts or "EditMode" in p.parts for p in repo.glob("Assets/**/Tests/**/*.cs"))
    have_play_tests = any("PlayMode" in p.parts for p in repo.glob("Assets/**/Tests/**/*.cs"))
    have_build_method = any(
        re.search(r"\bBuildPipeline\.BuildPlayer\b|\bBuildPlayerOptions\b", read_text(p))
        for p in repo.glob("Assets/**/*.cs")
        if not any(seg in p.parts for seg in IGNORE_DIRS)
    )
    have_husky = (repo / ".husky").exists() or (repo / ".husky").is_dir()
    have_workflows = (repo / ".github" / "workflows").exists()
    have_vcs_workflow = have_workflows or (vcs.kind == "unity-version-control" and bool(re.search(
        r"cm status|cm checkin|changeset|Unity Version Control|Plastic", "\n".join(read_text(p) for p in context_files),
        re.IGNORECASE,
    )))
    e3 = 0
    if have_unity_project or have_pkg_json or have_pyproject or have_make:
        e3 += 2
    if have_tests:
        e3 += 2
    if have_editor_tests or have_play_tests:
        e3 += 1
    if have_build_method:
        e3 += 1
    if have_vcs_workflow:
        e3 += 1
    has_verify_in_context = any(RE_VERIFY_CMD.search(read_text(p)) for p in context_files)
    if has_verify_in_context:
        e3 += 2
    sub["E3_TaskValidation"] = min(8, e3)

    # E4 Prompt / agent eval tests
    has_evals = any((repo / p).exists() for p in ("evals", "benchmarks", "agent-evals", "prompts/test", "tests/agent"))
    sub["E4_AgentWorkflowTests"] = 3 if has_evals else 0

    pts = sum(sub.values())
    pts = max(0, min(20, pts))

    findings: list[str] = []
    if bad_refs:
        sample = ", ".join(f"{p.relative_to(repo)}: {ref}" for p, ref in bad_refs[:4])
        findings.append(f"hallucinated path {len(bad_refs)}건 (총 {total_refs} 참조 중) — 예: {sample}")
    if not has_codeowners and not has_pr_template:
        if vcs.kind == "unity-version-control":
            findings.append("Unity Version Control checkin/review 규칙 없음 — changeset evidence 기록 약함")
        else:
            findings.append("CODEOWNERS / PR template 없음 — review 및 test evidence 기록 약함")
    if not has_evals:
        findings.append("agent eval / workflow test 디렉터리 없음 — Codex 작업 회귀 catch 없음")
    if not have_tests:
        findings.append("Unity Test Framework 테스트(Assets/**/Tests)가 감지되지 않음")
    if not has_verify_in_context:
        findings.append("AGENTS.md/context에 Unity local verification command 명시 부족")

    return CategoryScore(
        name="Unity Verification Gates & Testability",
        score=pts,
        max=20,
        evidence={
            "ref_total": total_refs,
            "ref_broken": len(bad_refs),
            "codeowners": has_codeowners,
            "pr_template": has_pr_template,
            "ci_workflows": have_workflows,
            "vcs_workflow": have_vcs_workflow,
            "husky": have_husky,
            "unity_project": have_unity_project,
            "unity_tests": have_tests,
            "editor_tests": have_editor_tests,
            "playmode_tests": have_play_tests,
            "build_method": have_build_method,
            "evals_dir": has_evals,
            "verify_commands_in_context": has_verify_in_context,
        },
        sub_scores=sub,
        findings=findings,
    )


# ----------------------------------------------------------------------------
# F. Safety, Secrets & Change Boundaries
# ----------------------------------------------------------------------------
def latest_code_mtime(d: Path) -> float:
    latest = 0.0
    for r, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in IGNORE_DIRS and not x.startswith(".")]
        for f in files:
            if Path(f).suffix in CODE_EXTS:
                latest = max(latest, file_mtime(Path(r) / f))
    return latest


def score_f(modules: list[Module], repo: Path, vcs: VcsInfo) -> CategoryScore:
    context_files = [m.context_file for m in modules if m.context_file] + [p for p in (repo / "AGENTS.md", repo / "CODEX.md") if p.exists()]
    safety_hits = sum(1 for p in context_files if p and RE_SAFETY.search(read_text(p)))
    has_env_example = any((repo / p).exists() for p in (".env.example", ".env.sample", "env.example"))
    ignore_path = repo / ("ignore.conf" if vcs.kind == "unity-version-control" else ".gitignore")
    ignore_text = read_text(ignore_path) if ignore_path.exists() else ""
    has_ignore_env = bool(ignore_path.exists() and re.search(r"\.env|secrets?|private", ignore_text, re.IGNORECASE))
    has_generated_hint = any(re.search(r"generated|do not edit|vendored|vendor|third[- ]party|external asset|asset store|migration|Library|Temp|Obj|Builds?|Logs|UserSettings|\.meta|ProjectSettings|Addressables|StreamingAssets|packages-lock", read_text(p), re.IGNORECASE) for p in context_files if p)
    has_unity_ignore = all(re.search(pat, ignore_text, re.IGNORECASE) for pat in (r"Library", r"Temp", r"Obj", r"Build"))
    external_asset_dirs = find_external_asset_dirs(repo)
    has_external_asset_boundary = (
        not external_asset_dirs
        or any(re.search(r"vendor|third[- ]party|external asset|asset store|Addressables|StreamingAssets|do not edit|수정\s*금지|외부\s*애셋", read_text(p), re.IGNORECASE) for p in context_files if p)
    )
    generated_dirs_present = find_generated_dirs_present(repo)

    pts = 0
    if context_files:
        pts += round(3 * safety_hits / len(context_files))
    if has_env_example:
        pts += 2
    if has_ignore_env:
        pts += 2
    if has_generated_hint:
        pts += 2
    if has_unity_ignore:
        pts += 1
    if has_external_asset_boundary:
        pts += 1
    pts = max(0, min(10, pts))

    findings: list[str] = []
    if not safety_hits:
        findings.append("AGENTS.md/context에 secrets, .meta, generated Unity dirs, ProjectSettings, destructive command 경계가 부족")
    if not has_env_example:
        findings.append(".env.example / .env.sample 부재 — 환경변수 계약이 불명확")
    if not has_ignore_env:
        findings.append(f"{ignore_path.name}에 .env/secrets/private 보호 규칙 확인 필요")
    if not has_unity_ignore:
        findings.append(f"{ignore_path.name}에 Unity generated dirs(Library/Temp/Obj/Builds/Logs/UserSettings) 보호 규칙 확인 필요")
    if external_asset_dirs and not has_external_asset_boundary:
        sample = ", ".join(str(p.relative_to(repo).as_posix()) for p in external_asset_dirs[:4])
        findings.append(f"외부 애셋 후보 경계 문서화 필요: {sample}")

    return CategoryScore(
        name="Asset, Package & Secret Safety Boundaries",
        score=pts,
        max=10,
        evidence={
            "context_files_checked": len(context_files),
            "safety_context_hits": safety_hits,
            "env_example": has_env_example,
            "ignore_file": str(ignore_path.name) if ignore_path.exists() else None,
            "ignore_env": bool(has_ignore_env),
            "unity_ignore": bool(has_unity_ignore),
            "generated_boundaries": has_generated_hint,
            "generated_dirs_present": generated_dirs_present,
            "external_asset_dirs": [str(p.relative_to(repo).as_posix()) for p in external_asset_dirs],
            "external_asset_boundary": bool(has_external_asset_boundary),
        },
        findings=findings,
    )


# ----------------------------------------------------------------------------
# G. Agent Performance Outcomes
# ----------------------------------------------------------------------------
def score_g(repo: Path) -> CategoryScore:
    eval_dirs = [p for p in ("evals", "benchmarks", "agent-evals", "agent-metrics") if (repo / p).exists()]
    metric_files = list(repo.glob("**/agent-results.json")) + list(repo.glob("**/.skill-eval.json"))
    metric_files = [m for m in metric_files if not any(seg in m.parts for seg in IGNORE_DIRS)]
    has_telemetry_hint = any(
        re.search(r"telemetry|opentelemetry|codex|agent.*log|task.*metric",
                  read_text(p), re.IGNORECASE)
        for p in (repo / "AGENTS.md", repo / "CODEX.md", repo / "README.md")
        if p.exists()
    )

    pts = 0
    if eval_dirs:
        pts += 3
    if metric_files:
        pts += 1
    if has_telemetry_hint:
        pts += 1
    pts = max(0, min(5, pts))

    findings: list[str] = []
    if not eval_dirs and not metric_files:
        findings.append("agent eval / benchmark 디렉터리·결과 파일 부재 — Codex 성능 측정 인프라 없음")
    if not has_telemetry_hint:
        findings.append("Codex/agent usage telemetry 단서 없음 (task metrics / OpenTelemetry)")

    return CategoryScore(
        name="Agent Outcome Evidence",
        score=pts,
        max=5,
        evidence={
            "eval_dirs": eval_dirs,
            "metric_files": [str(p.relative_to(repo)) for p in metric_files],
            "telemetry_hint": has_telemetry_hint,
        },
        findings=findings,
    )


# ----------------------------------------------------------------------------
# Bonus / extras: large files, naming hints
# ----------------------------------------------------------------------------
def find_large_files(repo: Path, threshold: int = 300) -> list[tuple[Path, int]]:
    out: list[tuple[Path, int]] = []
    for p in walk_files(repo):
        if p.suffix not in CODE_EXTS:
            continue
        ln = count_lines(p)
        if ln > threshold:
            out.append((p, ln))
    out.sort(key=lambda x: -x[1])
    return out


# ----------------------------------------------------------------------------
# Grade & ROI
# ----------------------------------------------------------------------------
def grade_label(total: int) -> tuple[str, str]:
    if total >= 90:
        return "Codex-Native", "green"
    if total >= 75:
        return "Codex-Ready", "green"
    if total >= 60:
        return "Codex-Assisted", "amber"
    if total >= 40:
        return "Codex-Fragile", "amber"
    return "Codex-Hostile", "red"


def derive_actions(report_partial: dict[str, CategoryScore], modules: list[Module],
                    large_files: list[tuple[Path, int]], repo: Path) -> list[Action]:
    actions: list[Action] = []
    A, B, C, D, E, F, G = (report_partial[k] for k in "ABCDEFG")

    # A — missing context files
    missing = [m.rel for m in modules if not m.has_context]
    if missing:
        actions.append(Action(
            title=f"{len(missing)}개 핵심 module에 AGENTS.md 신설 ({', '.join(missing[:3])}{'…' if len(missing) > 3 else ''})",
            category="A",
            effort="S", effort_hours=0.5 * len(missing),
            impact="Codex가 scope와 verification을 바로 파악 → task당 ~3 min 절감",
            impact_score=9,
            priority=9 / max(0.5, 0.5 * len(missing)),
        ))

    # B — over-long context
    if B.evidence.get("max_lines", 0) > 100:
        actions.append(Action(
            title="과도한 context를 25-80 lines로 압축하고 AGENTS.md 중심으로 정리",
            category="B",
            effort="M", effort_hours=2.0,
            impact="agent context 로드 시간 단축 + 핵심 정보 가시성 ↑",
            impact_score=7,
            priority=7 / 2.0,
        ))

    # C — weak local workflow
    if C.score < 9:
        actions.append(Action(
            title="AGENTS.md에 Unity version, EditMode/PlayMode/build, done criteria 보강",
            category="C",
            effort="S", effort_hours=1.0,
            impact="수정 후 Unity 검증 루프 명확화 → 미검증 완료 보고 감소",
            impact_score=8,
            priority=8 / 1.0,
        ))

    # D — no architecture doc
    if not D.evidence.get("architecture_doc"):
        actions.append(Action(
            title="ARCHITECTURE.md 또는 Mermaid scene/asmdef/package dependency 다이어그램 추가",
            category="D",
            effort="M", effort_hours=2.5,
            impact="scene/prefab/assembly ripple 추적 → 변경 영향 분석 시간 절반",
            impact_score=7,
            priority=7 / 2.5,
        ))

    # E1 — broken refs
    if E.evidence.get("ref_broken", 0) > 0:
        actions.append(Action(
            title=f"context의 hallucinated path {E.evidence['ref_broken']}건 수정 (referential trust)",
            category="E",
            effort="S", effort_hours=0.5,
            impact="agent의 잘못된 path-following 방지 — stale = worse than missing",
            impact_score=10,
            priority=10 / 0.5,
        ))

    # F — safety boundaries
    if F.score < 6:
        actions.append(Action(
            title="AGENTS.md에 .meta, generated Unity dirs, ProjectSettings, secrets 경계 추가",
            category="F",
            effort="S", effort_hours=1.0,
            impact="asset GUID 손상, generated 파일 오염, 민감정보 사고 방지",
            impact_score=8,
            priority=8 / 1.0,
        ))
    if F.evidence.get("external_asset_dirs") and not F.evidence.get("external_asset_boundary"):
        actions.append(Action(
            title="외부 애셋 후보(Plugins/ThirdParty/Vendor/Addressables/StreamingAssets)의 수정 경계 문서화",
            category="F",
            effort="S", effort_hours=0.75,
            impact="Asset Store/imported/runtime data를 Codex가 임의 수정하는 사고 방지",
            impact_score=9,
            priority=9 / 0.75,
        ))

    # 7 (large files) — included in B/C symptom but suggested separately
    huge = [(p, ln) for p, ln in large_files if ln > 500]
    if huge:
        sample = ", ".join(f"{p.relative_to(repo).as_posix()} ({ln})" for p, ln in huge[:3])
        actions.append(Action(
            title=f"god file {len(huge)}개 분할 (>500 lines): {sample}",
            category="B",
            effort="L", effort_hours=2.5 * len(huge),
            impact=f"파일당 ~5K-10K token 절감 + 편집 정확도 ↑",
            impact_score=6,
            priority=6 / max(2.5, 2.5 * len(huge)),
        ))

    # G — no eval infra
    if G.score < 3:
        actions.append(Action(
            title="evals/ 디렉터리 + 대표 Unity task pass-rate 측정 도입",
            category="G",
            effort="L", effort_hours=6.0,
            impact="Codex Unity 작업 회귀 측정 가능 — 개선 ROI 자체를 정량화",
            impact_score=6,
            priority=6 / 6.0,
        ))

    actions.sort(key=lambda a: -a.priority)
    return actions


# ----------------------------------------------------------------------------
# Generate insights
# ----------------------------------------------------------------------------
def generate_insights(cats: dict[str, CategoryScore], total: int) -> list[str]:
    out: list[str] = []
    grade, _ = grade_label(total)
    out.append(f"총점 {total}/100 · 등급 {grade}")

    # weakest categories
    norm = sorted(cats.items(), key=lambda kv: kv[1].score / kv[1].max)
    weakest = norm[:2]
    for k, c in weakest:
        out.append(f"가장 낮은 카테고리: {k} {c.name} {c.score}/{c.max}")

    # E1 hallucination is special
    e = cats.get("E")
    if e and e.evidence.get("ref_broken", 0) > 0:
        out.append(
            f"context에 hallucinated path {e.evidence['ref_broken']}건 — Codex는 잘못된 파일을 수정할 수 있음"
        )

    # F safety
    f = cats.get("F")
    if f and f.score < 6:
        out.append("Codex safety boundary 약함 — .meta/generated Unity dirs/ProjectSettings/secrets 규칙 보강 필요")
    if f and f.evidence.get("external_asset_dirs") and not f.evidence.get("external_asset_boundary"):
        out.append(f"외부 애셋 후보 {len(f.evidence['external_asset_dirs'])}개 — 수정 가능/금지 경계 문서화 필요")

    return out


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def git_branch(repo: Path) -> str:
    try:
        r = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def build_report(repo: Path) -> Report:
    modules = find_core_modules(repo)
    context_files = find_all_context_files(repo)
    root_context = find_root_codex_context(repo)
    large_files = find_large_files(repo, 300)
    vcs = detect_vcs(repo)

    cats = {
        "A": score_a(modules, root_context),
        "B": score_b(context_files, repo),
        "C": score_c(modules, repo),
        "D": score_d(repo, context_files),
        "E": score_e(repo, context_files, vcs),
        "F": score_f(modules, repo, vcs),
        "G": score_g(repo),
    }
    total = sum(c.score for c in cats.values())
    grade, color = grade_label(total)
    actions = derive_actions(cats, modules, large_files, repo)
    insights = generate_insights(cats, total)

    return Report(
        meta={
            "repo": repo.name,
            "path": str(repo.resolve()),
            "scored_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "vcs_kind": vcs.kind,
            "branch": vcs.branch,
            "git_branch": vcs.branch if vcs.kind == "git" else "n/a",
            "vcs": asdict(vcs),
            "rubric_version": "unity-codex-v1-100pt",
            "unity_project": is_unity_project(repo),
            "unity_version": unity_version(repo),
            "modules_total": len(modules),
            "context_files_total": len(context_files),
            "large_files_300plus": len(large_files),
            "generated_unity_dirs_present": find_generated_dirs_present(repo),
            "external_asset_dirs_total": len(find_external_asset_dirs(repo)),
        },
        total=total,
        grade=grade,
        grade_color=color,
        categories=cats,
        insights=insights,
        actions=actions,
        extras={
            "modules": [asdict(m) | {"path": str(m.path), "context_file": str(m.context_file) if m.context_file else None} for m in modules],
            "large_files": [
                {"path": str(p.relative_to(repo).as_posix()), "lines": ln}
                for p, ln in large_files[:30]
            ],
            "external_asset_dirs": [
                {"path": str(p.relative_to(repo).as_posix())}
                for p in find_external_asset_dirs(repo)
            ],
            "generated_unity_dirs_present": find_generated_dirs_present(repo),
        },
    )


def serialize(report: Report) -> dict[str, Any]:
    cats = {k: asdict(c) for k, c in report.categories.items()}
    return {
        "meta": report.meta,
        "total": report.total,
        "grade": report.grade,
        "grade_color": report.grade_color,
        "categories": cats,
        "insights": report.insights,
        "actions": [asdict(a) for a in report.actions],
        "extras": report.extras,
    }


def render_markdown(report: Report) -> str:
    lines = []
    lines.append(f"# Codex-Readiness Audit · {report.meta['repo']}")
    lines.append("")
    lines.append(f"**Score:** {report.total}/100 · **Grade:** {report.grade}")
    lines.append(f"**VCS:** `{report.meta.get('vcs_kind', 'unknown')}` · **Branch:** `{report.meta.get('branch', 'unknown')}` · **Scored:** {report.meta['scored_at']}")
    lines.append(f"**Modules:** {report.meta['modules_total']} · **Context files:** {report.meta['context_files_total']} · **Large files (>300 ln):** {report.meta['large_files_300plus']}")
    lines.append(f"**Unity boundaries:** generated dirs present {len(report.extras['generated_unity_dirs_present'])} · external asset candidates {len(report.extras['external_asset_dirs'])}")
    lines.append("")

    lines.append("## Category Scores")
    lines.append("")
    lines.append("| Cat | Name | Score |")
    lines.append("|-----|------|-------|")
    for k, c in report.categories.items():
        lines.append(f"| {k} | {c.name} | **{c.score}/{c.max}** |")
    lines.append("")

    lines.append("## Insights")
    for ins in report.insights:
        lines.append(f"- {ins}")
    lines.append("")

    lines.append("## Findings (per category)")
    for k, c in report.categories.items():
        if not c.findings:
            continue
        lines.append(f"### {k}. {c.name}  ({c.score}/{c.max})")
        for f in c.findings:
            lines.append(f"- {f}")
    lines.append("")

    lines.append("## Top Actions (ranked by ROI)")
    lines.append("")
    lines.append("| # | Effort | Action | Impact |")
    lines.append("|---|--------|--------|--------|")
    for i, a in enumerate(report.actions[:8], 1):
        lines.append(f"| {i} | {a.effort} ({a.effort_hours:.1f} hr) | [{a.category}] {a.title} | {a.impact} |")
    lines.append("")

    if report.extras["large_files"]:
        lines.append("## Large Files (>300 lines)")
        for lf in report.extras["large_files"][:10]:
            lines.append(f"- {lf['path']} — **{lf['lines']}** lines")
        lines.append("")

    if report.extras["external_asset_dirs"]:
        lines.append("## External Asset Boundary Candidates")
        for item in report.extras["external_asset_dirs"][:12]:
            lines.append(f"- {item['path']}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("repo", nargs="?", default=".", help="repo path (default: cwd)")
    p.add_argument("--json", dest="json_out", help="write JSON report to this path")
    p.add_argument("--markdown", action="store_true", help="emit markdown to stdout (default)")
    p.add_argument("--quiet", action="store_true", help="suppress stdout output")
    args = p.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"error: repo path not found: {repo}", file=sys.stderr)
        return 2

    report = build_report(repo)
    payload = serialize(report)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        if args.json_out and not args.markdown:
            # default: when writing json, also print summary
            print(render_markdown(report))
        elif args.markdown or not args.json_out:
            print(render_markdown(report))

    return 0


if __name__ == "__main__":
    sys.exit(main())
