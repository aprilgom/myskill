#!/usr/bin/env python3
"""Self-tests for Mission Cartography bundled scripts."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_aligned_project(root: Path) -> None:
    (root / "README.md").write_text(
        """
# Clinic Notes Copilot

## Mission

Mission: Help rural clinic nurses turn handwritten visit notes into accurate,
reviewable patient summaries before the end of each shift.

Target users are rural clinic nurses and supervising physicians. The urgent
problem is that nurses lose 7 hours per week rewriting notes, and interviews
with 14 clinics showed delayed documentation creates patient follow-up risk.

Product scope: OCR-assisted intake, review workflow, physician approval, and
audit history. Roadmap priority is documentation accuracy before billing or
analytics features.

Decision criteria: we will not build general hospital EHR replacement features.
Focus stays on shift-end summary completion and review quality.

Mission metrics: percentage of visits summarized before shift end, correction
rate after physician review, weekly nurse time saved, and monthly feedback loop
with pilot clinics.
""",
        encoding="utf-8",
    )
    (root / "docs").mkdir()
    (root / "docs" / "roadmap.md").write_text(
        """
# Roadmap

North star: rural clinic nurses complete accurate shift-end summaries.

Q1 features prioritize handwritten note capture, review workflow, and feedback
loop reporting. Success criteria include 80% same-day summary adoption and a
correction rate below 5%.
""",
        encoding="utf-8",
    )


def write_buzzy_project(root: Path) -> None:
    (root / "README.md").write_text(
        """
# ImpactOS

Vision: Empower everyone to transform the future with a seamless innovative
platform that unlocks world-class impact.

Our product will revolutionize workflows across every industry. More details
will be decided after launch.
""",
        encoding="utf-8",
    )


def test_score_detects_aligned_mission() -> None:
    score_mod = load_module(SKILL_DIR / "scripts" / "score.py", "mission_score")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        write_aligned_project(root)
        report = score_mod.score(root)

    assert report["meta"]["score_mode"] == "heuristic baseline + manual mission review"
    assert report["total"] >= 75
    assert report["grade"] in {"Mission-Led", "Mission-Aligned"}
    assert report["categories"]["A"]["name"] == "Mission Clarity & Specificity"
    assert report["categories"]["F"]["score"] > 0
    assert report["extras"]["mission_statements"]


def test_score_does_not_overcredit_generic_slogan() -> None:
    score_mod = load_module(SKILL_DIR / "scripts" / "score.py", "mission_score_low_evidence")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        write_buzzy_project(root)
        report = score_mod.score(root)

    assert report["total"] < 40
    assert report["grade"] == "Mission-Drifting"
    assert report["extras"]["manual_review_required"] is True
    assert any("audience" in action["title"].lower() for action in report["actions"])
    assert any("aspirational" in item.lower() for item in report["extras"]["manual_review_checks"])


def test_renderer_replaces_all_placeholders() -> None:
    score_mod = load_module(SKILL_DIR / "scripts" / "score.py", "mission_score_render")
    render_mod = load_module(SKILL_DIR / "scripts" / "render_dashboard.py", "mission_render")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        write_aligned_project(root)
        report = score_mod.score(root)

    template = (SKILL_DIR / "assets" / "template.html").read_text(encoding="utf-8")
    html = render_mod.render(report, template)
    assert "{{" not in html
    assert "Mission Cartography" in html
    assert "Clinic Notes Copilot" in html or report["meta"]["project"] in html
    assert json.loads(json.dumps(report))["total"] == report["total"]


def test_renderer_surfaces_manual_review_checks() -> None:
    score_mod = load_module(SKILL_DIR / "scripts" / "score.py", "mission_score_review")
    render_mod = load_module(SKILL_DIR / "scripts" / "render_dashboard.py", "mission_render_review")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        write_buzzy_project(root)
        report = score_mod.score(root)

    template = (SKILL_DIR / "assets" / "template.html").read_text(encoding="utf-8")
    html = render_mod.render(report, template)
    assert "Manual review required" in html
    assert "aspirational" in html.lower()


def main() -> int:
    tests = [
        test_score_detects_aligned_mission,
        test_score_does_not_overcredit_generic_slogan,
        test_renderer_replaces_all_placeholders,
        test_renderer_surfaces_manual_review_checks,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
