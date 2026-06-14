package audit

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestPortingAuditFixtureParity(t *testing.T) {
	root := t.TempDir()
	source := filepath.Join(root, "codex-rs", "demo")
	targetRepo := filepath.Join(root, "andex-go2")
	target := filepath.Join(targetRepo, "demo")
	writeTestFile(t, filepath.Join(source, "Cargo.toml"), `
[package]
name = "demo"
version = "0.1.0"
edition = "2024"

[dependencies]
andex-utils-absolute-path = { path = "../utils/absolute-path" }
serde_json = "1"
unknown-crate = "1"
`)
	writeTestFile(t, filepath.Join(source, "src", "lib.rs"), `
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
`)
	writeTestFile(t, filepath.Join(source, "tests", "integration.rs"), `
#[tokio::test(flavor = "multi_thread")]
async fn pipes_stdin_and_stdout_through_socket() {}
`)
	writeTestFile(t, filepath.Join(targetRepo, "go.mod"), "module andex-go2\n")
	writeTestFile(t, filepath.Join(targetRepo, "docs", "dependency-grade.md"), `
## 0단계
- `+"`utils/absolute-path`"+`

## 1단계
- `+"`demo`"+`
`)
	writeTestFile(t, filepath.Join(target, "demo.go"), `
package demo

import abspath "andex-go2/utils/absolute-path"

var _ = abspath.AbsolutePathBuf{}

func Demo() {}

func ParseValue() {}
`)
	writeTestFile(t, filepath.Join(target, "demo_test.go"), `
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
`)
	registryPath := filepath.Join(root, "registry.json")
	writeJSONTestFile(t, registryPath, M{"api_mappings": M{"demo": M{"target": "Demo", "status": "mapped"}, "parse_value": M{"target": "ParseValue", "status": "mapped"}}})

	inv, err := Inventory(source, target, targetRepo, registryPath)
	if err != nil {
		t.Fatal(err)
	}
	publicNames := names(toMaps(asMap(asMap(inv["source"])["rust"])["public_items"]))
	if strings.Join(publicNames, ",") != "demo,parse_value" {
		t.Fatalf("public names = %v", publicNames)
	}
	restrictedNames := names(toMaps(asMap(asMap(inv["source"])["rust"])["restricted_items"]))
	if strings.Join(restrictedNames, ",") != "CrateOnly,ScopedOnly,parent_only" {
		t.Fatalf("restricted names = %v", restrictedNames)
	}
	mapping := asMap(inv["test_mapping"])
	if intNum(mapping["matched_source_count"]) != 5 {
		t.Fatalf("mapping = %#v", mapping)
	}
	methods := map[string]string{}
	for _, row := range toMaps(mapping["mappings"]) {
		methods[str(row["source_test"])] = str(row["method"])
	}
	for name, method := range map[string]string{
		"rejects_invalid_host":                  "explicit",
		"serializes_payload_shape":              "name-similarity",
		"parses_value":                          "rust-name-pascal",
		"shuts_down_listener":                   "subtest-name",
		"pipes_stdin_and_stdout_through_socket": "rust-name-pascal",
	} {
		if methods[name] != method {
			t.Fatalf("method[%s] = %q, want %q; all=%v", name, methods[name], method, methods)
		}
	}
	handling := map[string]string{}
	for _, row := range toMaps(inv["deterministic_dependency_audit"]) {
		handling[str(row["source_dependency"])] = str(row["handling"])
	}
	if handling["andex-utils-absolute-path"] != "correct import" || handling["serde_json"] != "standard-library replacement allowed" || handling["unknown-crate"] != "unknown mapping" {
		t.Fatalf("handling = %v", handling)
	}

	suggestions := SuggestMappings(source, target, false)
	if str(asMap(suggestions["parse_value"])["target"]) != "ParseValue" {
		t.Fatalf("suggestions = %#v", suggestions)
	}

	verification := M{
		"go_test_package": M{"status": "pass", "command": "go test ./demo"},
		"go_test_all":     M{"status": "pass", "command": "go test ./..."},
		"porting_rules":   M{"status": "pass", "command": "make check-porting-rules"},
		"lint":            M{"status": "pass", "command": "golangci-lint run ./demo"},
	}
	score := ScoreInventory(inv, verification)
	core := asMap(asMap(score["categories"])["core_behavior_parity"])
	if intNum(core["score"]) != 24 {
		t.Fatalf("core score = %#v", core)
	}
	if !strings.Contains(toStrings(core["evidence"])[0], "mapped_source_tests=10/10, mapping_quality=5/5, public_api=4/4") {
		t.Fatalf("core evidence = %#v", core["evidence"])
	}
	if intNum(asMap(asMap(score["categories"])["api_surface_parity"])["score"]) != 15 {
		t.Fatalf("api score = %#v", asMap(score["categories"])["api_surface_parity"])
	}
	if intNum(asMap(asMap(score["categories"])["integration_build_quality"])["score"]) != 8 {
		t.Fatalf("integration score = %#v", asMap(score["categories"])["integration_build_quality"])
	}
	if len(toMaps(score["actions"])) == 0 {
		t.Fatal("expected actions")
	}

	template := readText(filepath.Join("..", "..", "assets", "template.html"))
	if template == "" {
		t.Fatal("missing template fixture")
	}
	rendered, err := Render(score, template)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(rendered, "Porting Audit Map") || strings.Contains(rendered, "__SCORE__") || strings.Contains(rendered, "{{") {
		t.Fatalf("bad render")
	}
}

func writeTestFile(t *testing.T, path, text string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(strings.TrimSpace(text)+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
}

func writeJSONTestFile(t *testing.T, path string, payload any) {
	t.Helper()
	b, err := json.Marshal(payload)
	if err != nil {
		t.Fatal(err)
	}
	writeTestFile(t, path, string(b))
}

func names(rows []M) []string {
	out := make([]string, 0, len(rows))
	for _, row := range rows {
		out = append(out, str(row["name"]))
	}
	sortStrings(out)
	return out
}

func sortStrings(rows []string) {
	for i := 0; i < len(rows); i++ {
		for j := i + 1; j < len(rows); j++ {
			if rows[j] < rows[i] {
				rows[i], rows[j] = rows[j], rows[i]
			}
		}
	}
}
