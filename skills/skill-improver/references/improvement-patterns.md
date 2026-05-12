# Skill Improvement Patterns

Use these patterns to patch common evaluator findings without making the skill unnecessarily long.

## Trigger Metadata

Problem: description is vague or misses common user phrasing.

Patch pattern:
- Start with the task verb: "Use when asked to..."
- Name the artifact: skill, SKILL.md, skill folder, metadata, references, scripts.
- Include common user intents: review, improve, fix, refactor, install, compare, score.
- Add boundaries only when false triggers are likely.

Avoid:
- Full workflow in the description.
- Marketing language.
- Generic claims like "helps with productivity."

## Executable Workflow

Problem: the body explains concepts but does not tell the agent what to do.

Patch pattern:
1. Identify target.
2. Read minimal required files.
3. Run deterministic checks if available.
4. Make scoped edits.
5. Verify.
6. Report.

Include commands only when they are stable. Use placeholders like `<target-skill-dir>` when the path varies.

## Progressive Disclosure

Problem: `SKILL.md` is too long or mixes reference material with procedure.

Patch pattern:
- Keep trigger, workflow, guardrails, and output format in `SKILL.md`.
- Move detailed examples, rewrite templates, and scoring tables to `references/`.
- Link each reference from `SKILL.md` with a clear "when to read" condition.

Avoid:
- Deep chains of references.
- Duplicating the same rule in multiple files.

## Validation

Problem: skill says to verify but does not define evidence.

Patch pattern:
- Name the exact command or inspection.
- State what passing means.
- State what to report if verification cannot run.

Examples:
- Run the bundled scorer and compare before/after JSON.
- Compile scripts with `python3 -m py_compile`.
- Render generated documents or screenshots when visual output is involved.

## Resource Connection

Problem: scripts/assets/references exist but are disconnected.

Patch pattern:
- Add a `Files` or `References` section.
- For each resource, state when to use it.
- Prefer invoking scripts without loading their source unless debugging or editing them.

## Common Pitfalls

Problem: agents repeatedly make the same bad edits.

Patch pattern:
- Add 4-7 concise bullets under `Common Pitfalls` or `Guardrails`.
- Phrase each as a behavioral constraint.
- Keep only pitfalls that would change future agent behavior.

## Before/After Report

Problem: user cannot tell what improved.

Patch pattern:
- Include before score, after score, changed files, high-signal improvements, remaining risks, and verification commands.
- If the score does not improve, explain why the patch is still valid or revert/revise.
