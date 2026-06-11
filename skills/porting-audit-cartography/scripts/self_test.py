#!/usr/bin/env python3
"""Smoke-test porting_inventory deterministic dependency audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "porting_inventory.py"
SCORE = ROOT / "scripts" / "score.py"
RENDER = ROOT / "scripts" / "render_dashboard.py"
SUGGEST_API_MAPPINGS = ROOT / "scripts" / "suggest_api_mappings.py"
TEMPLATE = ROOT / "assets" / "template.html"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "andex-rs" / "demo"
        target_repo = root / "andex-go2"
        target = target_repo / "demo"

        write(
            source / "Cargo.toml",
            """
[package]
name = "demo"
version = "0.1.0"
edition = "2024"

[dependencies]
andex-utils-absolute-path = { path = "../utils/absolute-path" }
serde_json = "1"
unknown-crate = "1"
""".strip(),
        )
        write(
            source / "src" / "lib.rs",
            """
pub fn demo() {}
pub fn parse_value() {}
pub(super) fn parent_only() {}
pub(crate) struct CrateOnly;
pub(in crate::demo) enum ScopedOnly {}

#[test]
fn rejects_invalid_host() {}

#[test]
fn serializes_payload_shape() {
    let _ = serde_json::to_string("payload").unwrap();
}

#[test]
fn parses_value() {}

#[test]
fn shuts_down_listener() {}
""".strip()
            + "\n",
        )
        write(
            source / "tests" / "integration.rs",
            """
#[tokio::test(flavor = "multi_thread")]
async fn pipes_stdin_and_stdout_through_socket() {}
""".strip()
            + "\n",
        )
        write(target_repo / "go.mod", "module andex-go2\n")
        write(
            target_repo / "docs" / "dependency-grade.md",
            """
## 0단계
- `utils/absolute-path`

## 1단계
- `demo`
""".strip(),
        )
        write(
            target / "demo.go",
            """
package demo

import abspath "andex-go2/utils/absolute-path"

var _ = abspath.AbsolutePathBuf{}

func Demo() {}

func ParseValue() {}
""".strip(),
        )
        write(
            target / "demo_test.go",
            """
package demo

import "testing"

// porting: rust-test=rejects_invalid_host
func TestDemo_shouldRejectInvalidHost(t *testing.T) {}

func TestDemo_shouldSerializePayloadShape(t *testing.T) {
    t.Log("json marshal payload")
}

func TestParsesValue(t *testing.T) {}

func TestNetworkProxyRustParity(t *testing.T) {
    t.Run("shuts_down_listener", func(t *testing.T) {
        t.Log("shutdown listener close")
    })
}

func TestPipesStdinAndStdoutThroughSocket(t *testing.T) {
    t.Log("listener socket stdin stdout close")
}
""".strip()
            + "\n",
        )
        registry_json = root / "registry.json"
        write(
            registry_json,
            json.dumps(
                {
                    "api_mappings": {
                        "demo": {"target": "Demo", "status": "mapped"},
                        "parse_value": {"target": "ParseValue", "status": "mapped"},
                    }
                }
            ),
        )
        verification_json = root / "verification.json"
        write(
            verification_json,
            json.dumps(
                {
                    "go_test_package": {"status": "pass", "command": "go test ./demo"},
                    "go_test_all": {"status": "pass", "command": "go test ./..."},
                    "porting_rules": {"status": "pass", "command": "make check-porting-rules"},
                    "lint": {"status": "pass", "command": "golangci-lint run ./demo"},
                }
            ),
        )

        inventory_json = root / "inventory.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--source",
                str(source),
                "--target",
                str(target),
                "--repo",
                str(target_repo),
                "--dependency-registry",
                str(registry_json),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            raise AssertionError(proc.stderr)
        inventory_json.write_text(proc.stdout, encoding="utf-8")
        payload = json.loads(proc.stdout)
        public_names = {item["name"] for item in payload["source"]["rust"]["public_items"]}
        restricted_names = {item["name"] for item in payload["source"]["rust"]["restricted_items"]}
        assert public_names == {"demo", "parse_value"}, public_names
        assert restricted_names == {"parent_only", "CrateOnly", "ScopedOnly"}, restricted_names
        mapping = payload["test_mapping"]
        assert mapping["matched_source_count"] == 5, mapping
        methods = {row["source_test"]: row["method"] for row in mapping["mappings"]}
        assert methods["rejects_invalid_host"] == "explicit", methods
        assert methods["serializes_payload_shape"] == "name-similarity", methods
        assert methods["parses_value"] == "rust-name-pascal", methods
        assert methods["shuts_down_listener"] == "subtest-name", methods
        assert methods["pipes_stdin_and_stdout_through_socket"] == "rust-name-pascal", methods
        serialize = next(row for row in mapping["mappings"] if row["source_test"] == "serializes_payload_shape")
        assert "serialization" in serialize["source_edge_tags"], serialize
        assert "serialization" in serialize["target_edge_tags"], serialize
        rows = payload["deterministic_dependency_audit"]
        handling = {row["source_dependency"]: row["handling"] for row in rows}
        assert handling["andex-utils-absolute-path"] == "correct import", handling
        assert handling["serde_json"] == "standard-library replacement allowed", handling
        assert handling["unknown-crate"] == "unknown mapping", handling

        suggest_input_registry_json = root / "suggest-input-registry.json"
        write(
            suggest_input_registry_json,
            json.dumps({"api_mappings": {"demo": {"target": "Demo", "status": "mapped"}}}),
        )
        suggested_registry_json = root / "suggested-registry.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(SUGGEST_API_MAPPINGS),
                "--source",
                str(source),
                "--target",
                str(target),
                "--repo",
                str(target_repo),
                "--dependency-registry",
                str(suggest_input_registry_json),
                "--out",
                str(suggested_registry_json),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            raise AssertionError(proc.stderr)
        suggested_registry = json.loads(suggested_registry_json.read_text(encoding="utf-8"))
        suggested_mappings = suggested_registry["api_mappings"]
        assert suggested_mappings["demo"]["target"] == "Demo", suggested_mappings
        assert suggested_mappings["demo"]["status"] == "mapped", suggested_mappings
        assert suggested_mappings["parse_value"]["target"] == "ParseValue", suggested_mappings
        assert suggested_mappings["parse_value"]["method"] == "snake-to-pascal", suggested_mappings

        score_json = root / "score.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(SCORE),
                "--inventory",
                str(inventory_json),
                "--json",
                str(score_json),
                "--verification",
                str(verification_json),
                "--markdown",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            raise AssertionError(proc.stderr)
        score = json.loads(score_json.read_text(encoding="utf-8"))
        assert score["schema_version"] == "1.0"
        assert "manual-review gap" in score["mode"]
        core = score["categories"]["core_behavior_parity"]
        assert core["score"] == 24, core
        assert "mapped_source_tests=10/10, mapping_quality=5/5, public_api=4/4" in core["evidence"][0], core
        assert score["categories"]["api_surface_parity"]["score"] == 15
        assert score["categories"]["integration_build_quality"]["score"] == 8
        assert score["categories"]["dependency_responsibility_boundary"]["score"] < 13
        assert score["actions"], "expected ROI actions for fixture gaps"

        weaker_payload = json.loads(inventory_json.read_text(encoding="utf-8"))
        weaker_payload["test_mapping"]["mappings"][0]["status"] = "weak"
        weaker_payload["test_mapping"]["mappings"][0]["confidence"] = 0.6
        weaker_payload["test_mapping"]["mappings"][0]["method"] = "name-similarity"
        weaker_payload["test_mapping"]["mappings"][0]["target_edge_tags"] = []
        weaker_inventory_json = root / "inventory-weaker.json"
        weaker_score_json = root / "score-weaker.json"
        weaker_inventory_json.write_text(json.dumps(weaker_payload), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SCORE), "--inventory", str(weaker_inventory_json), "--json", str(weaker_score_json)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            raise AssertionError(proc.stderr)
        weaker_score = json.loads(weaker_score_json.read_text(encoding="utf-8"))
        weaker_core = weaker_score["categories"]["core_behavior_parity"]
        assert weaker_core["score"] < core["score"], (core, weaker_core)
        assert "Behavior evidence diversity" in " ".join(weaker_core["gaps"]), weaker_core

        update_registry_json = root / "update-registry.json"
        write(update_registry_json, json.dumps({"api_mappings": {"demo": {"target": "Demo", "status": "mapped"}}}))
        update_score_json = root / "score-update.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(SCORE),
                "--source",
                str(source),
                "--target",
                str(target),
                "--repo",
                str(target_repo),
                "--dependency-registry",
                str(update_registry_json),
                "--update-api-mappings",
                "--json",
                str(update_score_json),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            raise AssertionError(proc.stderr)
        updated_registry = json.loads(update_registry_json.read_text(encoding="utf-8"))
        updated_mappings = updated_registry["api_mappings_by_package"]["demo"]
        assert updated_mappings["parse_value"]["target"] == "ParseValue", updated_registry
        update_score = json.loads(update_score_json.read_text(encoding="utf-8"))
        assert update_score["registry_update"]["added"] == 2, update_score["registry_update"]
        assert update_score["registry_update"]["preserved"] == 0, update_score["registry_update"]

        html_path = root / "audit.html"
        proc = subprocess.run(
            [
                sys.executable,
                str(RENDER),
                str(score_json),
                "--template",
                str(TEMPLATE),
                "--out",
                str(html_path),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            raise AssertionError(proc.stderr)
        html = html_path.read_text(encoding="utf-8")
        assert "Porting Audit Map" in html
        assert "__SCORE__" not in html
        assert "{{" not in html and "}}" not in html

    print("porting_inventory self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
