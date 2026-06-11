---
name: dependency-grade-cartography
description: Build deterministic dependency stage maps for workspaces or package internals. Use when asked to split dependencies into levels/stages/grades, decide porting order, document dependency layers, find cycles, verify lower-level dependency direction, or generate dependency-grade Markdown/JSON from Rust Cargo crates or Rust module files.
---

# Dependency Grade Cartography

## Purpose

Classify a dependency graph into implementation stages so lower-stage units can be ported or audited before higher-stage units. Prefer deterministic extraction over prose guesses.

## Workflow

1. Identify the graph boundary.
   - For workspace/package order, use Rust Cargo workspace crates.
   - For a package's internal file order, use Rust module files under `src/`.
   - If the user names a Go porting target, still grade from the Rust source when the task is about Rust-to-Go porting order.

2. Run the bundled analyzer before writing a stage table.
   - Workspace crates:
     ```bash
     python3 <skill>/scripts/dependency_grade.py workspace \
       --root /path/to/andex-rs \
       --markdown docs/dependency-grade.md \
       --json /tmp/dependency-grade.json
     ```
   - Rust package internals:
     ```bash
     python3 <skill>/scripts/dependency_grade.py rust-modules \
       --root /path/to/andex-rs/protocol \
       --markdown docs/protocol_dependency_grade.md \
       --json /tmp/protocol-dependency-grade.json
     ```
     Add `--include-tests` when the stage map should include Rust `*_tests.rs` files.

3. Review the extraction.
   - Confirm cycles are listed as strongly connected components.
   - Confirm test/dev-only dependencies are excluded unless the user explicitly asks to include them.
   - Confirm generated/legacy files are called out separately when excluded by project policy.
   - For Rust module graphs, inspect broad cycles manually; `crate::foo` references can be exact enough for order, but not for semantic ownership.

4. Write the result as dependency evidence, not final architecture judgment.
   - Use grade 0 for units with no in-bound dependency on other in-scope units.
   - Use grade `n` when a unit depends on at least one grade `n-1` component and no higher component.
   - Collapse cyclic units into one component and assign one grade to the whole component.
   - For re-export roots such as `lib.rs`, expect a high grade because they depend on many modules.

5. Use the grade map to guide porting.
   - Port grade 0 first.
   - A grade `n` target should import/reuse completed lower-grade Go packages instead of reimplementing their responsibilities.
   - When a target imports a higher-grade package, flag an upward dependency risk.
   - When source dependency points to a lower-grade unit but target has no matching import or accepted replacement, flag a missing dependency or local reimplementation risk.

## Script Notes

- The analyzer emits Markdown and JSON.
- Workspace mode uses `cargo metadata --no-deps` when available.
- Rust module mode scans `src/*.rs` and nested module files for `crate::<module>` references.
- The script deliberately ignores Rust `dev-dependencies` by default because test helpers often create cycles that do not define production porting order.

## Output Style

When reporting to the user, include:

- Source boundary and extraction method.
- Total units, max grade, and cycle components.
- Grade-by-grade table.
- Any manual caveats, such as legacy exclusion or broad cyclic core modules.
- The file paths written.
