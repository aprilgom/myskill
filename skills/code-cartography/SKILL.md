---
name: code-cartography
description: Use when evaluating repository code quality, maintainability risk, complexity hotspots, test safety, duplication, code hygiene, or ROI-ranked refactoring opportunities across a polyglot codebase.
---

# Code Cartography

This skill maps code-level maintainability risk across a repository. It is for code quality and maintenance planning, not semantic correctness, security review, performance tuning, or architecture boundary scoring.

## Workflow

1. Choose the repository path. If the user does not provide one, use the current working directory.
2. Run the heuristic scanner.

```bash
python3 <skill-dir>/scripts/score.py <repo-path> \
  --json <output-path>/code-score.json
```

3. Read `references/code-rubric.md` when manual adjustment is needed. Treat the scanner as an evidence collector, not an oracle.
4. Render the dashboard.

```bash
python3 <skill-dir>/scripts/render_dashboard.py \
  <output-path>/code-score.json \
  --template <skill-dir>/assets/template.html \
  --out <output-path>/code-map.html
```

5. Validate that the HTML contains the score, category bars, risk hotspots, ROI actions, and no unresolved `{{PLACEHOLDER}}` tokens.
6. Report briefly: score/grade, top 1-2 risks, Top 3 actions, generated file paths.

If the target repo has `docs/`, prefer `docs/code-score.json` and `docs/code-map.html`; otherwise write them at the repo root unless the user requests another output path.

## Expert Model

Good maintainable code is locally readable, focused in responsibility, cheap to change, covered near behavior, and explicit about failure paths. A code maintainer first looks for files that combine several risk signals: large or deeply nested code, broad dependency surface, missing nearby tests, repeated logic, persistent TODO/FIXME notes, and side effects without visible error handling.

The scanner ranks risk combinations rather than raw metrics alone. A 500-line generated file is usually low risk; a 180-line hand-written orchestration file with many imports, TODOs, and no nearby test can be high risk.

## Rubric

Total: 100 points.

| Cat | Name | Points |
|-----|------|--------|
| A | Local Complexity & Readability | 20 |
| B | Responsibility Focus & File Shape | 15 |
| C | Change Coupling & Dependency Surface | 15 |
| D | Test Proximity & Behavioral Safety | 15 |
| E | Duplication & Repetition Risk | 10 |
| F | Error Handling & Edge Case Visibility | 10 |
| G | Codebase Hygiene & Volatility | 10 |
| H | Maintainability Context | 5 |

Grades:

- 85-100: Maintainability-Native
- 70-84: Maintainability-Ready
- 55-69: Maintainability-Assisted
- 35-54: Maintainability-Fragile
- <35: Maintainability-Hostile

## What The Script Checks

- Polyglot source files by extension, excluding generated, vendor, build, dependency, binary, minified, and lock files.
- File length, non-comment LOC, branch keyword density, approximate nesting, and long block candidates.
- Import/include/use/require patterns and rough fan-in/fan-out signals.
- Test file ratio and source-to-test proximity by path and filename conventions.
- Repeated normalized lines across hand-written source files.
- TODO, FIXME, HACK, workaround, temporary, legacy, and deprecated markers.
- Side-effect markers with weak visible failure handling signals.
- Maintainability context files such as README, CONTRIBUTING, CODEOWNERS, docs, and ADRs.

## Output Rules

- Prefer concrete paths, counts, and combined risk evidence over generic refactoring advice.
- Do not claim exact cyclomatic complexity unless a language-specific parser was used.
- Do not penalize generated, vendor, dependency, minified, lock, build output, or fixture-like files as primary maintainability risks.
- ROI actions must include `effort`, `impact`, `priority`, `action`, and evidence.
- Manual review should decide whether risk is intentional, generated, or constrained by external APIs.
- Avoid rewrite recommendations unless smaller extraction, test, or failure-path improvements cannot reduce the risk.

## Validation

```bash
python3 -m py_compile <skill-dir>/scripts/score.py \
  <skill-dir>/scripts/render_dashboard.py \
  <skill-dir>/scripts/self_test.py
python3 <skill-dir>/scripts/self_test.py
```

## Output Format

```markdown
**Score**
<total>/100 - <grade>
Mode: heuristic baseline + manual maintainability review

**Key Findings**
1. <highest-risk code maintainability finding with evidence path/count>
2. <second finding, if material>

**Top ROI Actions**
1. [<effort>, priority <score>] <action> - <impact/evidence>
2. [<effort>, priority <score>] <action> - <impact/evidence>
3. [<effort>, priority <score>] <action> - <impact/evidence>

Generated: <code-score.json>, <code-map.html>
```

## Files

- `scripts/score.py` - polyglot maintainability signal scanner, Python stdlib only.
- `scripts/render_dashboard.py` - renders `assets/template.html` from `code-score.json`.
- `scripts/self_test.py` - creates a fixture, runs scanner and renderer, verifies output shape.
- `references/code-rubric.md` - detailed scoring model and manual review guidance.
- `assets/template.html` - single-file dashboard template.
