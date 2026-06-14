package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"porting-audit-cartography/audit"
)

func main() {
	source := flag.String("source", "", "Source package root")
	target := flag.String("target", "", "Target package root")
	repo := flag.String("repo", ".", "Target repository root")
	registryPath := flag.String("dependency-registry", "", "Existing registry JSON")
	out := flag.String("out", "", "Write merged registry JSON")
	inPlace := flag.Bool("in-place", false, "Rewrite --dependency-registry in place")
	replace := flag.Bool("replace-existing", false, "Replace existing api_mappings entries")
	include := flag.Bool("include-unmatched", false, "Emit partial review rows for unmapped source APIs")
	flag.Parse()
	if *source == "" || *target == "" {
		fmt.Fprintln(os.Stderr, "--source and --target are required")
		os.Exit(2)
	}
	if *inPlace && *registryPath == "" {
		fmt.Fprintln(os.Stderr, "--in-place requires --dependency-registry")
		os.Exit(2)
	}
	if *inPlace && *out != "" {
		fmt.Fprintln(os.Stderr, "--in-place and --out are mutually exclusive")
		os.Exit(2)
	}
	reg := audit.M{}
	if *registryPath != "" {
		if loaded, err := audit.ReadJSON(abs(*registryPath)); err == nil {
			reg = loaded
		}
	}
	if len(reg) == 0 {
		reg = audit.M{"rust_to_go": audit.M{}, "standard_replacements": audit.M{}, "external_replacements": audit.M{}, "allowed_local_reimplementations": audit.M{}}
	}
	if reg["module"] == nil {
		_ = repo
	}
	apiMappings := audit.M{}
	if existing, ok := reg["api_mappings"].(map[string]any); ok {
		apiMappings = audit.M(existing)
	}
	suggestions := audit.SuggestMappings(abs(*source), abs(*target), *include)
	for name, row := range suggestions {
		if *replace || apiMappings[name] == nil {
			apiMappings[name] = row
		}
	}
	reg["api_mappings"] = apiMappings
	dest := *out
	if *inPlace {
		dest = *registryPath
	}
	if dest == "" {
		audit.WriteJSON("/dev/stdout", reg)
		return
	}
	if err := audit.WriteJSON(abs(dest), reg); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func abs(path string) string {
	if path == "" {
		return ""
	}
	out, err := filepath.Abs(path)
	if err != nil {
		return path
	}
	return out
}
