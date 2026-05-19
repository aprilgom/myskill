---
name: tldr-cheatsheet-cartography
description: Audit `.tldr.md` cheat sheets for documentation quality, source coverage, code snippet usefulness, structure, correctness risk, and reader actionability. Produces a 100-point quality score, evidence-backed findings, and ROI-ranked edits. Use when reviewing, scoring, improving, or batch-checking TLDR/cheatsheet Markdown files, especially Hugo documentation sidecars paired with source `.md` pages. Do not use for generic prose copyediting unless the artifact is intended to be a concise cheat sheet.
---

# TLDR Cheatsheet Cartography

Evaluate whether a `.tldr.md` file works as a high-signal cheat sheet for its paired source document. The score supports the decision: "Is this cheat sheet useful enough to publish, and what edits would most improve it?"

## Workflow

1. Identify the target `.tldr.md`. If the user gives a source `.md`, infer the sidecar by replacing `.md` with `.tldr.md`.
2. Find the paired source page when available. For `foo.tldr.md`, use `foo.md`.
3. Run the baseline scanner:

```bash
python3 <skill-dir>/scripts/score.py <tldr-path> --json /tmp/tldr-score.json --markdown
```

If a nonstandard source path is needed:

```bash
python3 <skill-dir>/scripts/score.py <tldr-path> --source <source-md> --json /tmp/tldr-score.json --markdown
```

4. Read `references/tldr-cheatsheet-rubric.md` for manual review when judging usefulness, correctness, or source coverage beyond scanner proxies.
5. Adjust findings only with concrete evidence from the `.tldr.md`, source `.md`, generated HTML, or repository conventions.
6. Report the score, top findings, and the highest-ROI edits. If asked to improve the file, patch the `.tldr.md` directly and rerun the scanner.

## Expert Model

A strong reviewer behaves like a documentation editor, Go/API teacher, and impatient reader. They check whether the cheat sheet preserves the source's important decisions, compresses them without distortion, includes copy-pasteable snippets, and helps a reader act quickly without replacing the full document.

Strong cheat sheets are not summaries alone. They expose decisions, gotchas, examples, and "when to use this" guidance. Weak cheat sheets are either too sparse, too verbose, code-free, source-incomplete, or mechanically copied from the source.

## Rubric

Total: 100 points. Detailed criteria live in `references/tldr-cheatsheet-rubric.md`.

| Cat | Name | Points |
|-----|------|--------|
| A | Source Coverage & Prioritization | 20 |
| B | Cheat Sheet Density & Scanability | 16 |
| C | Code Snippet Usefulness | 18 |
| D | Correctness & Source Faithfulness | 18 |
| E | Actionability & Decision Cues | 14 |
| F | Integration With Site Conventions | 8 |
| G | Maintainability & Edit Safety | 6 |

Grades:
- 90-100: Publish-Ready
- 75-89: Strong With Minor Gaps
- 60-74: Useful Draft
- 40-59: Needs Editorial Pass
- <40: Not Yet a Cheat Sheet

## What The Script Checks

- Front matter presence and `build.render: never` convention
- Markdown heading count and heading depth
- Bullet/list density, paragraph length, and total size
- Fenced code block count and language tags
- Go snippet signals such as `func`, `return`, `defer`, `for`, `if`, `type`
- Source heading coverage by title overlap
- Potential copy-paste risk from very long code blocks or excessive prose
- TODO/placeholders and empty/near-empty files

The scanner is an evidence baseline, not an oracle. Manual review must judge whether examples are correct, whether omissions matter, and whether the cheat sheet reflects the actual source's priorities.

## Output Rules

- Cite file paths and concrete evidence such as heading names, code block counts, missing source sections, and representative lines.
- Separate scanner findings from manual judgment.
- Do not invent source coverage. If the source page is missing or unreadable, mark an extraction gap.
- Prefer edits that improve reader utility: better examples, clearer decision cues, missing caveats, and tighter structure.
- Keep final reports short: score/grade, 2-3 findings, Top 3 actions, generated JSON path if any.

## Validation

Before claiming the skill works after editing it, run:

```bash
python3 -m py_compile <skill-dir>/scripts/score.py
python3 <skill-dir>/scripts/score.py <sample.tldr.md> --json /tmp/tldr-score.json --markdown
```

For this repository, a good smoke target is:

```bash
python3 <skill-dir>/scripts/score.py content/ko/effective-go/7_Functions.tldr.md --markdown
```

## Common Pitfalls

- Rewarding length instead of density.
- Treating any code block as useful without checking whether it teaches the source's point.
- Penalizing a concise cheat sheet for omitting low-priority source prose.
- Copyediting grammar while ignoring missing decisions, caveats, or examples.
- Letting scanner keyword overlap decide correctness.

## Output Format

```markdown
**Score**
<total>/100 - <grade>
Mode: heuristic baseline + manual cheatsheet review

**Findings**
1. <finding with file/path evidence>
2. <finding with file/path evidence>

**Top Actions**
1. [<Effort>, priority <score>] <edit> - <impact>
2. [<Effort>, priority <score>] <edit> - <impact>
3. [<Effort>, priority <score>] <edit> - <impact>
```

## Files

- `scripts/score.py` - deterministic baseline scorer, Python stdlib only
- `references/tldr-cheatsheet-rubric.md` - detailed scoring rubric and manual review criteria
