---
name: improve-cartography-skill
description: Improve cartography-style Codex/Claude skills by first evaluating them with cartography-skill-evaluator, then patching the target skill's rubric, scanner, JSON schema, dashboard, validation, triggers, and ROI actions. Use when asked to fix, upgrade, refactor, optimize, harden, or improve a cartography skill, readiness map skill, score dashboard skill, diligence cartography skill, maturity cartography skill, or evidence-based evaluation skill.
---

# Improve Cartography Skill

This skill turns a `cartography-skill-evaluator` review into concrete improvements. It keeps evaluation and editing separate so changes are driven by evidence rather than preference.

## Core Rule

Always run or obtain a baseline cartography-specific evaluation before editing.

- Evaluation phase: uses `$cartography-skill-evaluator` or its bundled baseline scorer. It produces score, category breakdown, findings, and ROI actions. It does not edit files.
- Improvement phase: patches only the target cartography skill using the evaluation result. It does not redo the baseline from scratch unless the evaluation artifact is missing or invalid.
- Verification phase: reruns the evaluator and any target skill validation to confirm before/after improvement.

If subagents are explicitly allowed, use separate evaluation and improvement agents. If not, perform the same separation locally: save/read the baseline evaluation before editing, then rerun evaluation after editing.

## Workflow

1. Identify the target cartography skill.
   - If the user gives a path, use that folder.
   - If the user gives only `SKILL.md`, improve the containing folder when possible.
   - If no target is provided and several `*-cartography` skills exist, ask one concise question.

2. Capture baseline evaluation.

```bash
python3 <cartography-skill-evaluator-score-script> <target-skill-dir> \
  --json /tmp/improve-cartography-before.json --markdown
```

3. Manually review the baseline.
   - Prioritize P1 findings first.
   - Then prioritize low-scoring categories by category weight and fix effort.
   - Read `references/improvement-patterns.md` for concrete patch patterns.
   - Do not blindly chase 100/100 if a lightweight cartography skill intentionally omits scripts or dashboards.

4. Patch the target skill.
   - Target SKILL.md: trigger fit, workflow, rubric summary, output rules, validation, final report shape, pitfalls, file inventory.
   - Target rubric references: category criteria, evidence levels, manual review boundaries, grade bands.
   - Target scorer script: artifact scanning, evidence/gap capture, deterministic JSON, extraction boundaries, ROI actions.
   - Target dashboard renderer: required field validation, template rendering, failure behavior.
   - Target HTML template: score, category bars, evidence, risks, actions, extraction gaps, no unresolved placeholders.
   - Target self-test script: positive/negative fixtures, scorer + renderer assertions, placeholder checks.
   - Target agents metadata: update only when metadata no longer matches the skill.

5. Verify target skill integrity.
   - Compile edited Python scripts.
   - Run the target self-test script when present.
   - Run target scorer and renderer on a small fixture when practical.
   - Confirm generated HTML is non-empty and has no unresolved placeholders.
   - Confirm no generated cache files are left in the skill folder.

6. Rerun cartography evaluator.

```bash
python3 <cartography-skill-evaluator-score-script> <target-skill-dir> \
  --json /tmp/improve-cartography-after.json --markdown
```

7. Report before/after.
   - Include score movement, changed files, fixed findings, skipped findings with reasons, remaining risks, and verification commands.

## Evaluation Agent Prompt

Use this prompt when delegating evaluation:

```text
Evaluate the target cartography skill with $cartography-skill-evaluator. Produce score, category breakdown, evidence paths, findings, and ROI-ranked actions. Do not edit files. Distinguish automatic baseline evidence from manual judgment. Focus on cartography-specific reliability: rubric quality, evidence discipline, scanner fit, JSON schema, dashboard usefulness, validation integrity, triggers, and ROI action quality.
```

## Improvement Agent Prompt

Use this prompt when delegating implementation:

```text
Improve the target cartography skill using the supplied cartography-skill-evaluator result. Patch only the target skill files. Prioritize P1/P2 and highest-ROI issues. Do not redo the baseline evaluation from scratch. Preserve user changes. Keep SKILL.md concise and move detailed rubric or patch patterns into references. Strengthen scanner/dashboard/self-test only when the target skill promises production cartography. List changed files and any evaluation findings intentionally left unresolved.
```

## Improvement Priorities

Apply fixes in this order:

1. Broken structure: missing `SKILL.md`, invalid frontmatter, missing referenced files, scaffold TODOs.
2. Misleading cartography contract: target, decision, score meaning, or exclusions are unclear.
3. Rubric defects: point total not 100, overlapping categories, weak evidence criteria, missing grade bands.
4. Evidence discipline: scanner overweights keywords, omits evidence paths, hides extraction gaps, or blurs manual judgment.
5. JSON/output instability: undocumented schema, renderer/scorer mismatch, prose-only scoring.
6. Dashboard weakness: no evidence/gaps, unresolved placeholders, decorative design over decision support.
7. Validation gaps: no fixture, no scorer/renderer test, no placeholder check, no compile/smoke commands.
8. ROI action weakness: generic actions, no effort/impact/priority, no link to high-weight gaps.
9. Progressive disclosure and metadata: bloated target SKILL.md, duplicated details, stale agents metadata.

## Guardrails

- Do not convert every cartography skill into a full production scaffold if the user wants a lightweight rubric-only skill.
- Do not invent domain evidence, benchmark results, customers, policies, metrics, or test outcomes.
- Do not overwrite unrelated user edits.
- Do not add README, changelog, installation guide, or generic docs.
- Do not add scripts unless they materially improve repeatability or validation.
- Do not let automated score override manual judgment; explain any deliberate score tradeoff.
- Do not claim completion until evaluation and verification have run or a blocker is reported.

## Output Format

```markdown
**Before/After**
- Before: <score>/100 - <grade>
- After: <score>/100 - <grade>

**Changed Files**
- <path>

**Fixed**
- <finding fixed and why it matters>
- <finding fixed and why it matters>

**Remaining Risks**
- <skipped/manual item or "None found">

**Verification**
- `<command>` - <result>
```

## Files

- `references/improvement-patterns.md` - category-specific patch patterns for improving cartography skills.
