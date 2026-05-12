#!/usr/bin/env python3
"""Self-test for the code-cartography scorer and dashboard renderer."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "scripts" / "score.py"
RENDER = ROOT / "scripts" / "render_dashboard.py"
TEMPLATE = ROOT / "assets" / "template.html"


def write_fixture(repo: Path) -> None:
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "domain").mkdir(parents=True)
    (repo / "tests").mkdir(parents=True)
    (repo / "tests" / "domain").mkdir(parents=True)
    (repo / "Assets" / "Scripts" / "Editor" / "UnitAnimation").mkdir(parents=True)
    (repo / "Assets" / "Tests" / "EditMode").mkdir(parents=True)
    (repo / "vendor").mkdir(parents=True)

    (repo / "src" / "service.js").write_text(
        """
import db from './db'
import mailer from './mailer'

export function processOrder(order) {
  // TODO: split validation and side effects
  if (!order) {
    throw new Error('missing order')
  }
  if (order.total > 0) {
    if (order.user) {
      if (order.user.email) {
        mailer.send(order.user.email)
      }
    }
  }
  db.save(order)
}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (repo / "src" / "orchestrator.py").write_text(
        "\n".join(
            [
                "def run(value):",
                "    # FIXME temporary compatibility path",
                "    if value:",
                "        return value",
            ]
            + [f"    step_{i} = value" for i in range(90)]
            + ["    return value"]
        )
        + "\n",
        encoding="utf-8",
    )
    (repo / "tests" / "service.test.js").write_text(
        "test('processes order', () => {})\n",
        encoding="utf-8",
    )
    (repo / "src" / "domain" / "billing.py").write_text(
        "def bill(value):\n    return value\n",
        encoding="utf-8",
    )
    (repo / "tests" / "domain" / "test_billing.py").write_text(
        "def test_bill():\n    assert True\n",
        encoding="utf-8",
    )
    (repo / "Assets" / "Scripts" / "Editor" / "UnitAnimation" / "UnitAnimationPrefabFinalizer.cs").write_text(
        "namespace Example { public class UnitAnimationPrefabFinalizer { public void Save() {} } }\n",
        encoding="utf-8",
    )
    (repo / "Assets" / "Tests" / "EditMode" / "UnitAnimationPrefabFinalizerTests.cs").write_text(
        "namespace Example.Tests { public class UnitAnimationPrefabFinalizerTests { } }\n",
        encoding="utf-8",
    )
    (repo / "vendor" / "generated.js").write_text(
        "function generated() { return 1 }\n",
        encoding="utf-8",
    )


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo = tmp_path / "repo"
        repo.mkdir()
        write_fixture(repo)

        score_json = tmp_path / "code-score.json"
        html = tmp_path / "code-map.html"

        scored = run(
            [
                sys.executable,
                str(SCORE),
                str(repo),
                "--json",
                str(score_json),
                "--markdown",
            ]
        )
        assert scored.returncode == 0, scored.stderr or scored.stdout
        assert score_json.exists(), "score JSON was not written"

        data = json.loads(score_json.read_text(encoding="utf-8"))
        assert data["schema_version"] == "1.0"
        assert data["target"] == str(repo.resolve())
        assert 0 <= data["score"] <= 100
        assert data["grade"].startswith("Maintainability-")
        assert len(data["categories"]) == 8
        assert data["risks"], "expected risk findings"
        assert data["actions"], "expected ROI actions"
        assert any(
            "service.js" in item["path"] for item in data["hotspots"]
        ), "service.js should be identified as a hotspot"
        assert all(
            "vendor/generated.js" not in item.get("path", "")
            for item in data["hotspots"]
        ), "vendor/generated.js should be excluded from hotspots"
        assert data["metrics"]["source_test_proximity"] >= 0.7, (
            "proximity should recognize conventional tests outside source dirs, "
            "including tests/domain/test_billing.py and Unity Assets/Tests/EditMode/FooTests.cs"
        )

        rendered = run(
            [
                sys.executable,
                str(RENDER),
                str(score_json),
                "--template",
                str(TEMPLATE),
                "--out",
                str(html),
            ]
        )
        assert rendered.returncode == 0, rendered.stderr or rendered.stdout
        body = html.read_text(encoding="utf-8")
        assert "Code Cartography" in body
        assert "Local Complexity" in body
        assert "Risk Hotspots" in body
        assert "{{" not in body and "}}" not in body

    print("self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
