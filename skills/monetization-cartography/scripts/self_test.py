#!/usr/bin/env python3
"""Self-tests for Monetization Cartography bundled scripts."""
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


def write_sample_project(root: Path) -> None:
    (root / "README.md").write_text(
        """
# Revenue Ops Copilot

ICP: seed-stage B2B SaaS founders and revops leads who lose 6 hours per week
cleaning CRM data before board reporting. Buyer: VP Sales or founder.

Pricing: $99/month starter, $499/month team, and annual contracts for agencies.
Willingness to pay was validated through 18 customer interviews, 4 LOIs, and
2 paid pilots. Current MRR is $1.8k with 82% gross margin.

Distribution: founder-led sales, HubSpot marketplace listing, and agency
partners. Funnel target is 8% website-to-trial conversion with a 21 day sales
cycle for team accounts.

Unit economics: CAC target $180, LTV target $1,400, payback under 3 months.
Next experiment: paid onboarding for 10 pilot customers.
""",
        encoding="utf-8",
    )


def write_low_evidence_project(root: Path) -> None:
    (root / "launch-plan.md").write_text(
        """
# Growth Platform

Our scalable platform unlocks monetization, revenue growth, pricing strategy,
subscription expansion, conversion optimization, sales acceleration, ROI,
channels, marketplace reach, funnels, retention, enterprise packaging, and
customer success.

The product will transform the market with a viral launch and strong brand
momentum. We will evaluate business model options after the next release.
""",
        encoding="utf-8",
    )


def write_proxy_only_project(root: Path) -> None:
    (root / "traction.md").write_text(
        """
# Open Analytics Toolkit

The project has 42,000 GitHub stars, 120,000 downloads, a 9,000 person waitlist,
heavy community engagement, strong newsletter traffic, and many inbound users.
Enterprise teams love the product and the roadmap includes marketplace growth,
sales acceleration, conversion optimization, subscription expansion, and premium
packaging after the next release.

No payer, price point, paid pilot, checkout, contract, MRR, ARR, CAC, margin, or
conversion target has been selected yet.
""",
        encoding="utf-8",
    )


def test_score_detects_monetization_readiness() -> None:
    score_mod = load_module(SKILL_DIR / "scripts" / "score.py", "monetization_score")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        write_sample_project(root)
        report = score_mod.score(root)

    assert report["meta"]["score_mode"] == "heuristic baseline + manual monetization review"
    assert report["total"] >= 70
    assert report["grade"] in {"Monetization-Ready", "Revenue Experiment Ready"}
    assert report["categories"]["C"]["name"] == "Pricing & Packaging"
    assert report["categories"]["E"]["score"] > 0
    assert any("experiment" in action["title"].lower() for action in report["actions"])


def test_score_does_not_overcredit_generic_revenue_buzzwords() -> None:
    score_mod = load_module(SKILL_DIR / "scripts" / "score.py", "monetization_score_low_evidence")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        write_low_evidence_project(root)
        report = score_mod.score(root)

    assert report["total"] < 35
    assert report["grade"] == "Not Yet Monetizable"
    assert any(
        "unknown" in action["title"].lower() or "gap" in action["title"].lower()
        for action in report["actions"]
    )
    assert report["extras"]["manual_review_required"] is True
    assert any("buyer" in item.lower() for item in report["extras"]["manual_review_checks"])


def test_score_rejects_weak_proxy_audience_signals_as_revenue_proof() -> None:
    """Weak proxy audience signals must become gaps instead of inflated scores."""
    score_mod = load_module(SKILL_DIR / "scripts" / "score.py", "monetization_score_proxy_only")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        write_proxy_only_project(root)
        report = score_mod.score(root)

    assert report["total"] < 35
    assert report["grade"] == "Not Yet Monetizable"
    assert report["categories"]["D"]["score"] <= 4
    assert report["extras"]["proof_signals"]["buyer"] is False
    assert report["extras"]["proof_signals"]["price"] is False
    assert report["extras"]["proof_signals"]["revenue"] is False
    assert any("Core proof gap" in item for item in report["extras"]["manual_review_checks"])


def test_renderer_replaces_all_placeholders() -> None:
    score_mod = load_module(SKILL_DIR / "scripts" / "score.py", "monetization_score_render")
    render_mod = load_module(SKILL_DIR / "scripts" / "render_dashboard.py", "monetization_render")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        write_sample_project(root)
        report = score_mod.score(root)

    template = (SKILL_DIR / "assets" / "template.html").read_text(encoding="utf-8")
    html = render_mod.render(report, template)
    assert "{{" not in html
    assert "Revenue Ops Copilot" in html or report["meta"]["project"] in html
    assert "Monetization Cartography" in html
    assert json.loads(json.dumps(report))["total"] == report["total"]


def test_renderer_surfaces_manual_review_checks() -> None:
    score_mod = load_module(SKILL_DIR / "scripts" / "score.py", "monetization_score_review")
    render_mod = load_module(SKILL_DIR / "scripts" / "render_dashboard.py", "monetization_render_review")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        write_low_evidence_project(root)
        report = score_mod.score(root)

    template = (SKILL_DIR / "assets" / "template.html").read_text(encoding="utf-8")
    html = render_mod.render(report, template)
    assert "Manual review required" in html
    assert "buyer" in html.lower()


def main() -> int:
    tests = [
        test_score_detects_monetization_readiness,
        test_score_does_not_overcredit_generic_revenue_buzzwords,
        test_score_rejects_weak_proxy_audience_signals_as_revenue_proof,
        test_renderer_replaces_all_placeholders,
        test_renderer_surfaces_manual_review_checks,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
