# Code Cartography Rubric

## Target

The target is a repository's hand-written source code. The score supports maintainability planning: where to review first, what code is expensive to change, and which small actions reduce the most future maintenance risk.

## Expert Evaluation Model

A competent maintainer does not rank files by size alone. They look for risk combinations:

- Complex local flow plus weak tests.
- Broad dependency surface plus frequent side effects.
- Mixed responsibilities plus long files or long blocks.
- Repeated logic plus unclear failure handling.
- Persistent TODO/FIXME/HACK markers in change-sensitive source.
- Missing context for code that is central, unusual, or hard to change.

The scanner can collect these signals, but manual review must decide whether a hotspot is intentional, generated, constrained by framework shape, or already mitigated by external tests.

## Categories

### A. Local Complexity & Readability - 20

Strong evidence: most files are short enough to scan, branch density is moderate, nesting is shallow, and long block candidates are rare.

Partial evidence: a few large or nested files exist, but they are isolated or tested.

Weak evidence: many large files, deep nesting, high branch density, or long block candidates in hand-written source.

Proxy validity: line count and branch keyword density are imperfect, but useful early warning signs for review cost.

Manual review: confirm whether flagged files are generated, framework-required, or intentionally table-driven.

### B. Responsibility Focus & File Shape - 15

Strong evidence: file names, paths, and tokens suggest focused responsibilities.

Partial evidence: some orchestration files mix concerns, but are small and tested.

Weak evidence: large files combine persistence, transport, UI, auth, validation, notification, or async workflow concerns.

Proxy validity: concern keywords are only hints; they become more meaningful when combined with size and test gaps.

Manual review: distinguish legitimate boundary modules from accidental god files.

### C. Change Coupling & Dependency Surface - 15

Strong evidence: most files have small import surfaces and few central fan-in hotspots.

Partial evidence: broad imports are concentrated in composition roots or adapters.

Weak evidence: many source files import widely, rely on deep relative paths, or cluster around high fan-in files.

Proxy validity: import count and rough fan-in/fan-out indicate change propagation risk.

Manual review: distinguish stable shared primitives from unstable central modules.

### D. Test Proximity & Behavioral Safety - 15

Strong evidence: tests are present and source files have nearby or conventionally named tests.

Partial evidence: tests exist but are distant, integration-heavy, or unevenly distributed.

Weak evidence: few tests, low source-test proximity, or high-risk files without nearby behavioral coverage.

Proxy validity: filename/path proximity does not prove quality, but it is a defensible baseline for change safety.

Manual review: inspect whether tests assert behavior, not just snapshots or smoke paths.

### E. Duplication & Repetition Risk - 10

Strong evidence: repeated normalized lines are limited or confined to fixtures/config/generated content.

Partial evidence: repetition exists but is small or intentionally explicit.

Weak evidence: repeated hand-written logic appears across several source files.

Proxy validity: normalized line repetition is a weak proxy, so it should guide review rather than trigger automatic extraction.

Manual review: avoid extracting coincidental or domain-required repetition.

### F. Error Handling & Edge Case Visibility - 10

Strong evidence: files with side effects show visible failure handling or edge-case paths.

Partial evidence: failure handling exists but is inconsistent or hidden in wrappers.

Weak evidence: side-effect-heavy code has few visible error/edge-case markers.

Proxy validity: keywords cannot prove correctness, but missing failure-path evidence is a useful review prompt.

Manual review: check language idioms and framework-level error boundaries before scoring harshly.

### G. Codebase Hygiene & Volatility - 10

Strong evidence: low debt-marker density, clean generated/vendor exclusion, few extraction gaps.

Partial evidence: TODO/FIXME markers are present but localized.

Weak evidence: many debt markers, temporary/workaround notes, stale legacy names, or unreadable source files.

Proxy validity: debt markers are explicit maintainer signals and should be prioritized when near hotspots.

Manual review: distinguish active migration notes from abandoned debt.

### H. Maintainability Context - 5

Strong evidence: README, contributing/development docs, CODEOWNERS, docs, or ADRs provide local working context.

Partial evidence: basic README exists but little code-maintenance context.

Weak evidence: no visible context for how code should be changed or owned.

Proxy validity: context files do not make code maintainable, but they reduce onboarding and change risk.

Manual review: read the content before giving full credit.

## Red Flags

- A file appears in several risk categories at once.
- High fan-in files have weak tests and volatile TODO/FIXME notes.
- Repeated logic occurs in side-effect-heavy code.
- Generated/vendor files dominate metrics because exclusions failed.
- The scanner reports many extraction gaps.

## Actions

High-priority actions should reduce high-weight risks with small scope:

- Add focused tests around top high-risk files before refactoring.
- Split mixed-responsibility files along visible concern boundaries.
- Reduce import surface in high fan-out files.
- Extract duplicated behavior only after confirming semantic equivalence.
- Make failure paths explicit where side effects are concentrated.
