# Skill Evaluation Rubric

Total: 100 points.

Use this rubric after running `scripts/score.py` when possible. The script provides an automatic baseline and evidence inventory; the reviewer is responsible for adjusting subjective categories. Each category below identifies what can be checked automatically and what needs manual judgment.

Always preserve the automatic baseline separately from the manual adjusted score. Add adjustment rationale when manual review changes the total by 5+ points, crosses a grade band, or when the automatic baseline is 95+.

Before finalizing, run a brief meta-evaluation:
- What blind spot could make this review too generous?
- What blind spot could make this review too harsh?
- Did formatting, keywords, or script output crowd out evidence that an agent can execute the skill?
- Did the review distinguish skill evaluation from skill creation advice or ordinary code review?

## 1. Trigger Accuracy - 20

- 18-20: Description clearly names task, artifacts, synonyms, and boundaries. It triggers when needed without swallowing unrelated work.
- 14-17: Mostly clear, with minor missing synonyms or boundary ambiguity.
- 8-13: Usable but broad, narrow, or overlapping enough to cause missed or false triggers.
- 0-7: Vague, generic, or misleading.

Review prompts:
- Would a model know to use this skill from metadata alone?
- Does the description include the important user phrases and artifact names?
- Does it avoid claiming unrelated domains?
- What adjacent request should not trigger this skill?
- Would the description falsely trigger for creating a new skill, general code review, docs editing, or feature implementation?

Automatic evidence:
- frontmatter has `name` and `description`
- description length
- description mentions relevant artifacts and task verbs

Manual evidence:
- overlap with other installed skills
- missed synonyms specific to the user's environment
- overly broad phrasing that would swallow adjacent tasks
- explicit negative boundaries or counterexamples for adjacent work

## 2. Workflow Executability - 20

- 18-20: Steps are ordered, concrete, and usable in a real workspace.
- 14-17: Mostly executable, with minor assumptions or missing edge cases.
- 8-13: Procedure is understandable but leaves important decisions implicit.
- 0-7: Mostly conceptual, not operational.

Review prompts:
- Can an agent complete the task without inventing a process?
- Are commands, paths, and decision points specific enough?
- Are failure modes and fallback behavior addressed?
- What realistic request would make these steps break or become ambiguous?

Automatic evidence:
- workflow/process/steps section exists
- ordered steps are present
- bundled scripts are referenced from the workflow

Manual evidence:
- whether the procedure handles realistic ambiguity
- whether fallback behavior is safe
- whether commands are correct for the target environment

## 3. Progressive Disclosure - 15

- 14-15: `SKILL.md` is lean; details live in clearly linked references loaded only when needed.
- 10-13: Good size and organization, with minor duplication or extra context.
- 5-9: Too much detail in the main file or important details buried in references.
- 0-4: Context-heavy, deeply nested, or hard to navigate.

Review prompts:
- Is the always-loaded body worth its token cost?
- Are reference files one hop away and clearly named?
- Is information duplicated across files?
- Could a concise but incomplete skill score too well here because it is short?

Automatic evidence:
- `SKILL.md` body line count
- linked reference paths
- broken references

Manual evidence:
- whether details belong in references or the main workflow
- whether references are loaded only when needed

## 4. Resource Design - 15

- 14-15: Scripts/assets/references are necessary, named clearly, and connected to workflow.
- 10-13: Resources are useful but lightly documented or slightly redundant.
- 5-9: Resources exist but are disconnected, fragile, or too broad.
- 0-4: Missing required resources or cluttered with unrelated files.

Review prompts:
- Are deterministic or fragile operations handled by scripts?
- Are scripts runnable with clear inputs and outputs?
- Are assets/templates reused rather than recreated?
- Do bundled scripts measure the real quality claim, or only easy proxies?

Automatic evidence:
- scripts/references/assets inventory
- executable bit on script files
- resource paths mentioned from `SKILL.md`

Manual evidence:
- whether scripts are necessary
- whether assets/templates match the promised output
- whether resource naming makes intent clear

## 5. Validation Integrity - 15

- 14-15: Verification is explicit, evidence-based, and protects against answer leakage in evaluations.
- 10-13: Has reasonable validation with small gaps.
- 5-9: Mentions validation but lacks concrete checks.
- 0-4: No credible validation path.

Review prompts:
- What proves the skill worked?
- Are visual, generated, or external artifacts inspected rather than assumed?
- If subagents are used, is the validation independent?
- What negative or counterexample prompt would expose a false positive?
- What strong skill might look weak to the automatic scorer, and does manual evidence justify restoring points?
- What weak skill might look strong to the automatic scorer, and does manual evidence justify subtracting points?

Automatic evidence:
- validation/check/test/evidence terms in `SKILL.md`
- explicit output format or verification section

Manual evidence:
- whether checks are sufficient for the artifact type
- whether subagent validation avoids leaking expected answers
- whether visual or generated outputs require rendering/inspection

## 6. Maintainability - 10

- 9-10: Easy to update, scoped, and consistent with local style.
- 7-8: Mostly maintainable with minor organization issues.
- 4-6: Hard to update safely or overly coupled to volatile details.
- 0-3: Brittle or confusing.

Review prompts:
- Can a future editor update triggers, commands, or resources safely?
- Are volatile facts isolated?
- Does the skill avoid unnecessary docs and generated clutter?
- Is there one obvious place to update scoring, trigger boundaries, and validation guidance?

Automatic evidence:
- unwanted auxiliary docs
- hidden junk files
- top-level file inventory

Manual evidence:
- consistency with local skill style
- whether volatile facts are isolated in references or scripts
- whether future updates have one obvious place to land

## 7. Output Usefulness - 5

- 5: Final outputs are concise, actionable, and fit the user's likely decision.
- 3-4: Useful but too verbose, underspecified, or inconsistently structured.
- 1-2: Vague recommendations or no prioritization.
- 0: No useful output guidance.

## Priority Heuristic

Rank findings by user impact:

1. False trigger or missed trigger risk.
2. Broken or non-executable workflow.
3. Missing validation for promised outputs.
4. Context bloat or poor progressive disclosure.
5. Maintainability and polish.

## Score Reconciliation

Use two numbers when a deterministic baseline is available:

- Auto baseline: exact scorer output.
- Manual adjusted: reviewer judgment after applying this rubric.

Required rationale:

- Manual total differs from auto by 5+ points.
- Manual total crosses a grade band.
- Auto baseline is 95+.
- Any category changes by 3+ points.

Rationale should name the evidence and the rubric category, for example: "Auto baseline over-rewarded validation keywords; manual score subtracts 4 in Validation Integrity because no verification command or independent counterexample prompt is defined."

## JSON Scorecard Fields

When preserving evaluation data, use:

- `meta`: skill name, absolute path, score mode
- `total`: 0-100 aggregate
- `grade`: one of the grade labels in `SKILL.md`
- `categories`: map of category id to `score`, `max`, `mode`, and `evidence`
- `findings`: priority, category, issue, evidence, fix
- `actions`: title, category, effort, effort_hours, impact, impact_score, priority

## Dashboard Inputs

For multi-skill dashboards, aggregate these fields:

- Total score and grade by skill
- Category score ratios for heatmaps
- Count of P1/P2/P3 findings
- Top ROI action per skill
- Repeated findings across skills
