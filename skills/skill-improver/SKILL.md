---
name: skill-improver
description: Improve Codex/Claude-style skills by separating evaluation from editing, with an optional 100-point cartography map, evidence dashboard, rubric, and ROI actions. Use when asked to fix, upgrade, refactor, optimize, or improve a skill, SKILL.md, skill folder, skill metadata, trigger behavior, workflow, validation, bundled resources, or progressive disclosure. Prefers a separate eval agent/phase using skill-evaluator, then a separate improve agent/phase that patches the target and verifies before/after results.
---

# Skill Improver

This skill improves another skill while keeping evaluation and editing separate. The goal is not to make the skill longer; it is to make it trigger more accurately, execute more reliably, load less unnecessary context, and validate its outputs better.

## Core Rule

Separate evaluator and improver responsibilities.

- Eval agent/phase: scores the target skill and produces evidence, findings, and ROI actions.
- Improve agent/phase: patches the target using the evaluation result as input.
- Main agent: coordinates scope, preserves user changes, verifies before/after, and reports the outcome.

If subagents are available and the user has allowed agent delegation, use separate agents. If subagents are not available or not allowed, perform the same separation as two saved phases: write/read the baseline evaluation before editing, then rerun evaluation after editing.

## Workflow

1. Identify the target skill.
   - If the user gives a path, use it.
   - If the user gives a `SKILL.md`, improve that skill folder if possible.
   - If the target is ambiguous, ask one concise question.
2. Capture a baseline evaluation.
   - Prefer `$skill-evaluator`.
   - For an evidence-backed improvement map, run the bundled cartography scorer:

```bash
python3 <skill-improver-dir>/scripts/score.py <target-skill-dir> \
  --json /tmp/skill-improver-map-before.json \
  --markdown
```

   - If installed locally, run:

```bash
python3 ~/.codex/skills/skill-evaluator/scripts/score.py <target-skill-dir> \
  --json /tmp/skill-improver-before.json \
  --markdown
```

3. Decide the improvement scope.
   - Use top ROI actions from the eval result.
   - Prefer P1/P2 findings over polish.
   - Keep scope to the target skill unless the user asks for repo-wide cleanup.
4. Patch the target skill.
   - Edit `SKILL.md` for trigger, workflow, output, validation, and common pitfalls.
   - Edit `references/` when detail should not live in the always-loaded body.
   - Edit or add scripts only when deterministic checks are repeatedly useful.
   - Do not add README, changelog, installation guide, or unrelated docs.
5. Rerun evaluation.

```bash
python3 ~/.codex/skills/skill-evaluator/scripts/score.py <target-skill-dir> \
  --json /tmp/skill-improver-after.json \
  --markdown
```

When the bundled cartography scorer was used before editing, rerun it with a matching after JSON path.

6. Verify skill integrity.
   - `SKILL.md` frontmatter has `name` and `description`.
   - Referenced files exist.
   - Scripts compile or run with a minimal smoke test.
   - If using the bundled scorer/dashboard, run `python3 -m py_compile scripts/score.py scripts/render_dashboard.py scripts/self_test.py` and `python3 scripts/self_test.py` from this skill folder.
   - No generated cache files remain in the skill folder.
7. Report:
   - before/after score
   - changed files
   - main improvements
   - remaining risks or manual review needs

## Eval Agent Prompt

Use this prompt when delegating evaluation:

```text
Evaluate the target skill as an agent-facing operating procedure. Use skill-evaluator if available. Produce JSON/Markdown with score, category breakdown, evidence, findings, and ROI-ranked actions. Do not edit files. Do not infer intended fixes beyond concrete recommendations.
```

## Improve Agent Prompt

Use this prompt when delegating editing:

```text
Improve the target skill using the supplied evaluation result. Patch only the target skill files. Do not redo the evaluation from scratch. Prioritize P1/P2 and high-ROI actions. Preserve user changes. Keep SKILL.md concise and move detailed patterns into references when useful. List changed files.
```

## Improvement Priorities

Apply fixes in this order:

1. Broken structure: missing `SKILL.md`, invalid frontmatter, missing referenced files.
2. Trigger reliability: vague, too narrow, too broad, or overlapping description.
3. Workflow executability: unclear steps, missing commands, unsafe assumptions, no fallback.
4. Validation integrity: no evidence requirements, no rerun checks, answer leakage in validation.
5. Progressive disclosure: bloated main body, buried essential instructions, duplicated details.
6. Resource connection: scripts/assets/references exist but are not connected to the workflow.
7. Output usefulness: no final report shape, no prioritization, no user-facing summary guidance.
8. Maintainability polish: naming, volatile facts, common pitfalls, UI metadata.

## Pattern Reference

Read `references/improvement-patterns.md` when a finding needs a concrete rewrite pattern.
Read `references/rubric.md` when producing or interpreting the bundled 100-point improvement map.

## Bundled Cartography Output

`scripts/score.py` emits JSON with `schema_version`, `target`, `score`, `grade`, `categories`, `findings`, `risks`, `extraction_gaps`, and ROI-ranked `actions`. `scripts/render_dashboard.py` turns that JSON into a single-file HTML dashboard using `assets/template.html`; rendering must fail if required fields or template replacements are missing.

## Guardrails

- Do not make the skill more verbose unless the added text changes agent behavior.
- Do not add scripts just to look systematic.
- Do not treat the bundled scorer as a substitute for `$skill-evaluator`; use it when the user needs a repeatable improvement map, dashboard, or before/after JSON.
- Do not treat automated score as final when manual quality clearly disagrees.
- Do not overwrite unrelated user edits.
- Do not let the improve phase silently discard eval findings; report any skipped finding with a reason.
- Do not use subagents unless the user explicitly allowed agent delegation or parallel agent work.

## Output Format

```markdown
**Before/After**
- Before: <score>/100 - <grade>
- After: <score>/100 - <grade>

**Changed Files**
- <path>

**Improvements**
- <high-signal change>
- <high-signal change>

**Remaining Risks**
- <manual review item or "None found">

**Verification**
- <command> - <result>
```

## Files

- `references/improvement-patterns.md` - concrete rewrite patterns for common skill-evaluator findings.
- `references/rubric.md` - 100-point skill improvement cartography rubric and JSON schema.
- `scripts/score.py` - deterministic heuristic scorer for skill improvement readiness.
- `scripts/render_dashboard.py` - renders score JSON into `assets/template.html`.
- `scripts/self_test.py` - fixture-based scorer and dashboard smoke test.
- `assets/template.html` - single-file HTML dashboard template.
