#!/usr/bin/env python3
"""Smoke tests for GitHub Monetization Cartography."""
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


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(*args: str) -> None:
    subprocess.run([sys.executable, *args], check=True)


def fixture_popular_without_revenue(root: Path) -> Path:
    repo = root / "popular-without-revenue"
    write(repo / "README.md", """
# DevCache

DevCache is a popular developer tool with 12,000 stars, 800 forks, active issues,
and many production users. It has a quickstart, Docker install, examples, and API docs.
It is useful for platform teams, but there is no pricing, no paid support, no billing,
and no sponsor tier.
""")
    write(repo / "package.json", '{"name":"devcache","version":"1.4.0"}')
    write(repo / "docs" / "quickstart.md", "Install with npm. Docker demo included.")
    write(repo / "LICENSE", "MIT")
    return repo


def fixture_revenue_ready(root: Path) -> Path:
    repo = root / "revenue-ready"
    write(repo / "README.md", """
# DeployDesk

DeployDesk helps enterprise platform teams audit deployment risk. The economic buyer is
the VP Engineering or platform leader with a compliance budget. Hosted cloud, enterprise
support, and managed onboarding are documented. Pricing starts at $199/month per team.
We have paid pilots, sponsor tiers, Stripe checkout, and a trial landing page.
""")
    write(repo / ".github" / "FUNDING.yml", "github: deploydesk")
    write(repo / "docs" / "enterprise.md", "SLA, support plan, roadmap, paid onboarding, enterprise intake.")
    write(repo / "CHANGELOG.md", "## 2.0.0\nStable API release with semver.")
    write(repo / "pyproject.toml", "[project]\nname='deploydesk'\nversion='2.0.0'")
    write(repo / "LICENSE", "Apache-2.0")
    return repo


def assert_dashboard(score_path: Path, html_path: Path) -> None:
    run(str(RENDER), str(score_path), "--template", str(TEMPLATE), "--out", str(html_path))
    html = html_path.read_text(encoding="utf-8")
    assert len(html) > 1000
    assert "{{" not in html and "}}" not in html
    assert "GitHub Monetization Cartography" in html


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        popular = fixture_popular_without_revenue(root)
        ready = fixture_revenue_ready(root)

        popular_json = root / "popular.json"
        ready_json = root / "ready.json"
        run(str(SCORE), str(popular), "--json", str(popular_json))
        run(str(SCORE), str(ready), "--json", str(ready_json))

        popular_data = json.loads(popular_json.read_text(encoding="utf-8"))
        ready_data = json.loads(ready_json.read_text(encoding="utf-8"))

        assert popular_data["score"] < 70, popular_data
        assert any("Popularity without monetization proof" in risk["title"] for risk in popular_data["risks"])
        assert ready_data["score"] > popular_data["score"], (ready_data, popular_data)
        assert ready_data["signals"]["revenue"] is True
        assert ready_data["actions"], ready_data

        assert_dashboard(popular_json, root / "popular.html")
        assert_dashboard(ready_json, root / "ready.html")
    print("self_test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
