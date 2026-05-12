#!/usr/bin/env python3
"""Self-test scorer and dashboard rendering for skill-improver."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "scripts" / "score.py"
RENDER = ROOT / "scripts" / "render_dashboard.py"


GOOD_SKILL = """---
name: example-improver
description: Use when asked to improve, fix, upgrade, refactor, or optimize a skill, SKILL.md, metadata, references, or scripts.
---

# Example Improver

## Core Rule
Separate evaluator and improver responsibilities. Do not treat automated score as final.

## Workflow
1. Identify the target skill.
2. Capture a baseline evaluation with --json before.json.
3. Decide scoped improvements.
4. Patch only the target skill.
5. Rerun after.json.
6. Verify frontmatter, referenced files exist, scripts compile with py_compile, self_test passes, no generated cache remains.
7. Report findings, ROI actions, remaining risks, and verification.

## Pattern Reference
Read `references/improvement-patterns.md` when a finding needs a rewrite pattern.

## Output Format
**Before/After**
**Changed Files**
**Improvements**
**Remaining Risks**
**Verification**
"""


WEAK_SKILL = """---
name: vague
description: Helps improve things.
---

# Vague

Do some edits and say it is done.
"""


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def make_skill(root: Path, text: str, include_refs: bool = False) -> Path:
    target = root / ("good" if include_refs else "weak")
    target.mkdir()
    (target / "SKILL.md").write_text(text, encoding="utf-8")
    if include_refs:
        (target / "references").mkdir()
        (target / "references" / "improvement-patterns.md").write_text("# Patterns\n", encoding="utf-8")
        (target / "references" / "rubric.md").write_text("# Rubric\n", encoding="utf-8")
        (target / "scripts").mkdir()
        (target / "scripts" / "score.py").write_text("print('score')\n", encoding="utf-8")
        (target / "scripts" / "render_dashboard.py").write_text("print('render')\n", encoding="utf-8")
        (target / "scripts" / "self_test.py").write_text("assert True\n", encoding="utf-8")
        (target / "assets").mkdir()
        (target / "assets" / "template.html").write_text("<html>fixture</html>\n", encoding="utf-8")
        (target / "agents").mkdir()
        (target / "agents" / "openai.yaml").write_text("interface:\n  display_name: Example\n", encoding="utf-8")
    return target


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        good = make_skill(tmp_path, GOOD_SKILL, include_refs=True)
        weak = make_skill(tmp_path, WEAK_SKILL)
        good_json = tmp_path / "good.json"
        weak_json = tmp_path / "weak.json"
        run([sys.executable, str(SCORE), str(good), "--json", str(good_json), "--markdown"])
        run([sys.executable, str(SCORE), str(weak), "--json", str(weak_json), "--markdown"])
        good_data = json.loads(good_json.read_text(encoding="utf-8"))
        weak_data = json.loads(weak_json.read_text(encoding="utf-8"))
        assert good_data["schema_version"] == "1.0"
        assert good_data["score"] > weak_data["score"]
        assert good_data["actions"] or good_data["score"] == 100
        html_path = tmp_path / "dashboard.html"
        run([sys.executable, str(RENDER), str(good_json), str(html_path)])
        html = html_path.read_text(encoding="utf-8")
        assert html.strip()
        assert "{{" not in html and "}}" not in html
    print("self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

