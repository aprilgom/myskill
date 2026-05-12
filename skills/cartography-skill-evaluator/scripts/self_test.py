#!/usr/bin/env python3
"""Self-tests for the cartography skill evaluator scorer."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path


sys.dont_write_bytecode = True
SKILL_DIR = Path(__file__).resolve().parents[1]


def load_score_module():
    path = SKILL_DIR / "scripts" / "score.py"
    spec = importlib.util.spec_from_file_location("cartography_skill_eval_score", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["cartography_skill_eval_score"] = module
    spec.loader.exec_module(module)
    return module


def load_render_module():
    path = SKILL_DIR / "scripts" / "render_dashboard.py"
    spec = importlib.util.spec_from_file_location("cartography_skill_eval_render", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["cartography_skill_eval_render"] = module
    spec.loader.exec_module(module)
    return module


def write_strong_cartography_skill(root: Path) -> Path:
    skill = root / "sample-cartography"
    (skill / "references").mkdir(parents=True)
    (skill / "scripts").mkdir()
    (skill / "assets").mkdir()
    (skill / "agents").mkdir()
    (skill / "SKILL.md").write_text(
        """---
name: sample-cartography
description: Evaluate sample readiness with a 100-point cartography rubric, evidence scanner, JSON score output, dashboard, risks, gaps, and ROI actions. Do not use for legal advice.
---

# Sample Cartography

Evaluates a target and supports a readiness decision. Treat the scanner as a heuristic baseline, not an oracle.

## Expert Model

A competent practitioner inspects decisive evidence first, then checks failure modes, disqualifiers, weak proxy signals, and manual review boundaries. Expert-only judgments must become a manual-review gap rather than a misleading score.

## Rubric

| Cat | Name | Points |
|-----|------|--------|
| A | Evidence Quality | 25 |
| B | Execution Readiness | 20 |
| C | Risk Controls | 20 |
| D | Validation Path | 15 |
| E | Actionability | 20 |

Grades: 85-100 Ready, 70-84 Follow-up, 55-69 Incomplete, 35-54 Risky, <35 Not ready.

## Validation

Run py_compile, self_test, scorer, renderer, and check non-empty HTML with no unresolved placeholder tokens.

## Output

JSON includes schema_version, categories, evidence, risks, actions, extraction_gaps, priority, effort, impact, and Top 3 ROI actions.
""",
        encoding="utf-8",
    )
    (skill / "references" / "sample-rubric.md").write_text(
        "Categories are observable, independent, decision-relevant, and include manual review criteria. The rubric documents expert evaluation priorities, failure modes, disqualifiers, and proxy validity for scanner-detected signals.\n",
        encoding="utf-8",
    )
    (skill / "scripts" / "score.py").write_text(
        """import argparse, json
def main():
    p=argparse.ArgumentParser(); p.add_argument('target'); p.add_argument('--json')
    a=p.parse_args()
    # Weak proxy and expert-only signals are carried as gaps/manual-review notes, not inflated scores.
    report={'schema_version':'1.0','categories':[],'evidence':[{'path':'README.md'}],'risks':[],'actions':[{'priority':90,'effort':'S','impact':'H'}],'extraction_gaps':[]}
    open(a.json,'w').write(json.dumps(report)) if a.json else print(json.dumps(report))
if __name__ == '__main__': main()
""",
        encoding="utf-8",
    )
    (skill / "scripts" / "render_dashboard.py").write_text(
        "import json\nREQUIRED=['categories','actions']\ndef render(report, template):\n    missing=[k for k in REQUIRED if k not in report]\n    if missing: raise KeyError(missing)\n    return template.replace('{{SCORE}}','90')\n",
        encoding="utf-8",
    )
    (skill / "scripts" / "self_test.py").write_text(
        "import tempfile\nfrom pathlib import Path\nwith tempfile.TemporaryDirectory() as d:\n    fixture=Path(d)/'fixture.md'; fixture.write_text('positive evidence plus weak proxy requiring manual-review gap')\n    assert fixture.exists()\n",
        encoding="utf-8",
    )
    (skill / "assets" / "template.html").write_text(
        "<html><body>score {{SCORE}} category evidence risk action gap</body></html>",
        encoding="utf-8",
    )
    (skill / "agents" / "openai.yaml").write_text(
        'interface:\n  display_name: "Sample Cartography"\n',
        encoding="utf-8",
    )
    return skill


def write_weak_skill(root: Path) -> Path:
    skill = root / "weak-cartography"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        """---
name: weak-cartography
description: Evaluate quality.
---

# Weak

Look at things and say if they are good.
""",
        encoding="utf-8",
    )
    return skill


def test_strong_skill_scores_high() -> None:
    score = load_score_module()
    with tempfile.TemporaryDirectory() as temp:
        result = score.evaluate(write_strong_cartography_skill(Path(temp)))
    assert result["score"] >= 80
    assert result["categories"]["rubric_design_quality"]["score"] >= 15
    assert result["categories"]["validation_integrity"]["score"] >= 10


def test_renderer_replaces_all_placeholders() -> None:
    score = load_score_module()
    render = load_render_module()
    with tempfile.TemporaryDirectory() as temp:
        result = score.evaluate(write_strong_cartography_skill(Path(temp)))
    template = (SKILL_DIR / "assets" / "template.html").read_text(encoding="utf-8")
    html = render.render(result, template)
    assert "{{" not in html and "}}" not in html
    assert "__SCORE__" not in html
    assert "Cartography Skill Evaluation Map" in html
    assert "Category Map" in html
    assert str(result["score"]) in html


def test_weak_skill_scores_low() -> None:
    score = load_score_module()
    with tempfile.TemporaryDirectory() as temp:
        result = score.evaluate(write_weak_skill(Path(temp)))
    assert result["score"] < 50
    assert any(finding["severity"] == "P2" for finding in result["findings"])
    assert "risks" in result and "extraction_gaps" in result
    assert result["actions"]


def test_generated_cache_files_are_flagged() -> None:
    score = load_score_module()
    with tempfile.TemporaryDirectory() as temp:
        skill = write_strong_cartography_skill(Path(temp))
        cache = skill / "scripts" / "__pycache__"
        cache.mkdir()
        (cache / "score.cpython-313.pyc").write_bytes(b"cache")
        result = score.evaluate(skill)
    assert result["categories"]["progressive_disclosure_maintainability"]["score"] < 5
    assert any("cache" in finding["title"].lower() for finding in result["findings"])


if __name__ == "__main__":
    test_strong_skill_scores_high()
    test_renderer_replaces_all_placeholders()
    test_weak_skill_scores_low()
    test_generated_cache_files_are_flagged()
    print("self-test passed")
