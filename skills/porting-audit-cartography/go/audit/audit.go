package audit

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"html"
	"math"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
	"unicode"
)

type M map[string]any

var (
	rustPublicRE     = regexp.MustCompile(`(?m)^\s*pub\s+(struct|enum|trait|type|const|static|mod|fn)\s+([A-Za-z_][A-Za-z0-9_]*)`)
	rustImplFnRE     = regexp.MustCompile(`(?m)^\s*pub\s+(?:async\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)`)
	rustRestrictedRE = regexp.MustCompile(`(?m)^\s*pub\(([^)]*)\)\s+(struct|enum|trait|type|const|static|mod|fn)\s+([A-Za-z_][A-Za-z0-9_]*)`)
	rustRestrFnRE    = regexp.MustCompile(`(?m)^\s*pub\(([^)]*)\)\s+(?:async\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)`)
	rustUseRE        = regexp.MustCompile(`(?m)^\s*use\s+([^;]+);`)
	rustTestRE       = regexp.MustCompile(`(?m)#\[(?:tokio::)?test(?:\([^]]*\))?\]\s*(?:async\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)`)
	goDeclRE         = regexp.MustCompile(`(?m)^\s*(?:func\s+(?:\([^)]*\)\s*)?([A-Z][A-Za-z0-9_]*)|type\s+([A-Z][A-Za-z0-9_]*)|(?:const|var)\s+([A-Z][A-Za-z0-9_]*))\b`)
	goTestRE         = regexp.MustCompile(`(?m)^\s*func\s+(Test[A-Za-z0-9_]+)\s*\(`)
	goPortingRE      = regexp.MustCompile(`^\s*//\s*porting:\s*rust-test=([A-Za-z_][A-Za-z0-9_]*)`)
	goSubtestRE      = regexp.MustCompile(`\bt\.Run\(\s*"([A-Za-z_][A-Za-z0-9_]*)"`)
)

var standardReplacements = M{
	"anyhow":             "go error wrapping",
	"chrono":             "time",
	"clap":               "target CLI parser or flag package",
	"codex-git-utils":    "Go tests and target-owned git metadata fields",
	"dirs":               "os.UserHomeDir and path/filepath",
	"dunce":              "path/filepath plus target-owned Windows extended path cleanup helper",
	"libc":               "syscall or golang.org/x/sys/unix",
	"log":                "log/slog and target-owned logging adapter",
	"owo-colors":         "not applicable for non-TTY Go package tests",
	"pretty_assertions":  "Go testing diagnostics",
	"serde":              "encoding/json or typed Go structs",
	"serde_json":         "encoding/json",
	"socket2":            "syscall or net Unix socket primitives",
	"sqlx":               "database/sql plus modernc.org/sqlite",
	"strum":              "target-owned string constants and enum helper methods",
	"tempfile":           "testing.T.TempDir or os.MkdirTemp",
	"thiserror":          "Go error types",
	"tokio":              "goroutines, channels, context, and standard I/O primitives",
	"tokio-util":         "context cancellation and package-owned synchronization",
	"tracing":            "standard logging or target package diagnostics",
	"tracing-subscriber": "standard logging setup or target package diagnostics",
	"uuid":               "protocol ThreadID wrappers and target-owned process UUID generation",
}

var tokenSynonyms = map[string]string{"allows": "allow", "allowed": "allow", "allowlisted": "allowlist", "allowlist": "allowlist", "blocks": "block", "blocked": "block", "blocking": "block", "denied": "deny", "denies": "deny", "disallowed": "deny", "disallows": "deny", "rejects": "reject", "rejected": "reject", "requires": "require", "required": "require", "fails": "error", "failure": "error", "invalid": "invalid", "malformed": "invalid", "serializes": "serialize", "serialized": "serialize", "marshal": "serialize", "marshals": "serialize", "json": "serialize", "timeouts": "timeout", "timed": "timeout", "times": "timeout", "out": "timeout", "shutdown": "shutdown", "shuts": "shutdown", "stops": "shutdown", "started": "start", "starts": "start", "running": "run", "runs": "run", "mismatched": "mismatch", "mismatches": "mismatch", "strip": "strip", "strips": "strip", "stripped": "strip", "supports": "support", "supported": "support", "wildcards": "wildcard", "globset": "matcher"}
var stopTokens = map[string]bool{"test": true, "should": true, "when": true, "with": true, "without": true, "and": true, "or": true, "is": true, "are": true, "the": true, "a": true, "an": true, "for": true, "to": true, "from": true, "on": true, "in": true, "by": true, "be": true, "as": true, "go": true, "rust": true, "runtime": true, "http": true, "proxy": true, "inner": true, "url": true, "contains": true, "credentials": true, "telemetry": true}
var edgePatterns = map[string][]string{"error": {"error", "err", "fail", "failure", "unwrap_err", "is_err"}, "reject": {"reject", "block", "deny", "denied", "forbidden", "not_allowed"}, "invalid": {"invalid", "missing", "malformed", "mismatch"}, "serialization": {"json", "marshal", "serialize", "payload", "omitempty", "serde_json"}, "http_response": {"statuscode", "status code", "http.status", ".status", "header", "x-proxy-error", "body"}, "timeout_dns": {"timeout", "deadline", "lookupipaddr", "lookup_host", "dns"}}
var lifecyclePatterns = map[string][]string{"run_shutdown": {"run", "shutdown", "wait", "close", "serve", "listener"}, "cancellation": {"context.withcancel", "withcancel", "cancel()", ".cancel", "done", "closed"}, "concurrency": {"go func", "goroutine", "mutex", "rwmutex", "chan ", "channel"}, "resource_cleanup": {"defer", "close", "remove", "tempdir", "sync", "fsync"}, "platform": {"runtime.goos", "darwin", "macos", "windows", "unix", "symlink", "chmod", "0600", "socket"}}

func ReadJSON(path string) (M, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var out M
	err = json.Unmarshal(b, &out)
	return out, err
}

func WriteJSON(path string, payload any) error {
	b, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		return err
	}
	b = append(b, '\n')
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, b, 0o644)
}

func readText(path string) string {
	b, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	return string(b)
}

func relFiles(root string) []string {
	var out []string
	filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		name := d.Name()
		if d.IsDir() && (name == ".git" || name == "target" || name == "vendor") {
			return filepath.SkipDir
		}
		if !d.IsDir() {
			rel, _ := filepath.Rel(root, path)
			out = append(out, filepath.ToSlash(rel))
		}
		return nil
	})
	sort.Strings(out)
	return out
}

func cargoDependencies(source string) M {
	text := readText(filepath.Join(source, "Cargo.toml"))
	sections := M{"dependencies": []string{}, "dev-dependencies": []string{}, "build-dependencies": []string{}}
	current := ""
	depRE := regexp.MustCompile(`^([A-Za-z0-9_.-]+)\s*=`)
	for _, line := range strings.Split(text, "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
			name := strings.Trim(line, "[]")
			if _, ok := sections[name]; ok {
				current = name
			} else {
				current = ""
			}
			continue
		}
		if current == "" || line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if m := depRE.FindStringSubmatch(line); m != nil {
			sections[current] = append(sections[current].([]string), m[1])
		}
	}
	for k, v := range sections {
		sort.Strings(v.([]string))
		sections[k] = v
	}
	return sections
}

func RustItems(source string) M {
	var files []string
	for _, dir := range []string{filepath.Join(source, "src"), filepath.Join(source, "tests")} {
		filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
			if err == nil && !d.IsDir() && strings.HasSuffix(path, ".rs") {
				files = append(files, path)
			}
			return nil
		})
	}
	sort.Strings(files)
	var public, restricted, tests []M
	uses := map[string]bool{}
	for _, file := range files {
		text := readText(file)
		rel, _ := filepath.Rel(source, file)
		rel = filepath.ToSlash(rel)
		for _, m := range rustPublicRE.FindAllStringSubmatch(text, -1) {
			public = append(public, M{"file": rel, "kind": m[1], "name": m[2]})
		}
		for _, m := range rustImplFnRE.FindAllStringSubmatch(text, -1) {
			public = append(public, M{"file": rel, "kind": "fn", "name": m[1]})
		}
		for _, m := range rustRestrictedRE.FindAllStringSubmatch(text, -1) {
			restricted = append(restricted, M{"file": rel, "scope": m[1], "kind": m[2], "name": m[3]})
		}
		for _, m := range rustRestrFnRE.FindAllStringSubmatch(text, -1) {
			restricted = append(restricted, M{"file": rel, "scope": m[1], "kind": "fn", "name": m[2]})
		}
		for _, loc := range rustTestRE.FindAllStringSubmatchIndex(text, -1) {
			name := text[loc[2]:loc[3]]
			tests = append(tests, testRecord(rel, name, functionBodyAfter(text, loc[1])))
		}
		for _, m := range rustUseRE.FindAllStringSubmatch(text, -1) {
			uses[strings.TrimSpace(m[1])] = true
		}
	}
	return M{"public_items": unique(public), "restricted_items": unique(restricted), "tests": unique(tests), "uses": sortedKeys(uses), "dependencies": cargoDependencies(source)}
}

func GoItems(target string) M {
	entries, _ := filepath.Glob(filepath.Join(target, "*.go"))
	sort.Strings(entries)
	var public, tests, helpers, explicit []M
	imports := map[string]bool{}
	for _, file := range entries {
		text := readText(file)
		rel := filepath.Base(file)
		for _, imp := range parseGoImports(text) {
			imports[imp] = true
		}
		if !strings.HasSuffix(file, "_test.go") {
			for _, m := range goDeclRE.FindAllStringSubmatch(text, -1) {
				kind, name := "var", m[3]
				if m[1] != "" {
					kind, name = "func", m[1]
				} else if m[2] != "" {
					kind, name = "type", m[2]
				}
				public = append(public, M{"file": rel, "kind": kind, "name": name})
			}
		}
		for _, loc := range goTestRE.FindAllStringSubmatchIndex(text, -1) {
			name := text[loc[2]:loc[3]]
			tests = append(tests, testRecord(rel, name, functionBodyAfter(text, loc[1])))
		}
		explicit = append(explicit, goExplicitTestMappings(text, rel)...)
		for _, m := range regexp.MustCompile(`(?m)^\s*func\s+([a-z][A-Za-z0-9_]*)\s*\(`).FindAllStringSubmatch(text, -1) {
			helpers = append(helpers, M{"file": rel, "name": m[1]})
		}
	}
	return M{"package": goPackageName(target), "public_items": unique(public), "tests": unique(tests), "explicit_test_mappings": unique(explicit), "imports": sortedKeys(imports), "local_helper_candidates": unique(helpers), "go_list_imports": goListImports(target)}
}

func goPackageName(path string) string {
	files, _ := filepath.Glob(filepath.Join(path, "*.go"))
	sort.Strings(files)
	re := regexp.MustCompile(`(?m)^\s*package\s+([A-Za-z_][A-Za-z0-9_]*)`)
	for _, file := range files {
		if m := re.FindStringSubmatch(readText(file)); m != nil {
			return m[1]
		}
	}
	return ""
}

func parseGoImports(text string) []string {
	var out []string
	for _, block := range regexp.MustCompile(`(?s)import\s*\((.*?)\)`).FindAllStringSubmatch(text, -1) {
		for _, q := range regexp.MustCompile(`"([^"]+)"`).FindAllStringSubmatch(block[1], -1) {
			out = append(out, q[1])
		}
	}
	for _, m := range regexp.MustCompile(`(?m)^\s*import\s+(?:[._A-Za-z0-9]+\s+)?"([^"]+)"`).FindAllStringSubmatch(text, -1) {
		out = append(out, m[1])
	}
	return out
}

func functionBodyAfter(text string, start int) string {
	open := strings.Index(text[start:], "{")
	if open < 0 {
		return ""
	}
	open += start
	depth := 0
	var in rune
	escaped := false
	for i, r := range text[open:] {
		idx := open + i
		if in != 0 {
			if escaped {
				escaped = false
			} else if r == '\\' {
				escaped = true
			} else if r == in {
				in = 0
			}
			continue
		}
		if r == '"' || r == '\'' || r == '`' {
			in = r
			continue
		}
		if r == '{' {
			depth++
		} else if r == '}' {
			depth--
			if depth == 0 {
				return text[open+1 : idx]
			}
		}
	}
	return text[open+1:]
}

func testRecord(rel, name, body string) M {
	tags, edge, lifecycle := testEvidence(name, body)
	return M{"file": rel, "name": name, "evidence_tags": tags, "edge_tags": edge, "lifecycle_tags": lifecycle}
}

func testEvidence(name, body string) ([]string, []string, []string) {
	hay := strings.ToLower(name + "\n" + body)
	edgeSet, lifeSet := map[string]bool{}, map[string]bool{}
	for tag, patterns := range edgePatterns {
		for _, p := range patterns {
			if strings.Contains(hay, p) {
				edgeSet[tag] = true
				break
			}
		}
	}
	for tag, patterns := range lifecyclePatterns {
		for _, p := range patterns {
			if strings.Contains(hay, p) {
				lifeSet[tag] = true
				break
			}
		}
	}
	tagSet := map[string]bool{}
	for k := range edgeSet {
		tagSet[k] = true
	}
	for k := range lifeSet {
		tagSet[k] = true
	}
	if len(edgeSet) > 0 {
		tagSet["edge"] = true
	}
	if len(lifeSet) > 0 {
		tagSet["lifecycle"] = true
	}
	return sortedKeys(tagSet), sortedKeys(edgeSet), sortedKeys(lifeSet)
}

func goExplicitTestMappings(text, rel string) []M {
	var out []M
	var pending []string
	for _, line := range strings.Split(text, "\n") {
		if m := goPortingRE.FindStringSubmatch(line); m != nil {
			pending = append(pending, m[1])
			continue
		}
		if m := goTestRE.FindStringSubmatch(line); m != nil {
			for _, rust := range pending {
				out = append(out, M{"file": rel, "source_test": rust, "target_test": m[1]})
			}
			pending = nil
			continue
		}
		trim := strings.TrimSpace(line)
		if trim != "" && !strings.HasPrefix(strings.TrimLeft(line, " \t"), "//") {
			pending = nil
		}
	}
	for _, loc := range goTestRE.FindAllStringSubmatchIndex(text, -1) {
		testName := text[loc[2]:loc[3]]
		body := functionBodyAfter(text, loc[1])
		for _, m := range goSubtestRE.FindAllStringSubmatch(body, -1) {
			out = append(out, M{"file": rel, "source_test": m[1], "target_test": testName, "method": "subtest-name"})
		}
	}
	return out
}

func RustTestGoName(name string) string {
	parts := regexp.MustCompile(`[^A-Za-z0-9]+`).Split(name, -1)
	var b strings.Builder
	b.WriteString("Test")
	for _, p := range parts {
		if p == "" {
			continue
		}
		b.WriteString(strings.ToUpper(p[:1]))
		if len(p) > 1 {
			b.WriteString(p[1:])
		}
	}
	return b.String()
}

func TestTokens(name string) map[string]bool {
	raw := []string{}
	for _, part := range regexp.MustCompile(`[^A-Za-z0-9]+`).Split(name, -1) {
		for _, tok := range camelTokens(part) {
			raw = append(raw, strings.ToLower(tok))
		}
	}
	tokens := map[string]bool{}
	skipOut := false
	for _, tok := range raw {
		if stopTokens[tok] {
			continue
		}
		if tok == "non" {
			tokens["nonpublic"] = true
			continue
		}
		if tok == "public" {
			if !tokens["nonpublic"] {
				tokens["public"] = true
			}
			continue
		}
		if tok == "time" {
			skipOut = true
			tokens["timeout"] = true
			continue
		}
		if skipOut && tok == "out" {
			skipOut = false
			continue
		}
		if v := tokenSynonyms[tok]; v != "" {
			tok = v
		}
		if tok != "" && !stopTokens[tok] {
			tokens[tok] = true
		}
	}
	return tokens
}

func TokenSimilarity(left, right map[string]bool) float64 {
	if len(left) == 0 || len(right) == 0 {
		return 0
	}
	over := 0
	for k := range left {
		if right[k] {
			over++
		}
	}
	precision := float64(over) / float64(len(right))
	recall := float64(over) / float64(len(left))
	if precision+recall == 0 {
		return 0
	}
	return 2 * precision * recall / (precision + recall)
}

func TestMappingInventory(sourceTests, targetTests, explicit, excluded []M) M {
	excl := map[string]bool{}
	for _, row := range excluded {
		if s, _ := row["name"].(string); s != "" {
			excl[s] = true
		}
	}
	sourceBy, targetBy := map[string]M{}, map[string]M{}
	for _, item := range sourceTests {
		name := str(item["name"])
		if !excl[name] {
			sourceBy[name] = item
		}
	}
	for _, item := range targetTests {
		targetBy[str(item["name"])] = item
	}
	var mappings []M
	used := map[string]bool{}
	for _, row := range explicit {
		src, tgt := str(row["source_test"]), str(row["target_test"])
		if excl[src] {
			continue
		}
		status, conf := "invalid", 0.0
		if sourceBy[src] != nil && targetBy[tgt] != nil {
			status, conf, used[src] = "matched", 1.0, true
		}
		mappings = append(mappings, M{"source_test": src, "target_test": tgt, "method": defaultStr(row["method"], "explicit"), "confidence": conf, "status": status, "source_edge_tags": sourceBy[src]["edge_tags"], "target_edge_tags": targetBy[tgt]["edge_tags"], "source_lifecycle_tags": sourceBy[src]["lifecycle_tags"], "target_lifecycle_tags": targetBy[tgt]["lifecycle_tags"]})
	}
	for _, source := range sourceTests {
		src := str(source["name"])
		if excl[src] || used[src] {
			continue
		}
		tgt := RustTestGoName(src)
		if targetBy[tgt] == nil {
			continue
		}
		used[src] = true
		mappings = append(mappings, M{"source_test": src, "target_test": tgt, "method": "rust-name-pascal", "confidence": 1.0, "status": "matched", "source_edge_tags": source["edge_tags"], "target_edge_tags": targetBy[tgt]["edge_tags"], "source_lifecycle_tags": source["lifecycle_tags"], "target_lifecycle_tags": targetBy[tgt]["lifecycle_tags"]})
	}
	targetTokens := map[string]map[string]bool{}
	for _, t := range targetTests {
		targetTokens[str(t["name"])] = TestTokens(str(t["name"]))
	}
	for _, source := range sourceTests {
		src := str(source["name"])
		if excl[src] || used[src] {
			continue
		}
		bestName, bestScore := "", 0.0
		srcTok := TestTokens(src)
		for tgt, toks := range targetTokens {
			score := TokenSimilarity(srcTok, toks)
			if score > bestScore {
				bestName, bestScore = tgt, score
			}
		}
		if bestName != "" && bestScore >= 0.55 {
			status := "weak"
			if bestScore >= 0.72 {
				status = "matched"
			}
			used[src] = true
			mappings = append(mappings, M{"source_test": src, "target_test": bestName, "method": "name-similarity", "confidence": round3(bestScore), "status": status, "source_edge_tags": source["edge_tags"], "target_edge_tags": targetBy[bestName]["edge_tags"], "source_lifecycle_tags": source["lifecycle_tags"], "target_lifecycle_tags": targetBy[bestName]["lifecycle_tags"]})
		}
	}
	var unmatched []M
	for _, item := range sourceTests {
		name := str(item["name"])
		if !used[name] && !excl[name] {
			unmatched = append(unmatched, M{"file": item["file"], "name": name})
		}
	}
	return M{"mappings": mappings, "matched_source_count": len(used), "source_count": len(sourceBy), "target_count": len(targetTests), "unmatched_source_tests": unmatched, "excluded_source_tests": excluded}
}

func goListImports(target string) []string {
	cmd := exec.Command("go", "list", "-f", `{{join .Imports "\n"}}`)
	cmd.Dir = target
	out, err := cmd.Output()
	if err != nil {
		return []string{}
	}
	lines := strings.FieldsFunc(string(out), func(r rune) bool { return r == '\n' || r == '\r' })
	sort.Strings(lines)
	return lines
}

func Inventory(source, target, repo, registryPath string) (M, error) {
	reg := MergeRegistry(defaultAndexRegistry(repo), loadDependencyRegistry(registryPath))
	sourceRust := RustItems(source)
	targetGo := GoItems(target)
	packageRel := ""
	if rel, err := filepath.Rel(repo, target); err == nil {
		packageRel = filepath.ToSlash(rel)
	}
	excluded := selectedExcludedTests(reg, packageRel)
	sourceTests := toMaps(sourceRust["tests"])
	targetTests := toMaps(targetGo["tests"])
	explicit := toMaps(targetGo["explicit_test_mappings"])
	return M{
		"source":                         M{"root": source, "files": relFiles(source), "rust": sourceRust},
		"target":                         M{"root": target, "files": relFiles(target), "go": targetGo, "dependency_grade": dependencyGrade(repo, packageRel)},
		"dependency_map":                 sourceDependencyMap(sourceRust["dependencies"].(M), toStrings(targetGo["imports"])),
		"deterministic_dependency_audit": deterministicDependencyAudit(sourceRust["dependencies"].(M), toStrings(targetGo["imports"]), packageRel, repo, reg),
		"test_mapping":                   TestMappingInventory(sourceTests, targetTests, explicit, excluded),
		"registry":                       M{"api_mappings": selectedAPIMappings(reg, packageRel), "excluded_tests": excluded},
		"notes":                          []string{"Regex-based extraction is evidence inventory, not semantic proof.", "deterministic_dependency_audit is registry-driven; unknown mapping means the registry must be extended before making a dependency-boundary claim.", "test_mapping prefers explicit // porting: rust-test=<name> comments and falls back to normalized test-name similarity.", "Review local_helper_candidates for possible copied dependency responsibilities after deterministic dependency findings."},
	}, nil
}

func modulePath(repo string) string {
	for _, line := range strings.Split(readText(filepath.Join(repo, "go.mod")), "\n") {
		f := strings.Fields(line)
		if len(f) >= 2 && f[0] == "module" {
			return f[1]
		}
	}
	return ""
}

func loadDependencyRegistry(path string) M {
	if path == "" {
		return M{}
	}
	reg, err := ReadJSON(path)
	if err != nil {
		return M{}
	}
	return reg
}

func defaultAndexRegistry(repo string) M {
	mod := modulePath(repo)
	if mod == "" {
		mod = "andex-go2"
	}
	rustToGo := M{
		"andex-utils-absolute-path": mod + "/utils/absolute-path",
		"codex-utils-absolute-path": mod + "/utils/absolute-path",
		"andex-utils-cache":         mod + "/utils/cache",
		"codex-utils-cache":         mod + "/utils/cache",
		"andex-utils-elapsed":       mod + "/utils/elapsed",
		"codex-utils-elapsed":       mod + "/utils/elapsed",
		"andex-utils-home-dir":      mod + "/utils/home-dir",
		"codex-utils-home-dir":      mod + "/utils/home-dir",
		"andex-utils-image":         mod + "/utils/image",
		"codex-utils-image":         mod + "/utils/image",
		"andex-utils-path-utils":    mod + "/utils/path-utils",
		"codex-utils-path-utils":    mod + "/utils/path-utils",
		"andex-utils-pty":           mod + "/utils/pty",
		"codex-utils-pty":           mod + "/utils/pty",
		"andex-utils-readiness":     mod + "/utils/readiness",
		"codex-utils-readiness":     mod + "/utils/readiness",
		"andex-utils-stream-parser": mod + "/utils/stream-parser",
		"codex-utils-stream-parser": mod + "/utils/stream-parser",
		"andex-utils-string":        mod + "/utils/string",
		"codex-utils-string":        mod + "/utils/string",
		"andex-utils-template":      mod + "/utils/template",
		"codex-utils-template":      mod + "/utils/template",
		"andex-protocol":            mod + "/protocol",
		"codex-protocol":            mod + "/protocol",
		"andex-execpolicy":          mod + "/execpolicy",
		"codex-execpolicy":          mod + "/execpolicy",
		"andex-file-watcher":        mod + "/file-watcher",
		"codex-file-watcher":        mod + "/file-watcher",
		"andex-stdio-to-uds":        mod + "/stdio-to-uds",
		"codex-stdio-to-uds":        mod + "/stdio-to-uds",
		"andex-uds":                 mod + "/uds",
		"codex-uds":                 mod + "/uds",
	}
	return M{"rust_to_go": rustToGo, "standard_replacements": standardReplacements, "external_replacements": M{}, "allowed_local_reimplementations": M{}}
}

func MergeRegistry(base, override M) M {
	out := M{}
	for k, v := range base {
		out[k] = v
	}
	for k, v := range override {
		if bm, ok := out[k].(M); ok {
			if om, ok := v.(map[string]any); ok {
				n := M{}
				for kk, vv := range bm {
					n[kk] = vv
				}
				for kk, vv := range om {
					n[kk] = vv
				}
				out[k] = n
				continue
			}
		}
		out[k] = v
	}
	return out
}

func selectedAPIMappings(reg M, packageRel string) M {
	if by, ok := reg["api_mappings_by_package"].(map[string]any); ok && packageRel != "" {
		if scoped, ok := by[packageRel].(map[string]any); ok && len(scoped) > 0 {
			return M(scoped)
		}
	}
	if gm, ok := reg["api_mappings"].(map[string]any); ok {
		return M(gm)
	}
	return M{}
}

func selectedExcludedTests(reg M, packageRel string) []M {
	by, ok := reg["excluded_tests_by_package"].(map[string]any)
	if !ok || packageRel == "" {
		return nil
	}
	rows, ok := by[packageRel].([]any)
	if !ok {
		return nil
	}
	var out []M
	for _, raw := range rows {
		row, ok := raw.(map[string]any)
		if ok && str(row["name"]) != "" {
			out = append(out, M{"file": str(row["file"]), "name": str(row["name"]), "reason": str(row["reason"])})
		}
	}
	return out
}

func dependencyGrade(repo, pkg string) M {
	text := readText(filepath.Join(repo, "docs", "dependency-grade.md"))
	if pkg == "" || text == "" {
		return M{}
	}
	current := ""
	for _, line := range strings.Split(text, "\n") {
		if strings.HasPrefix(line, "## ") {
			current = strings.TrimSpace(strings.TrimPrefix(line, "## "))
		} else if current != "" && strings.Contains(line, "`"+pkg+"`") {
			return M{"grade": current, "line": strings.TrimSpace(line)}
		}
	}
	return M{}
}

func dependencyGrades(repo string) map[string]int {
	out := map[string]int{}
	text := readText(filepath.Join(repo, "docs", "dependency-grade.md"))
	current := -1
	for _, line := range strings.Split(text, "\n") {
		if strings.HasPrefix(line, "## ") {
			num := regexp.MustCompile(`\d+`).FindString(line)
			current = -1
			if num != "" {
				current, _ = strconv.Atoi(num)
			}
			continue
		}
		if current < 0 || !strings.HasPrefix(line, "- ") {
			continue
		}
		if m := regexp.MustCompile("`([^`]+)`").FindStringSubmatch(line); m != nil {
			out[m[1]] = current
		}
	}
	return out
}

func sourceDependencyMap(sourceDeps M, targetImports []string) []M {
	var rows []M
	for section, raw := range sourceDeps {
		for _, dep := range toStrings(raw) {
			matched := ""
			depC := dependencyNameCandidates(dep)
			for _, imp := range targetImports {
				if intersects(depC, importNameCandidates(imp)) {
					matched = imp
					break
				}
			}
			handling := "unmatched"
			if matched != "" {
				handling = "candidate import"
			}
			rows = append(rows, M{"source_section": section, "source_dependency": dep, "target_import_guess": matched, "handling": handling})
		}
	}
	return rows
}

func deterministicDependencyAudit(sourceDeps M, targetImports []string, packageRel, repo string, registry M) []M {
	var rows []M
	rustToGo := asMap(registry["rust_to_go"])
	standard := asMap(registry["standard_replacements"])
	external := asMap(registry["external_replacements"])
	allowed := asMap(registry["allowed_local_reimplementations"])
	gradeMap := dependencyGrades(repo)
	packageGrade, hasPackageGrade := gradeMap[packageRel]
	mod := modulePath(repo)
	importSet := map[string]bool{}
	for _, imp := range targetImports {
		importSet[imp] = true
	}
	for section, raw := range sourceDeps {
		for _, dep := range toStrings(raw) {
			expected := str(rustToGo[dep])
			handling := "unknown mapping"
			ev := M{"source_section": section}
			if expected != "" {
				if importSet[expected] {
					handling = "correct import"
					ev["target_import"] = expected
				} else if containsString(toStrings(allowed[packageRel]), dep) {
					handling = "allowed local reimplementation"
					ev["allowlist"] = true
				} else {
					handling = "missing dependency"
					ev["expected_target_import"] = expected
				}
				if handling == "correct import" && hasPackageGrade {
					if eg, ok := gradeMap[importToRepoRel(expected, mod)]; ok && eg > packageGrade {
						handling = "upward dependency violation"
						ev["package_grade"], ev["dependency_grade"] = packageGrade, eg
					}
				}
			} else if standard[dep] != nil {
				handling = "standard-library replacement allowed"
				ev["replacement"] = standard[dep]
			} else if external[dep] != nil {
				handling = "external replacement allowed"
				ev["replacement"] = external[dep]
			}
			rows = append(rows, M{"source_dependency": dep, "expected_target_import": expected, "handling": handling, "evidence": ev})
		}
	}
	for _, imp := range targetImports {
		if !hasPackageGrade {
			continue
		}
		if ig, ok := gradeMap[importToRepoRel(imp, mod)]; ok && ig > packageGrade {
			rows = append(rows, M{"source_dependency": "", "expected_target_import": imp, "handling": "upward dependency violation", "evidence": M{"package": packageRel, "package_grade": packageGrade, "target_import": imp, "dependency_grade": ig}})
		}
	}
	return rows
}

func importToRepoRel(imp, mod string) string {
	if mod != "" && strings.HasPrefix(imp, mod+"/") {
		return strings.TrimPrefix(imp, mod+"/")
	}
	return imp
}

func compactName(v string) string {
	var b strings.Builder
	for _, r := range strings.ToLower(v) {
		if r >= 'a' && r <= 'z' || r >= '0' && r <= '9' {
			b.WriteRune(r)
		}
	}
	return b.String()
}

func dependencyNameCandidates(dep string) map[string]bool {
	out := map[string]bool{compactName(dep): true}
	if strings.HasPrefix(dep, "andex-") {
		stripped := strings.TrimPrefix(dep, "andex-")
		out[compactName(stripped)] = true
		if strings.HasPrefix(stripped, "utils-") {
			out[compactName("utils/"+strings.TrimPrefix(stripped, "utils-"))] = true
		}
	}
	return out
}

func importNameCandidates(imp string) map[string]bool {
	parts := strings.Split(imp, "/")
	out := map[string]bool{compactName(imp): true, compactName(parts[len(parts)-1]): true}
	if len(parts) >= 2 {
		out[compactName(strings.Join(parts[len(parts)-2:], "/"))] = true
	}
	return out
}

func SuggestMappings(source, target string, includeUnmatched bool) M {
	rustPublic := toMaps(RustItems(source)["public_items"])
	goPublic := toMaps(GoItems(target)["public_items"])
	nameSet := map[string]bool{}
	var goNames []string
	for _, item := range goPublic {
		name := str(item["name"])
		if name != "" && !nameSet[name] {
			nameSet[name] = true
			goNames = append(goNames, name)
		}
	}
	sort.Strings(goNames)
	out := M{}
	for _, item := range rustPublic {
		src := str(item["name"])
		if src == "" || out[src] != nil {
			continue
		}
		cand := bestCandidate(src, goNames)
		if cand == nil {
			if !includeUnmatched {
				continue
			}
			cand = M{"target": "", "status": "partial", "confidence": 0.0, "method": "unmatched"}
		}
		out[src] = M{"target": cand["target"], "status": cand["status"], "source": fmt.Sprintf("%s:%s", str(item["file"]), str(item["kind"])), "confidence": cand["confidence"], "method": cand["method"]}
	}
	return out
}

func RustExportName(name string) string {
	parts := regexp.MustCompile(`[^A-Za-z0-9]+`).Split(name, -1)
	var b strings.Builder
	for _, p := range parts {
		if p == "" {
			continue
		}
		b.WriteString(strings.ToUpper(p[:1]) + p[1:])
	}
	if b.Len() == 0 {
		return name
	}
	return b.String()
}

func apiTokens(name string) map[string]bool {
	out := map[string]bool{}
	for _, part := range regexp.MustCompile(`[^A-Za-z0-9]+`).Split(name, -1) {
		for _, t := range camelTokens(part) {
			out[strings.ToLower(t)] = true
		}
	}
	return out
}

func bestCandidate(source string, goNames []string) M {
	pascal := RustExportName(source)
	upper := strings.ToUpper(source)
	for _, n := range goNames {
		if n == source {
			return M{"target": source, "status": "mapped", "confidence": 1.0, "method": "exact"}
		}
		if n == pascal {
			return M{"target": pascal, "status": "mapped", "confidence": 1.0, "method": "snake-to-pascal"}
		}
		if n == upper {
			return M{"target": upper, "status": "mapped", "confidence": 1.0, "method": "upper-constant"}
		}
	}
	best, score := "", 0.0
	srcTok := apiTokens(source)
	for _, n := range goNames {
		if s := TokenSimilarity(srcTok, apiTokens(n)); s > score {
			best, score = n, s
		}
	}
	if best == "" || score < 0.55 {
		return nil
	}
	status := "partial"
	if score >= 0.88 {
		status = "mapped"
	}
	return M{"target": best, "status": status, "confidence": round3(score), "method": "token-similarity"}
}

func ScoreInventory(inv M, verification M) M {
	source := asMap(inv["source"])
	target := asMap(inv["target"])
	rust := asMap(source["rust"])
	goInv := asMap(target["go"])
	rustPublic, goPublic := toMaps(rust["public_items"]), toMaps(goInv["public_items"])
	rustTests, goTests := toMaps(rust["tests"]), toMaps(goInv["tests"])
	depRows := toMaps(inv["deterministic_dependency_audit"])
	helpers := toMaps(goInv["local_helper_candidates"])
	testMap := asMap(inv["test_mapping"])
	mappings := toMaps(testMap["mappings"])
	findings := []M{}

	apiRatio := math.Min(1, float64(len(goPublic))/float64(max(1, len(rustPublic))))
	apiEvidence := []string{fmt.Sprintf("source public items: %d", len(rustPublic)), fmt.Sprintf("target public items: %d", len(goPublic))}
	apiGaps := []string{}
	if apiMap := apiMappingScore(inv, rustPublic); apiMap != nil {
		apiRatio = apiMap["ratio"].(float64)
		apiEvidence = []string{fmt.Sprintf("mapped API items: %.1f/%d", apiMap["mapped"].(float64), apiMap["total"].(int)), fmt.Sprintf("mapping statuses: %v", apiMap["statuses"])}
	}
	if apiRatio < 0.85 {
		apiGaps = append(apiGaps, fmt.Sprintf("Target exports %d items for %d source public items", len(goPublic), len(rustPublic)))
	}
	api := category(int(math.Round(15*apiRatio)), 15, "Compares extracted source public items against target exported API count; manual review required for exact mapping.", apiEvidence, apiGaps)

	matched := intNum(testMap["matched_source_count"])
	sourceCount := intNum(testMap["source_count"])
	testRatio := math.Min(1, float64(matched)/float64(max(1, sourceCount)))
	testGaps := []string{}
	if sourceCount == 0 {
		testRatio = math.Min(1, float64(len(goTests))/float64(max(1, len(rustTests))))
	}
	if testRatio < 1 {
		testGaps = append(testGaps, "Source tests remain unmatched in test_mapping")
	}
	tests := category(int(math.Round(12*testRatio)), 12, "Scores source tests matched to target tests using explicit porting comments first, then normalized test-name similarity.", []string{fmt.Sprintf("source tests: %d", len(rustTests)), fmt.Sprintf("target tests: %d", len(goTests)), fmt.Sprintf("matched source tests: %d/%d", matched, sourceCount)}, testGaps)

	var correct, missing, upward, unknown, allowed []M
	for _, row := range depRows {
		switch str(row["handling"]) {
		case "correct import":
			correct = append(correct, row)
		case "missing dependency":
			missing = append(missing, row)
		case "upward dependency violation":
			upward = append(upward, row)
		case "unknown mapping":
			unknown = append(unknown, row)
		}
		if strings.HasSuffix(str(row["handling"]), "allowed") || str(row["handling"]) == "allowed local reimplementation" {
			allowed = append(allowed, row)
		}
	}
	depScore := 13 - min(8, len(missing)*3+len(upward)*5) - min(4, len(unknown))
	depGaps := []string{}
	if len(missing) > 0 {
		depGaps = append(depGaps, "Registered Rust dependencies are missing expected target imports")
	}
	if len(upward) > 0 {
		depGaps = append(depGaps, "Target imports higher-stage package according to dependency-grade parsing")
	}
	if len(unknown) > 0 {
		depGaps = append(depGaps, "Registry has unknown dependency mappings; manual review required")
	}
	dep := category(depScore, 13, "Uses deterministic_dependency_audit from registry, Go imports, and dependency-grade evidence.", []string{fmt.Sprintf("correct imports: %d", len(correct)), fmt.Sprintf("allowed replacements: %d", len(allowed))}, depGaps)

	coreMetrics := coreMappingMetrics(mappings, firstNonZero(sourceCount, len(rustTests)))
	coreDep := coreDependencyRatio(missing, upward, unknown)
	coreParts := M{"mapped_source_tests": int(math.Round(10 * coreMetrics["coverage_ratio"].(float64))), "mapping_quality": int(math.Round(5 * coreMetrics["quality_ratio"].(float64))), "public_api": int(math.Round(4 * apiRatio)), "dependency_cleanliness": int(math.Round(3 * coreDep)), "evidence_diversity": int(math.Round(3 * coreMetrics["diversity_ratio"].(float64)))}
	coreScore := intNum(coreParts["mapped_source_tests"]) + intNum(coreParts["mapping_quality"]) + intNum(coreParts["public_api"]) + intNum(coreParts["dependency_cleanliness"]) + intNum(coreParts["evidence_diversity"])
	coreGaps := []string{}
	if coreMetrics["coverage_ratio"].(float64) < 0.9 {
		coreGaps = append(coreGaps, fmt.Sprintf("Mapped source-test coverage is %.1f/%d after weak-match weighting", coreMetrics["weighted_coverage"].(float64), intNum(coreMetrics["source_count"])))
	}
	if coreMetrics["quality_ratio"].(float64) < 0.9 {
		coreGaps = append(coreGaps, fmt.Sprintf("High-confidence/explicit mapping quality is %d/%d source tests", intNum(coreMetrics["high_confidence_count"]), intNum(coreMetrics["source_count"])))
	}
	if coreMetrics["diversity_ratio"].(float64) < 0.9 {
		coreGaps = append(coreGaps, fmt.Sprintf("Behavior evidence diversity is %.1f/%d tagged source mappings", coreMetrics["diversity_covered"].(float64), intNum(coreMetrics["diversity_relevant"])))
	}
	if len(coreGaps) == 0 {
		coreGaps = append(coreGaps, "Manual review must still confirm semantic equivalence beyond mapped evidence")
	}
	core := category(coreScore, 25, "Behavior-slice score from mapped source-test coverage (10), high-confidence/explicit mapping quality (5), public API ratio (4), dependency cleanliness (3), and edge/lifecycle evidence diversity (3).", []string{fmt.Sprintf("core subscores: mapped_source_tests=%d/10, mapping_quality=%d/5, public_api=%d/4, dependency_cleanliness=%d/3, evidence_diversity=%d/3", intNum(coreParts["mapped_source_tests"]), intNum(coreParts["mapping_quality"]), intNum(coreParts["public_api"]), intNum(coreParts["dependency_cleanliness"]), intNum(coreParts["evidence_diversity"])), fmt.Sprintf("mapping coverage: %.1f/%d weighted source tests; valid mappings=%d, explicit=%d, high-confidence=%d", coreMetrics["weighted_coverage"].(float64), intNum(coreMetrics["source_count"]), intNum(coreMetrics["valid_count"]), intNum(coreMetrics["explicit_count"]), intNum(coreMetrics["high_confidence_count"])), fmt.Sprintf("dependency boundary blockers: missing=%d, upward=%d, unknown=%d", len(missing), len(upward), len(unknown)), fmt.Sprintf("tag diversity coverage: %.1f/%d", coreMetrics["diversity_covered"].(float64), intNum(coreMetrics["diversity_relevant"]))}, coreGaps)

	edgeCov := evidenceCoverage(mappings, "source_edge_tags", "target_edge_tags")
	edgeScore := 3
	if intNum(edgeCov["relevant"]) > 0 {
		edgeScore = int(math.Round(15 * edgeCov["ratio"].(float64)))
	} else if len(goTests) > 0 {
		edgeScore = 9
	}
	edge := category(edgeScore, 15, "Scores mapped source edge/error tests whose target tests contain corresponding assertion or failure-mode evidence tags.", []string{fmt.Sprintf("edge evidence coverage: %d/%d", intNum(edgeCov["covered"]), intNum(edgeCov["relevant"])), "source edge tags: " + joinAny(edgeCov["source_tags"]), "target edge tags: " + joinAny(edgeCov["target_tags"])}, conditionalGap(edgeCov["ratio"].(float64) < 0.9, "Source edge/error tests lack matched target edge evidence"))
	lifeCov := evidenceCoverage(mappings, "source_lifecycle_tags", "target_lifecycle_tags")
	lifeScore := 4
	if intNum(lifeCov["relevant"]) > 0 {
		lifeScore = int(math.Round(12 * lifeCov["ratio"].(float64)))
	} else if len(goTests) > 0 {
		lifeScore = 8
	}
	life := category(lifeScore, 12, "Scores mapped source lifecycle/platform tests whose target tests contain corresponding run/shutdown/concurrency/resource/platform evidence tags.", []string{fmt.Sprintf("lifecycle evidence coverage: %d/%d", intNum(lifeCov["covered"]), intNum(lifeCov["relevant"])), "source lifecycle tags: " + joinAny(lifeCov["source_tags"]), "target lifecycle tags: " + joinAny(lifeCov["target_tags"]), fmt.Sprintf("local helper candidates: %d", len(helpers))}, conditionalGap(lifeCov["ratio"].(float64) < 0.9, "Source lifecycle/platform tests lack matched target lifecycle evidence"))
	integration := category(intNum(verificationScore(verification)["score"]), 8, "Scores supplied verification evidence for focused tests, full tests, porting-rule checks, and lint.", toStrings(verificationScore(verification)["evidence"]), toStrings(verificationScore(verification)["gaps"]))

	if len(missing) > 0 {
		findings = append(findings, M{"severity": "P1", "title": "Missing registered target dependency", "evidence": joinDeps(missing, "source_dependency"), "fix": "Import the expected ported package or add a narrow registry exception with evidence."})
	}
	if len(upward) > 0 {
		findings = append(findings, M{"severity": "P1", "title": "Upward dependency violation", "evidence": joinDeps(upward, "expected_target_import"), "fix": "Move behavior downward or depend only on allowed lower-stage packages."})
	}
	if len(unknown) > 0 {
		findings = append(findings, M{"severity": "P2", "title": "Unknown dependency mapping", "evidence": joinDeps(unknown, "source_dependency"), "fix": "Extend the dependency registry before claiming dependency-boundary parity."})
	}
	cats := M{"api_surface_parity": api, "core_behavior_parity": core, "edge_cases_error_semantics": edge, "lifecycle_concurrency_platform": life, "dependency_responsibility_boundary": dep, "test_coverage": tests, "integration_build_quality": integration}
	score := 0
	for _, v := range cats {
		score += intNum(asMap(v)["score"])
	}
	grade := "effectively unported"
	if score >= 90 {
		grade = "near complete"
	} else if score >= 75 {
		grade = "substantially ported"
	} else if score >= 50 {
		grade = "usable partial port"
	} else if score >= 25 {
		grade = "skeleton or narrow slice"
	}
	return M{"schema_version": "1.0", "generated_at": time.Now().UTC().Format(time.RFC3339), "source": str(source["root"]), "target": str(target["root"]), "score": score, "grade": grade, "mode": "heuristic baseline; manual-review gap remains for semantic parity", "categories": cats, "findings": findings, "risks": risks(findings), "extraction_gaps": extractionGaps(cats), "actions": makeActions(cats, findings), "verification": verification, "inventory": inv}
}

func apiMappingScore(inv M, rustPublic []M) M {
	reg := asMap(inv["registry"])
	mappings := asMap(reg["api_mappings"])
	if len(mappings) == 0 {
		return nil
	}
	mapped := 0.0
	statuses := map[string]int{}
	total := max(1, len(rustPublic))
	for _, item := range rustPublic {
		row := mappings[str(item["name"])]
		if s, ok := row.(string); ok {
			row = M{"target": s, "status": "mapped"}
		}
		rm := asMap(row)
		if len(rm) == 0 {
			continue
		}
		status := defaultStr(rm["status"], "mapped")
		statuses[status]++
		if status == "mapped" || status == "merged" || status == "internal_equivalent" || status == "not_applicable" {
			mapped++
		} else if status == "partial" {
			mapped += 0.5
		}
	}
	return M{"ratio": math.Min(1, mapped/float64(total)), "mapped": mapped, "total": total, "statuses": statuses}
}

func category(score, maxScore int, rationale string, evidence, gaps []string) M {
	return M{"score": max(0, min(score, maxScore)), "max": maxScore, "rationale": rationale, "evidence": evidence, "gaps": gaps}
}

func evidenceCoverage(mappings []M, sourceKey, targetKey string) M {
	relevant, covered := 0, 0
	sourceTags, targetTags := map[string]bool{}, map[string]bool{}
	for _, row := range mappings {
		if str(row["status"]) != "matched" && str(row["status"]) != "weak" {
			continue
		}
		src := toStrings(row[sourceKey])
		if len(src) == 0 {
			continue
		}
		relevant++
		tgt := toStrings(row[targetKey])
		if stringIntersection(src, tgt) {
			covered++
			for _, t := range tgt {
				targetTags[t] = true
			}
		}
		for _, t := range src {
			sourceTags[t] = true
		}
	}
	ratio := 0.0
	if relevant > 0 {
		ratio = float64(covered) / float64(relevant)
	}
	return M{"relevant": relevant, "covered": covered, "ratio": ratio, "source_tags": sortedKeys(sourceTags), "target_tags": sortedKeys(targetTags)}
}

func mappingWeight(row M) float64 {
	if str(row["status"]) == "matched" {
		return 1
	}
	if str(row["status"]) == "weak" {
		return 0.7
	}
	return 0
}

func coreMappingMetrics(mappings []M, sourceCount int) M {
	den := max(1, sourceCount)
	valid, explicit, high := 0, 0, 0
	weighted, quality := 0.0, 0.0
	divRel, divCov := 0, 0.0
	for _, row := range mappings {
		if str(row["status"]) != "matched" && str(row["status"]) != "weak" {
			continue
		}
		valid++
		w := mappingWeight(row)
		weighted += w
		conf := floatNum(row["confidence"])
		if str(row["method"]) == "explicit" {
			explicit++
			high++
			quality += 1
		} else if conf >= 0.9 {
			high++
			quality += 1
		} else if str(row["status"]) == "matched" {
			quality += 0.8
		} else {
			quality += 0.5
		}
		srcE, srcL := toStrings(row["source_edge_tags"]), toStrings(row["source_lifecycle_tags"])
		if len(srcE) == 0 && len(srcL) == 0 {
			continue
		}
		divRel++
		edgeOK := len(srcE) == 0 || stringIntersection(srcE, toStrings(row["target_edge_tags"]))
		lifeOK := len(srcL) == 0 || stringIntersection(srcL, toStrings(row["target_lifecycle_tags"]))
		if edgeOK && lifeOK {
			divCov += w
		}
	}
	divRatio := 1.0
	if divRel > 0 {
		divRatio = math.Min(1, divCov/float64(divRel))
	}
	return M{"source_count": sourceCount, "valid_count": valid, "explicit_count": explicit, "high_confidence_count": high, "weighted_coverage": weighted, "coverage_ratio": math.Min(1, weighted/float64(den)), "quality_ratio": math.Min(1, quality/float64(den)), "diversity_relevant": divRel, "diversity_covered": divCov, "diversity_ratio": divRatio}
}

func coreDependencyRatio(missing, upward, unknown []M) float64 {
	penalty := float64(len(missing))*0.35 + float64(len(upward))*0.5 + float64(len(unknown))*0.2
	return math.Max(0, 1-math.Min(1, penalty))
}

func verificationScore(v M) M {
	if len(v) == 0 {
		return M{"score": 5, "evidence": []string{"inventory JSON produced successfully"}, "gaps": []string{"Focused go test, source test, and lint results are not embedded unless supplied externally"}}
	}
	required := map[string]int{"go_test_package": 2, "go_test_all": 2, "porting_rules": 2, "lint": 2}
	score := 0
	var evidence, gaps []string
	for key, pts := range required {
		row := asMap(v[key])
		if strings.ToLower(str(row["status"])) == "pass" {
			score += pts
			evidence = append(evidence, fmt.Sprintf("%s: pass (%s)", key, defaultStr(row["command"], key)))
		} else {
			gaps = append(gaps, key+": missing or not passing")
		}
	}
	if len(evidence) == 0 {
		evidence = []string{"verification JSON supplied"}
	}
	return M{"score": score, "evidence": evidence, "gaps": gaps}
}

var categoryNames = map[string]string{"api_surface_parity": "API surface parity", "core_behavior_parity": "Core behavior parity", "edge_cases_error_semantics": "Edge cases and error semantics", "lifecycle_concurrency_platform": "Lifecycle, concurrency, and platform semantics", "dependency_responsibility_boundary": "Dependency and responsibility boundary fidelity", "test_coverage": "Test coverage ported from source behavior", "integration_build_quality": "Integration/build quality"}

func makeActions(categories M, findings []M) []M {
	var actions []M
	for key, raw := range categories {
		item := asMap(raw)
		gap := intNum(item["max"]) - intNum(item["score"])
		if gap <= 0 {
			continue
		}
		effort := "S"
		if gap > 3 {
			effort = "M"
		}
		impact := "M"
		if key == "dependency_responsibility_boundary" || key == "core_behavior_parity" {
			impact = "H"
		}
		gaps := toStrings(item["gaps"])
		first := "add evidence"
		if len(gaps) > 0 {
			first = gaps[0]
		}
		actions = append(actions, M{"priority": int(math.Round((float64(gap) / float64(max(1, intNum(item["max"])))) * 100)), "effort": effort, "impact": impact, "action": "Improve " + categoryNames[key] + ": " + first})
	}
	for _, finding := range findings {
		if str(finding["severity"]) == "P1" {
			actions = append(actions, M{"priority": 100, "effort": "M", "impact": "H", "action": finding["fix"]})
		}
	}
	sort.Slice(actions, func(i, j int) bool { return intNum(actions[i]["priority"]) > intNum(actions[j]["priority"]) })
	if len(actions) > 8 {
		return actions[:8]
	}
	return actions
}

func Markdown(result M) string {
	var b strings.Builder
	fmt.Fprintf(&b, "**Score**\n%d/100 - %s\n\n**Rubric Breakdown**", intNum(result["score"]), str(result["grade"]))
	for _, key := range []string{"api_surface_parity", "core_behavior_parity", "edge_cases_error_semantics", "lifecycle_concurrency_platform", "dependency_responsibility_boundary", "test_coverage", "integration_build_quality"} {
		item := asMap(asMap(result["categories"])[key])
		fmt.Fprintf(&b, "\n- %s: %d/%d", categoryNames[key], intNum(item["score"]), intNum(item["max"]))
	}
	if findings := toMaps(result["findings"]); len(findings) > 0 {
		b.WriteString("\n\n**Findings**")
		for i, f := range findings {
			if i >= 7 {
				break
			}
			fmt.Fprintf(&b, "\n%d. [%s] %s - %s", i+1, str(f["severity"]), str(f["title"]), str(f["fix"]))
		}
	}
	if actions := toMaps(result["actions"]); len(actions) > 0 {
		b.WriteString("\n\n**Top Actions**")
		for i, a := range actions {
			if i >= 3 {
				break
			}
			fmt.Fprintf(&b, "\n%d. [%s, priority %d] %s", i+1, str(a["effort"]), intNum(a["priority"]), str(a["action"]))
		}
	}
	return b.String()
}

func UpdateAPIMappingsRegistry(source, target, repo, registryPath string, includeUnmatched, replaceExisting bool) (M, error) {
	if registryPath == "" {
		return nil, errors.New("--update-api-mappings requires --dependency-registry")
	}
	reg := loadDependencyRegistry(registryPath)
	rel, err := filepath.Rel(repo, target)
	if err != nil {
		rel = filepath.Base(target)
	}
	rel = filepath.ToSlash(rel)
	by := asMap(reg["api_mappings_by_package"])
	existing := asMap(by[rel])
	suggestions := SuggestMappings(source, target, includeUnmatched)
	merged := M{}
	for k, v := range existing {
		merged[k] = v
	}
	added, replaced, preserved := 0, 0, 0
	for name, row := range suggestions {
		if merged[name] != nil && !replaceExisting {
			preserved++
			continue
		}
		if merged[name] != nil {
			replaced++
		} else {
			added++
		}
		merged[name] = row
	}
	by[rel] = sortedMap(merged)
	reg["api_mappings_by_package"] = sortedMap(by)
	if err := WriteJSON(registryPath, reg); err != nil {
		return nil, err
	}
	return M{"path": registryPath, "package": rel, "suggested": len(suggestions), "added": added, "replaced": replaced, "preserved": preserved, "total": len(merged)}, nil
}

func Render(report M, template string) (string, error) {
	required := []string{"schema_version", "source", "target", "score", "grade", "categories", "findings", "actions"}
	for _, f := range required {
		if report[f] == nil {
			return "", fmt.Errorf("missing required report fields: %s", f)
		}
	}
	repl := map[string]string{"__SOURCE__": esc(report["source"]), "__TARGET__": esc(report["target"]), "__GENERATED_AT__": esc(report["generated_at"]), "__SCORE__": esc(report["score"]), "__GRADE__": esc(report["grade"]), "__CATEGORY_ROWS__": categoryRows(report), "__FINDINGS__": listItems(toMaps(report["findings"]), "No material findings recorded.", false), "__ACTIONS__": listItems(toMaps(report["actions"]), "No ROI actions recorded.", true)}
	out := template
	for k, v := range repl {
		out = strings.ReplaceAll(out, k, v)
	}
	for k := range repl {
		if strings.Contains(out, k) {
			return "", fmt.Errorf("unresolved template tokens: %s", k)
		}
	}
	if strings.Contains(out, "{{") || strings.Contains(out, "}}") {
		return "", errors.New("unresolved placeholder braces remain in rendered HTML")
	}
	return out, nil
}

func categoryRows(report M) string {
	var b strings.Builder
	cats := asMap(report["categories"])
	keys := sortedMapKeys(cats)
	for _, key := range keys {
		item := asMap(cats[key])
		score, maximum := intNum(item["score"]), max(1, intNum(item["max"]))
		pct := max(0, min(100, int(math.Round(float64(score)/float64(maximum)*100))))
		evidence, gaps := toStrings(item["evidence"]), toStrings(item["gaps"])
		ev, gap := "No evidence recorded", "No material gap recorded"
		if len(evidence) > 0 {
			ev = evidence[0]
		}
		if len(gaps) > 0 {
			gap = gaps[0]
		}
		fmt.Fprintf(&b, "<tr><td><strong>%s</strong><span>%s</span></td><td>%d/%d</td><td><div class=\"bar\"><i style=\"width:%d%%\"></i></div></td><td>%s</td><td>%s</td></tr>\n", esc(title(strings.ReplaceAll(key, "_", " "))), esc(item["rationale"]), score, maximum, pct, esc(ev), esc(gap))
	}
	return b.String()
}

func listItems(items []M, empty string, actionMode bool) string {
	if len(items) == 0 {
		return "<li>" + esc(empty) + "</li>"
	}
	var b strings.Builder
	for i, item := range items {
		if i >= 8 {
			break
		}
		if actionMode {
			fmt.Fprintf(&b, "<li><strong>Priority %s · %s/%s</strong><span>%s</span></li>\n", esc(item["priority"]), esc(item["effort"]), esc(item["impact"]), esc(item["action"]))
		} else {
			fmt.Fprintf(&b, "<li><strong>%s: %s</strong><span>%s</span><em>%s</em></li>\n", esc(item["severity"]), esc(item["title"]), esc(item["evidence"]), esc(item["fix"]))
		}
	}
	return b.String()
}

func CollectVerification(target, repo, lintCommand string) M {
	pkg := packageArgForGoCommand(target, repo)
	if lintCommand == "" {
		lintCommand = "golangci-lint run " + pkg
	}
	return M{"go_test_package": runVerification([]string{"go", "test", pkg}, repo), "go_test_all": runVerification([]string{"go", "test", "./..."}, repo), "porting_rules": runVerification([]string{"make", "check-porting-rules"}, repo), "lint": runVerification(strings.Fields(lintCommand), repo)}
}

func packageArgForGoCommand(target, repo string) string {
	if rel, err := filepath.Rel(repo, target); err == nil {
		rel = filepath.ToSlash(rel)
		if rel == "." || rel == "" {
			return "."
		}
		return "./" + rel
	}
	return target
}

func runVerification(command []string, repo string) M {
	cmd := exec.Command(command[0], command[1:]...)
	cmd.Dir = repo
	var out bytes.Buffer
	cmd.Stdout, cmd.Stderr = &out, &out
	err := cmd.Run()
	code := 0
	if err != nil {
		code = 1
		if ee, ok := err.(*exec.ExitError); ok {
			code = ee.ExitCode()
		}
	}
	status := "pass"
	if code != 0 {
		status = "fail"
	}
	summary := out.String()
	if len(summary) > 4000 {
		summary = summary[len(summary)-4000:]
	}
	return M{"status": status, "command": strings.Join(command, " "), "exit_code": code, "summary": strings.TrimSpace(summary)}
}

func risks(findings []M) []M {
	var out []M
	for _, f := range findings {
		out = append(out, M{"severity": f["severity"], "risk": f["title"], "evidence": f["evidence"]})
	}
	return out
}

func extractionGaps(cats M) []string {
	var out []string
	for _, raw := range cats {
		for _, gap := range toStrings(asMap(raw)["gaps"]) {
			l := strings.ToLower(gap)
			if strings.Contains(gap, "Manual review") || strings.Contains(l, "unknown") || strings.Contains(l, "not embedded") {
				out = append(out, gap)
			}
		}
	}
	return out
}

func sortedMap(in M) M { return in }
func sortedMapKeys(m M) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}
func sortedKeys(m map[string]bool) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
func unique(items []M) []M {
	seen := map[string]bool{}
	var out []M
	for _, item := range items {
		b, _ := json.Marshal(item)
		if !seen[string(b)] {
			seen[string(b)] = true
			out = append(out, item)
		}
	}
	return out
}
func asMap(v any) M {
	if v == nil {
		return M{}
	}
	if m, ok := v.(M); ok {
		return m
	}
	if m, ok := v.(map[string]any); ok {
		return M(m)
	}
	return M{}
}
func toMaps(v any) []M {
	switch rows := v.(type) {
	case []M:
		return rows
	case []any:
		out := make([]M, 0, len(rows))
		for _, row := range rows {
			out = append(out, asMap(row))
		}
		return out
	default:
		return nil
	}
}
func toStrings(v any) []string {
	switch rows := v.(type) {
	case []string:
		return rows
	case []any:
		out := make([]string, 0, len(rows))
		for _, row := range rows {
			out = append(out, str(row))
		}
		return out
	case []M:
		return nil
	default:
		return nil
	}
}
func str(v any) string {
	if v == nil {
		return ""
	}
	return fmt.Sprint(v)
}
func defaultStr(v any, d string) string {
	if s := str(v); s != "" {
		return s
	}
	return d
}
func intNum(v any) int {
	switch n := v.(type) {
	case int:
		return n
	case int64:
		return int(n)
	case float64:
		return int(n)
	case json.Number:
		i, _ := n.Int64()
		return int(i)
	default:
		i, _ := strconv.Atoi(str(v))
		return i
	}
}
func floatNum(v any) float64 {
	switch n := v.(type) {
	case float64:
		return n
	case int:
		return float64(n)
	default:
		f, _ := strconv.ParseFloat(str(v), 64)
		return f
	}
}
func round3(f float64) float64 { return math.Round(f*1000) / 1000 }
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
func firstNonZero(a, b int) int {
	if a != 0 {
		return a
	}
	return b
}
func containsString(rows []string, needle string) bool {
	for _, row := range rows {
		if row == needle {
			return true
		}
	}
	return false
}
func intersects(a, b map[string]bool) bool {
	for k := range a {
		if b[k] {
			return true
		}
	}
	return false
}
func stringIntersection(a, b []string) bool {
	set := map[string]bool{}
	for _, x := range a {
		set[x] = true
	}
	for _, x := range b {
		if set[x] {
			return true
		}
	}
	return false
}
func joinAny(v any) string {
	s := toStrings(v)
	if len(s) == 0 {
		return "none"
	}
	if len(s) > 10 {
		s = s[:10]
	}
	return strings.Join(s, ", ")
}
func joinDeps(rows []M, key string) string {
	var out []string
	for i, row := range rows {
		if i >= 5 {
			break
		}
		out = append(out, str(row[key]))
	}
	return strings.Join(out, ", ")
}
func conditionalGap(ok bool, msg string) []string {
	if ok {
		return []string{msg}
	}
	return nil
}
func esc(v any) string { return html.EscapeString(str(v)) }
func title(s string) string {
	upperNext := true
	return strings.Map(func(r rune) rune {
		if unicode.IsSpace(r) {
			upperNext = true
			return r
		}
		if upperNext {
			upperNext = false
			return unicode.ToUpper(r)
		}
		return r
	}, s)
}

func camelTokens(s string) []string {
	if s == "" {
		return nil
	}
	runes := []rune(s)
	var out []string
	start := 0
	for i := 1; i < len(runes); i++ {
		prevKind := runeKind(runes[i-1])
		kind := runeKind(runes[i])
		nextKind := rune(0)
		if i+1 < len(runes) {
			nextKind = runeKind(runes[i+1])
		}
		breakHere := false
		if kind == 'd' && prevKind != 'd' || kind != 'd' && prevKind == 'd' {
			breakHere = true
		} else if kind == 'u' && (prevKind == 'l' || prevKind == 'd') {
			breakHere = true
		} else if kind == 'u' && prevKind == 'u' && nextKind == 'l' {
			breakHere = true
		} else if kind == 'o' || prevKind == 'o' {
			breakHere = true
		}
		if breakHere {
			if start < i {
				out = append(out, string(runes[start:i]))
			}
			start = i
		}
	}
	if start < len(runes) {
		out = append(out, string(runes[start:]))
	}
	return out
}

func runeKind(r rune) rune {
	switch {
	case unicode.IsDigit(r):
		return 'd'
	case unicode.IsUpper(r):
		return 'u'
	case unicode.IsLower(r):
		return 'l'
	default:
		return 'o'
	}
}
