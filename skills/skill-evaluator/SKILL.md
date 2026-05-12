---
name: skill-evaluator
description: Use when asked to evaluate, review, audit, score, benchmark, or compare an existing Codex/Claude-style skill, SKILL.md, skill folder, skill metadata, skill rubric, or skill evaluation result. Use as the evaluation phase for improvement workflows, not as the primary skill for editing or creating skills.
---

# Skill Evaluator

This skill evaluates another skill as an agent-facing operating procedure, not as user documentation. The output is a scored review with concrete fixes, evidence, and ROI-ranked actions.

## Workflow

1. Identify the skill target.
   - If the user gives a path, inspect that skill folder.
   - If the user gives a `SKILL.md`, evaluate its parent folder when accessible; otherwise evaluate the standalone file and note missing folder context.
   - If no path is given, evaluate the most relevant skill in the current repo or ask one concise question if no reasonable target exists.
2. Read only the necessary files.
   - Always read `SKILL.md`.
   - Read agents/openai.yaml if present.
   - Read referenced files only when the main workflow depends on them.
   - List scripts/assets by filename first; open scripts only when they are part of the skill's promised behavior.
3. Run the deterministic baseline scorer when a skill folder is available. If only a standalone file is available, skip this command and report `manual-only` mode.

```bash
python3 <this-skill>/scripts/score.py <target-skill-dir> \
  --json /tmp/skill-evaluation.json
```

The scorer is stdlib only. It emits:
- JSON scorecard: `total`, `grade`, `categories`, `evidence`, `findings`, and ROI-ranked `actions`.
- Markdown summary when called with `--markdown`.

4. Refine the score with manual review using `references/rubric.md`.
   - Keep automatic evidence unless it is clearly wrong.
   - Use manual judgment for workflow quality, trigger overlap, validation integrity, and output fit.
   - Record both the automatic baseline score and the final manual adjusted score.
   - Add adjustment rationale when the manual score differs by 5+ points, changes a grade band, or the automatic baseline is 95+.
5. Validate against negative and counterexample prompts without asking the user unless required context is missing.
   - Identify a similar request that should *not* trigger this skill.
   - Identify a weak skill that could still score well automatically, and whether manual review catches it.
   - Identify a strong skill that could score poorly automatically, and whether evidence justifies an adjustment.
6. Self-evaluate the evaluation before reporting.
   - Check for evaluator blind spots: over-rewarding well-formatted text, under-weighting real-world execution, ignoring adjacent-skill overlap, trusting scripts without inspecting fit, or mistaking verbosity for rigor.
   - Re-read the top finding and top score adjustment as if defending them to the skill author.
7. Report findings in priority order with evidence and concrete fixes.
8. If the user wants implementation, patch the skill directly and re-run the scorer.

## Automatic vs Manual Scoring

Treat `scripts/score.py` as an evidence baseline, not a final oracle.

Automatic checks:
- frontmatter `name` / `description`
- description length and trigger cue coverage
- workflow heading and ordered steps
- referenced files that do not exist
- scripts/references/assets inventory
- executable bit on `.py` / `.sh` scripts
- unwanted auxiliary docs such as `README.md` or `CHANGELOG.md`
- output format and validation cue presence

Manual checks:
- whether the description overlaps too much with other available skills
- whether the workflow is actually executable for realistic requests
- whether bundled scripts solve the right problem
- whether validation evidence is strong enough
- whether the report is useful for the user's decision

Always report:
- Auto baseline score and grade from `scripts/score.py` when available.
- Manual adjusted score and grade.
- Adjustment rationale when the scores differ by 5+ points, cross a grade boundary, or the auto baseline is 95+.

If no manual adjustment is needed, say why the automatic evidence is sufficient. When auto baseline is 95+, actively look for false confidence from formatting, keyword stuffing, shallow validation language, or missing negative boundaries.

## Evaluation Focus

Judge whether an AI agent can reliably decide when to use the skill, load the right amount of context, execute the procedure, handle failures, and verify the result.

High-signal issues include:

- Trigger description is too vague, too narrow, or overlaps heavily with another skill.
- `SKILL.md` explains background instead of giving executable workflow.
- Important instructions are hidden in deep references or duplicated across files.
- Scripts are promised but missing, non-executable, undocumented, or fragile.
- Validation steps are absent, impossible, or rely on visual claims without inspection.
- The skill encourages leaking answer keys into subagent validation.
- The output format is undefined, verbose, or mismatched to the user's likely request.
- The skill has no negative trigger boundaries or counterexamples for adjacent tasks.

## Boundary Checks

- Use this skill for evaluation evidence, scoring, findings, and recommended actions.
- Prefer `skill-improver` when the user's primary request is to fix, upgrade, refactor, or patch a skill.
- Prefer `skill-creator` when the user's primary request is to create a new skill.
- Prefer ordinary code-review skills when the artifact under review is application code rather than a skill.

Do not over-penalize:

- A small skill with no scripts if text instructions are sufficient.
- Missing examples when the workflow is obvious.
- A narrow trigger if the skill is intentionally specialized.

## Output Format

Use this structure unless the user asks for a different format:

```markdown
**Score**
Auto baseline: <auto-total>/100 - <auto-grade>
Manual adjusted: <manual-total>/100 - <manual-grade>
Adjustment: <none, or rationale for 5+ point/grade-band/high-auto change>
Mode: deterministic baseline + manual review

**Findings**
1. [P1/P2/P3] <issue>
   Evidence: <file/path:line or quoted short phrase>
   Fix: <specific change>

**Rubric Breakdown**
- Trigger accuracy: <score>/<points>
- Workflow executability: <score>/<points>
- Progressive disclosure: <score>/<points>
- Resource design: <score>/<points>
- Validation integrity: <score>/<points>
- Maintainability: <score>/<points>
- Output usefulness: <score>/<points>

**Recommended Patch Plan**
1. [<Effort>, priority <score>] <highest ROI edit>
2. [<Effort>, priority <score>] <next edit>
3. [<Effort>, priority <score>] <optional edit>
```

Keep the report concise. Prefer 3-7 findings. If the skill is already strong, say so and focus on residual risk.

## JSON Scorecard

When the user wants repeatable scoring or comparison across skills, produce or preserve JSON in this shape:

```json
{
  "meta": {
    "skill": "skill-name",
    "path": "/abs/path/to/skill",
    "score_mode": "auto baseline + manual adjusted score",
    "auto_total": 84,
    "manual_total": 80,
    "adjustment_rationale": "Manual review reduced validation integrity because checks are named but not executable."
  },
  "total": 80,
  "grade": "Strong",
  "categories": {
    "trigger_accuracy": {
      "score": 18,
      "max": 20,
      "mode": "auto",
      "evidence": {}
    }
  },
  "findings": [],
  "actions": []
}
```

When a manual adjustment exists, `total` and `grade` reflect the manual adjusted score. Preserve the deterministic baseline in `meta.auto_total`.

## ROI Actions

Rank recommended fixes by expected user impact per effort.

- Effort: `S` (<1h), `M` (1-4h), `L` (4h+)
- Impact score: 1-10
- Priority: `impact_score / effort_hours`

Prefer fixes that improve trigger reliability, executable workflow, or validation before polish.

## Dashboard Pattern

For a single skill review, Markdown is enough. For comparing many skills in a repo, use the JSON scorecards to build a lightweight HTML dashboard:

- score hero: average score, grade distribution, weakest category
- skill table: skill name, total score, grade, top finding, top ROI action
- category heatmap: trigger, workflow, disclosure, resources, validation, maintainability, output
- action list: top repo-wide fixes sorted by priority

Use an existing template if one is present. Do not invent decorative visuals; keep it a technical dashboard.

## Severity

- P1: The skill will often fail, mis-trigger, or produce misleading results.
- P2: The skill works but wastes context, misses validation, or has ambiguous steps.
- P3: Polish, maintainability, examples, or optional metadata improvements.

## Grades

- 90-100: Production-ready
- 80-89: Strong
- 70-79: Usable with targeted fixes
- 60-69: Risky
- <60: Needs redesign

## Common Pitfalls

- Do not treat a skill as bad just because it has no scripts. Text-only skills are fine when the workflow is judgment-heavy.
- Do not reward long background explanations. Evaluate whether the loaded context helps execution.
- Do not score only the trigger description. A skill can trigger well and still fail at execution or validation.
- Do not require examples for every small skill. Require examples when the workflow has fragile decisions.
- Do not leak the intended answer into subagent validation. Validation must test whether the skill works from task-local context.
- Do not turn a single skill review into a full repo dashboard unless the user asks for comparison or portfolio-level reporting.
- Do not let a high automatic score skip manual skepticism. High scores need stronger counterexample checks, not less review.
- Do not take primary ownership of skill editing when a dedicated improver workflow is available; provide the evaluation input for that workflow.
- Do not evaluate ordinary code quality, feature design, or skill creation advice unless the artifact under review is a skill or skill-evaluation process.

## References

- `references/rubric.md` - scoring rubric and review prompts.
- `scripts/score.py` - deterministic baseline scorer and JSON scorecard generator.
