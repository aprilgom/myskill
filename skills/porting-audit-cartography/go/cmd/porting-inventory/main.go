package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"porting-audit-cartography/audit"
)

func main() {
	source := flag.String("source", "", "Source package root, e.g. Rust crate")
	target := flag.String("target", "", "Target package root, e.g. Go package")
	repo := flag.String("repo", ".", "Target repository root")
	registry := flag.String("dependency-registry", "", "Dependency registry JSON")
	pretty := flag.Bool("pretty", false, "Pretty-print JSON")
	flag.Parse()
	if *source == "" || *target == "" {
		fmt.Fprintln(os.Stderr, "--source and --target are required")
		os.Exit(2)
	}
	payload, err := audit.Inventory(abs(*source), abs(*target), abs(*repo), abs(*registry))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	var b []byte
	if *pretty {
		b, err = json.MarshalIndent(payload, "", "  ")
	} else {
		b, err = json.Marshal(payload)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	os.Stdout.Write(append(b, '\n'))
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
