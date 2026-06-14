package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"porting-audit-cartography/audit"
)

func main() {
	template := flag.String("template", "", "HTML template")
	out := flag.String("out", "", "Output HTML")
	flag.Parse()
	if flag.NArg() != 1 || *template == "" || *out == "" {
		fmt.Fprintln(os.Stderr, "usage: render-dashboard <score-json> --template <template> --out <out>")
		os.Exit(2)
	}
	report, err := audit.ReadJSON(abs(flag.Arg(0)))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	tpl, err := os.ReadFile(abs(*template))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	rendered, err := audit.Render(report, string(tpl))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := os.MkdirAll(filepath.Dir(abs(*out)), 0o755); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := os.WriteFile(abs(*out), []byte(rendered), 0o644); err != nil {
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
