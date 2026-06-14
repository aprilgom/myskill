---
name: porting-audit-cartography
description: Audit source-to-target port completeness and architectural responsibility boundaries, especially Rust-to-Go package ports. Use when asked how much code is ported, whether a package/module matches its source implementation, whether dependencies are imported from the right ported packages instead of reimplemented locally, whether the port became a ball of mud, what behavior/API/tests are missing, or to produce a scored porting audit with evidence and next actions.
---

# Porting Audit Cartography

## Purpose

Audit a target port against its source implementation and report what is ported, missing, behaviorally divergent, architecturally misplaced, and worth doing next. Prefer evidence from source files, tests, manifests, dependency graphs, imports, and runnable verification over impressions.

## Workflow

1. Identify source and target roots.
   - Use user-provided paths first.
   - If auditing this Andex workspace, default source to `/Users/aprilgom/Andex/codex-rs/<package>` and target to the current repo's corresponding folder.
   - If names differ, inspect docs such as `docs/dependency-grade-2.md`, `README.md`, `PURPOSE.md`, manifests, and nearby package naming.

2. Inventory both sides.
   - First run `go run ./go/cmd/porting-inventory` with source, target, repo, and pretty flags.
   - For a scored baseline, run `go run ./go/cmd/score` with source, target, repo, JSON output, and markdown flags. This wraps inventory extraction and emits category scores, findings, extraction gaps, and ROI actions.
   - Prefer passing `--collect-verification` to `go run ./go/cmd/score` so it runs target package tests, full Go tests, porting-rule checks, and lint itself, then embeds the results in the score JSON. Use `--verification-out <json-file>` when the raw verification evidence should be saved separately.
   - When verification commands have already been run externally, pass `--verification <json-file>` to `go run ./go/cmd/score` so integration/build quality reflects actual focused tests, full tests, lint, and porting-rule checks instead of a default inventory-only score.
   - To render a compact evidence dashboard, run `go run ./go/cmd/render-dashboard` with the score JSON, `assets/template.html`, and an output HTML path.
   - When the repository has a custom Rust-to-Go dependency mapping, pass `--dependency-registry <json-file>`. If omitted in this Andex workspace, the script uses a built-in Andex registry for common workspace crates.
   - The dependency registry may also include `api_mappings` for explicit Rust public API to Go API coverage. Use statuses such as `mapped`, `merged`, `internal_equivalent`, `partial`, or `not_applicable` when idiomatic Go shape differs from Rust.
   - To create an initial `api_mappings` draft, run `go run ./go/cmd/suggest-api-mappings` with source, target, repo, and dependency-registry paths. It preserves existing mappings by default, emits exact/snake-to-Pascal matches as `mapped`, fuzzy token matches as `partial`, and omits unmatched APIs unless `--include-unmatched` is supplied. Use `--in-place` only after reviewing the diff.
   - To refresh `api_mappings` as part of an audit, pass `--update-api-mappings` to `go run ./go/cmd/score` together with `--source`, `--target`, and `--dependency-registry`. This rewrites the registry before inventory extraction, preserves existing mappings by default, and records an `registry_update` summary in the score JSON. Use `--replace-existing-api-mappings` only when regenerating reviewed mappings intentionally.
   - Use the JSON as the initial evidence set for files, Rust public items, Rust tests, Cargo dependencies, Go exported items, Go tests, Go imports, helper candidates, dependency-grade lookup, and deterministic dependency audit rows.
   - Rust `pub(crate)`, `pub(super)`, `pub(self)`, and `pub(in ...)` items are restricted visibility, not external public API. Do not include them in API surface parity counts; use them only as internal responsibility evidence when relevant.
   - Test coverage is based on source-test to target-test mapping, not raw test counts, when mapping evidence is available. Prefer explicit Go comments of the form `// porting: rust-test=<rust_test_name>` immediately before the corresponding `Test...` function. The scanner falls back to normalized test-name similarity only when explicit comments are absent.
   - Edge/error and lifecycle/platform category scores use mapped test evidence tags when available. The scanner tags test names and bodies for signals such as errors, rejected requests, invalid input, serialization, HTTP status/header/body assertions, DNS timeout, run/shutdown/wait, context cancellation, concurrency, resource cleanup, and platform-specific behavior.
   - List source/target files, manifests, tests, generated/platform files; use `rg --files`, `find`, `go list`, `cargo metadata`, `go test`, or focused manifest reads as appropriate.
   - If the script fails or misses language-specific constructs, fall back to manual inspection and mention that extraction was partial.
   - Do not count copied README/PURPOSE files as functional porting.

3. Extract source behavior.
   - Read the source public API, data types, constructors, error types, concurrency/lifecycle behavior, serialization contracts, platform behavior, and tests.
   - For Rust, inspect `Cargo.toml`, `src/lib.rs`, module files, `#[cfg(test)]`, integration tests, feature flags, and important dependencies.
   - Record which source crate/module owns each behavior. If the audited source crate calls another workspace crate, that dependency should normally map to an import of the corresponding target package rather than copied code.
   - Treat tests as behavior specs, but do not assume tests cover everything.
   - When porting tests, add `// porting: rust-test=<name>` above each Go test where practical. This makes audit output deterministic and exposes exactly which source tests remain unmatched.
   - Preserve observable assertions in the target tests. Assertions over error strings, status codes, headers, JSON payloads, shutdown behavior, file permissions, symlinks, OS guards, and timeout/cancellation paths are used as scorer evidence for edge/error and lifecycle/platform parity.

4. Extract target behavior.
   - Read target public API, tests, package docs, and build tags.
   - Inspect target imports and local helper code. Start from the script's `local_helper_candidates`, then flag helpers that look like copied behavior from another package already ported elsewhere.
   - Check `go.mod`, package imports, local package boundaries, and any dependency-grade or porting-order docs.
   - Run the focused target tests when possible.
   - If the target has no tests, say so explicitly and lower confidence.

5. Compare by behavior slices, not just file count.
   - Mark each slice as `ported`, `partial`, `missing`, `divergent`, or `not applicable`.
   - Separate API surface, runtime behavior, edge cases, platform behavior, error text/types, serialization formats, resource lifecycle, concurrency semantics, and tests.
   - For ports across languages, accept idiomatic API shape differences only when behavior and caller guarantees are equivalent.

6. Audit dependency and responsibility boundaries.
   - Start from `deterministic_dependency_audit`, not prose impressions. Treat rows as follows:
     - `correct import`: strong evidence that the target imports the expected ported package.
     - `missing dependency`: deterministic finding when a registered Rust workspace dependency has a known Go equivalent and the target does not import it.
     - `upward dependency violation`: deterministic finding when dependency-grade parsing shows the target imports a higher-stage package.
     - `standard-library replacement allowed` or `external replacement allowed`: accepted only because the registry explicitly says so; still judge semantic parity manually.
     - `allowed local reimplementation`: accepted only for package-specific allowlisted exceptions.
     - `unknown mapping`: do not decide dependency correctness yet; extend the registry or classify manually with explicit evidence.
   - Compare source dependencies to target imports. For each source dependency, classify the target handling as `correct import`, `missing dependency`, `local reimplementation`, `merged responsibility`, `intentionally replaced`, or `not applicable`.
   - Check whether target code bypasses a ported lower-level package by reimplementing path, cache, template, protocol, filesystem, process, watcher, or serialization logic locally.
   - Check whether the target package imports upward to a higher dependency grade or application-level package when the source crate depended only downward.
   - Flag cyclic, overly broad, or convenience imports that make the package harder to port independently.
   - Flag "ball of mud" signs: one package owns unrelated source-crate responsibilities, mixed transport/domain/UI/storage concerns, large local helper clusters with no source ownership match, or tests that validate combined behavior while lower-level packages remain unused.
   - Prefer dependency reuse when the corresponding lower-level port exists and its API can express the needed behavior. Prefer local implementation only for behavior genuinely owned by the audited source package or for target-language standard-library equivalents.

7. Verify.
   - Run focused tests for the audited target package when safe.
   - If source tests can be run cheaply, run them or at least cite their expected coverage.
   - Report any verification command that failed, including whether failure is related to the audited package.

## Scoring

Produce a 100-point score with this rubric:

- API surface parity: 15
- Core behavior parity: 25
- Edge cases and error semantics: 15
- Lifecycle, concurrency, and platform semantics: 12
- Dependency and responsibility boundary fidelity: 13
- Test coverage ported from source behavior: 12
- Integration/build quality: 8
- Documentation/navigation accuracy: 5

The automated `go/cmd/score` baseline uses the detailed rubric in `references/rubric.md` and emits a heuristic score. Core behavior parity is scored from behavior-slice evidence rather than raw test presence: mapped source-test coverage (10), high-confidence or explicit mapping quality (5), public API ratio or explicit API mapping coverage (4), dependency/responsibility cleanliness (3), and edge/lifecycle evidence diversity where the source has tagged behavior (3). Weak test mappings receive partial credit. Integration/build quality uses `--verification` evidence when supplied. Manual review can override the baseline only with explicit evidence, because behavior parity, exact error semantics, and expert-only architectural judgment cannot be proven by inventory alone.

Use these bands:

- 90-100: near complete; only minor idiomatic or doc gaps
- 75-89: substantially ported; some important edge cases or tests missing
- 50-74: usable partial port; core behavior exists but meaningful source behavior is absent
- 25-49: skeleton or narrow behavior slice only
- 0-24: effectively unported

When evidence is thin, give a range or lower-confidence score instead of a precise-looking number.

## Output Format

Keep the final answer compact and evidence-backed:

```markdown
**Porting Audit: <package>**
Score: <n>/100 (<band>)
Confidence: <high|medium|low>

Ported:
- ...

Partial or Divergent:
- ...

Dependency/Responsibility Findings:
- ...

Missing:
- ...

Tests/Verification:
- `<command>`: <result>

Next Actions:
1. ...
2. ...
3. ...
```

Stable JSON schema emitted by `go/cmd/score` is documented in `references/rubric.md`.

For quick user questions like "how much is this ported?", provide the same substance in shorter prose, but still include a score/range and the largest missing behaviors.

## Evidence Discipline

- Cite concrete local file paths and line numbers when making specific claims.
- Use `go/cmd/porting-inventory` output as evidence inventory, not as final judgment.
- Prefer source/target test names, public type names, and function names as evidence.
- Do not infer completeness from file count alone.
- Do not claim full parity when the implementation uses a different backend with weaker guarantees, such as polling instead of OS events, unless tests prove equivalent behavior.
- Distinguish "not ported" from "intentionally not applicable in the target language."
- Distinguish "acceptable target-language replacement" from "local reimplementation of another package's responsibility."
- Treat duplicated code as a finding only when there is evidence that another source crate/package owns the behavior or an existing target package should own it.
- If generated source is involved, audit the generator contract or generated artifacts that callers use.

## Dependency Boundary Checks

Build a compact source-to-target dependency map before judging architecture:

```text
source crate/module -> source dependency -> expected target package/import -> target handling
```

Start from the script's `dependency_map`, then correct its guesses manually. The script intentionally marks weak matches as guesses because package names often differ across languages.

For deterministic checks, prefer the script's `deterministic_dependency_audit` over `dependency_map`. It is driven by a Rust-to-Go alias registry rather than fuzzy name matching. A finding is deterministic only when:

1. the Rust dependency appears in `Cargo.toml`;
2. the registry maps it to an expected Go import, accepted standard-library replacement, accepted external replacement, or package-specific local exception;
3. `go list`/Go import extraction confirms whether the target import exists; and
4. dependency-grade parsing confirms whether the target import direction is allowed.

If any of those inputs is absent, report `unknown mapping` or `manual review required` instead of claiming correctness.

Registry JSON shape is documented in `references/rubric.md`.

Use `allowed_local_reimplementations` sparingly. It is for deliberately scoped exceptions, not a way to silence missing lower-level ports.

Classify each dependency:

- `correct import`: target imports and uses the corresponding ported package.
- `missing dependency`: target has no equivalent behavior yet.
- `local reimplementation`: target implements behavior that belongs to a source dependency.
- `merged responsibility`: target intentionally or accidentally combines multiple source packages.
- `upward dependency`: target imports a package at a higher layer than the source dependency graph allows.
- `standard-library replacement`: target uses a standard library facility that genuinely replaces a source dependency.
- `external replacement`: target uses a third-party dependency instead of the source dependency; judge whether semantics match.

Use these evidence patterns:

- Source `Cargo.toml` or module imports show ownership.
- Target `import` blocks show whether the equivalent ported package is reused.
- Repeated helper names, algorithms, error strings, serialization shape, or path handling suggest copied responsibility.
- Tests that duplicate lower-level behavior inside a higher package suggest misplaced responsibility.
- Lack of imports is not automatically bad for zero-dependency source packages.

When recommending fixes, preserve porting order:

1. Port or complete the lower-level dependency first.
2. Replace local helper code with imports of that dependency.
3. Add contract tests at the lower-level package.
4. Keep only orchestration tests in the higher-level package.

## Andex Rust-to-Go Checks

For this workspace, always check these porting risks when relevant:

- Rust `Drop`/RAII behavior versus Go `Close` or garbage collection.
- Rust `Result`/custom error enums versus Go errors and `errors.Is`.
- Rust async/Tokio behavior versus Go goroutines, contexts, channels, and cancellation.
- Rust feature flags, platform cfgs, and dependency-backed behavior versus Go build tags and standard-library replacements.
- `PathBuf`/canonicalization behavior versus Go string or `filepath` behavior.
- JSON/TOML formatting, byte offsets, UTF-8 boundaries, and exact error strings when observable.
- Public API generality, such as Rust traits/generics versus Go concrete functions or generic constraints.
- Dependency-grade direction from `docs/dependency-grade-2.md`: lower-stage packages should not depend on higher-stage packages, and higher-stage ports should reuse completed lower-stage ports instead of copying their logic.

## Stop Conditions

Ask for clarification only if the source implementation cannot be located and multiple plausible sources exist. Otherwise make a reasonable mapping, state it, and proceed.

## Validation

- `cd go && go test ./...`
- `go run ./go/cmd/porting-inventory --source <source-root> --target <target-root> --repo <target-repo> --pretty`
- `go run ./go/cmd/score --source <source-root> --target <target-root> --repo <target-repo> --json /tmp/porting-score.json --markdown`
- `go run ./go/cmd/score --source <source-root> --target <target-root> --repo <target-repo> --verification <verification.json> --json /tmp/porting-score.json --markdown`
- `go run ./go/cmd/score --source <source-root> --target <target-root> --repo <target-repo> --collect-verification --verification-out /tmp/porting-verification.json --json /tmp/porting-score.json --markdown`
- `go run ./go/cmd/score --source <source-root> --target <target-root> --repo <target-repo> --dependency-registry <registry.json> --update-api-mappings --json /tmp/porting-score.json --markdown`
- `go run ./go/cmd/suggest-api-mappings --source <source-root> --target <target-root> --repo <target-repo> --dependency-registry <registry.json> --out /tmp/registry-with-api-mappings.json`
- `go run ./go/cmd/render-dashboard /tmp/porting-score.json --template assets/template.html --out /tmp/porting-audit.html`
- Check rendered HTML is non-empty and has no unresolved placeholders such as `{{...}}` or `__TOKEN__`.

The self-test uses temporary fixtures, asserts deterministic dependency handling, verifies scorer JSON shape, checks ROI actions, renders HTML, and guards against unresolved placeholders. It intentionally includes an unknown mapping fixture so weak proxy/manual-review gap behavior is tested.

## Files

- `go/audit` - shared Go implementation for inventory extraction, scoring, API mapping suggestions, verification collection, and HTML rendering.
- `go/cmd/porting-inventory` - extracts source/target inventory and deterministic dependency audit rows.
- `go/cmd/score` - converts inventory into a 100-point heuristic baseline with findings, risks, extraction gaps, and ROI actions.
- `go/cmd/render-dashboard` - renders a score JSON into a compact single-file HTML dashboard.
- `go/cmd/suggest-api-mappings` - suggests dependency-registry API mappings.
- `go/audit/audit_test.go` - fixture-based validation for inventory, score, render, and placeholder checks.
- `assets/template.html` - HTML dashboard template.
- `references/rubric.md` - detailed scoring criteria, grade bands, and failure modes.
