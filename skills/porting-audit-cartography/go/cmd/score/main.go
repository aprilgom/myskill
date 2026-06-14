package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"porting-audit-cartography/audit"
)

func main() {
	inventoryPath := flag.String("inventory", "", "Existing porting_inventory JSON")
	source := flag.String("source", "", "Source package root")
	target := flag.String("target", "", "Target package root")
	repo := flag.String("repo", ".", "Target repository root")
	registry := flag.String("dependency-registry", "", "Dependency registry")
	verificationPath := flag.String("verification", "", "Verification JSON")
	collectVerification := flag.Bool("collect-verification", false, "Run Go tests and lint")
	verificationOut := flag.String("verification-out", "", "Write collected verification JSON")
	lintCommand := flag.String("lint-command", "", "Lint command")
	jsonOut := flag.String("json", "", "Score JSON output")
	markdown := flag.Bool("markdown", false, "Print markdown")
	updateAPI := flag.Bool("update-api-mappings", false, "Update registry api_mappings")
	replaceAPI := flag.Bool("replace-existing-api-mappings", false, "Replace existing api_mappings")
	includeUnmatched := flag.Bool("include-unmatched-api-mappings", false, "Include unmatched API mappings")
	flag.Parse()

	repoAbs := abs(*repo)
	var registryUpdate audit.M
	var err error
	if *updateAPI {
		if *inventoryPath != "" {
			fmt.Fprintln(os.Stderr, "--update-api-mappings cannot be used with --inventory")
			os.Exit(2)
		}
		registryUpdate, err = audit.UpdateAPIMappingsRegistry(abs(*source), abs(*target), repoAbs, abs(*registry), *includeUnmatched, *replaceAPI)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}

	var inv audit.M
	if *inventoryPath != "" {
		inv, err = audit.ReadJSON(abs(*inventoryPath))
	} else if *source != "" && *target != "" {
		inv, err = audit.Inventory(abs(*source), abs(*target), repoAbs, abs(*registry))
	} else {
		fmt.Fprintln(os.Stderr, "--inventory or both --source and --target are required")
		os.Exit(2)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if *verificationPath != "" && *collectVerification {
		fmt.Fprintln(os.Stderr, "--verification and --collect-verification are mutually exclusive")
		os.Exit(2)
	}
	verification := audit.M{}
	if *collectVerification {
		verification = audit.CollectVerification(abs(*target), repoAbs, *lintCommand)
		if *verificationOut != "" {
			if err := audit.WriteJSON(abs(*verificationOut), verification); err != nil {
				fmt.Fprintln(os.Stderr, err)
				os.Exit(1)
			}
		}
	} else if *verificationPath != "" {
		verification, err = audit.ReadJSON(abs(*verificationPath))
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
	result := audit.ScoreInventory(inv, verification)
	if registryUpdate != nil {
		result["registry_update"] = registryUpdate
	}
	if *jsonOut != "" {
		if err := audit.WriteJSON(abs(*jsonOut), result); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
	if *markdown || *jsonOut == "" {
		fmt.Println(audit.Markdown(result))
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
