---
name: cartography-skill-evaluator
description: Evaluate cartography-style Codex/Claude skills for rubric quality, evidence discipline, scanner reliability, JSON score schema, dashboard usefulness, validation integrity, trigger accuracy, and ROI action quality. Use when asked to review, audit, score, benchmark, compare, or improve a cartography skill, cartography SKILL.md, cartography rubric, cartography scorer, or cartography dashboard workflow.
---

# Cartography Skill Evaluator

This skill evaluates skills that produce cartography-style outputs: evidence maps, 100-point scores, dashboards, and prioritized actions. It can produce both a JSON scorecard and a single-file HTML evaluation map.

Use the general `skill-evaluator` for ordinary skills. Use this skill when the target promises cartography, readiness maps, score dashboards, diligence maps, maturity maps, or domain evaluation with evidence and actions.

## Workflow

1. Identify the target skill.
   - If the user provides a path, inspect that folder.
   - If only `SKILL.md` is provided, evaluate the file and note missing folder context.
   - If no target is given, evaluate the most relevant `*-cartography` skill in the current repo, or ask one concise question if ambiguous.

2. Read the minimum necessary files.
   - Always read `SKILL.md`.
   - Read rubric reference files when present.
   - Read `scripts/score.py`, `scripts/render_dashboard.py`, and `scripts/self_test.py` when present because they define the promised cartography behavior.
   - Inspect `assets/template.html` enough to confirm dashboard fields and unresolved placeholders.
   - Read `agents/openai.yaml` if present.

3. Run the baseline scorer when a skill folder is available.

```bash
python3 <this-skill>/scripts/score.py <target-skill-dir> \
  --json /tmp/cartography-skill-evaluation.json --markdown
```

4. Render the cartography skill evaluation map when an HTML artifact is useful.

```bash
python3 <this-skill>/scripts/render_dashboard.py \
  /tmp/cartography-skill-evaluation.json \
  --template <this-skill>/assets/template.html \
  --out /tmp/cartography-skill-map.html
```

5. Manually refine the score using `references/rubric.md`.
   - Treat the script as an evidence baseline, not an oracle.
   - Manual review is required for expert-model fit, rubric judgment, scanner/domain fit, dashboard usefulness, and action quality.
   - Check whether the target skill models what a competent domain expert would inspect first, which failure modes matter most, and which scanner signals are valid or weak proxies.

6. If scripts exist, run the target skill's own validation when practical.
   - Prefer bundled `self_test.py`.
   - Then run scorer + renderer on a tiny fixture if the target skill documents that path.
   - If validation is impossible, report exactly why.

7. Report concise findings.
   - Lead with score and grade.
   - List 3-7 findings by severity.
   - Include evidence paths and concrete fixes.
   - End with the highest ROI patch plan and generated artifact paths.

8. If the user asks for implementation, patch the target skill and rerun this evaluation.

## Evaluation Categories

Use this 100-point model:

| Cat | Name | Points |
|-----|------|--------|
| A | Cartography Contract & Trigger Fit | 15 |
| B | Rubric Design Quality | 20 |
| C | Evidence Collection & Scanner Fit | 15 |
| D | JSON Schema & Output Stability | 10 |
| E | Dashboard Decision Usefulness | 10 |
| F | Validation Integrity | 15 |
| G | ROI Action Quality | 10 |
| H | Progressive Disclosure & Maintainability | 5 |

Read `references/rubric.md` when scoring subjective categories or resolving borderline cases.

## What Good Looks Like

A strong cartography skill:

- States what target it evaluates and what decision the score supports.
- Models the domain expert's evaluation frame before scoring: priorities, failure modes, disqualifiers, strong evidence, weak proxies, and manual judgment boundaries.
- Uses a 100-point rubric with non-overlapping, weighted categories that reflect domain-expert priorities rather than generic quality criteria.
- Separates scanner evidence from manual judgment.
- Emits deterministic JSON with score, categories, evidence, risks, actions, gaps, and metadata.
- Renders a single-file dashboard that exposes evidence and gaps, not just a polished score.
- Includes validation that exercises scorer, renderer, fixture data, and placeholder checks.
- Produces ROI-ranked actions that directly address high-weight gaps and severe risks.

## Automatic vs Manual Review

Automatic checks are useful for:

- frontmatter and trigger cues
- presence of rubric, scripts, dashboard template, self-test
- 100-point category declarations
- JSON/output/validation language
- referenced file existence
- placeholder and TODO leaks

Manual review is required for:

- whether the rubric reflects a credible domain expert decision model
- whether rubric categories are independent and decision-relevant
- whether category weights match expert priority rather than ease of automated detection
- whether scanner signals match the domain
- whether scanner-detected signals are valid proxies or weak signals that should become gaps/manual-review notes
- whether action recommendations are specific enough
- whether dashboard design helps a real decision
- whether validation would catch misleading scores

## Output Format

Use this final shape unless the user asks otherwise:

```markdown
**Score**
<total>/100 - <grade>
Mode: heuristic baseline + manual cartography review

**Findings**
1. [P1/P2/P3] <issue>
   Evidence: <file/path:line or short quote>
   Fix: <specific change>

**Rubric Breakdown**
- Cartography contract & trigger fit: <score>/15
- Rubric design quality: <score>/20
- Evidence collection & scanner fit: <score>/15
- JSON schema & output stability: <score>/10
- Dashboard decision usefulness: <score>/10
- Validation integrity: <score>/15
- ROI action quality: <score>/10
- Progressive disclosure & maintainability: <score>/5

**Recommended Patch Plan**
1. [<Effort>, priority <score>] <highest ROI edit>
2. [<Effort>, priority <score>] <next edit>
3. [<Effort>, priority <score>] <optional edit>

Generated: <cartography-skill-evaluation.json>, <cartography-skill-map.html>
```

## Severity

- P1: The skill can produce misleading scores, cannot run its promised workflow, or mis-triggers often.
- P2: The skill works but has weak rubric design, thin validation, unstable output, or vague actions.
- P3: Metadata, maintainability, examples, or polish improvements.

## Grades

- 90-100: Production cartography skill
- 80-89: Strong with small gaps
- 70-79: Usable with targeted fixes
- 60-69: Risky cartography
- <60: Needs redesign

## Common Pitfalls

- Do not reward a dashboard if it hides weak evidence.
- Do not accept a keyword scanner as sufficient unless the skill explicitly requires manual review.
- Do not treat a tidy 100-point rubric as expert-grade unless it explains domain priorities, failure modes, disqualifiers, and proxy validity.
- Do not reward scanner-friendly criteria when they replace what an expert would actually inspect.
- Do not require scripts for a deliberately lightweight rubric-only cartography skill, but mark the absence as a limitation.
- Do not double-penalize one flaw across many categories; cite the primary affected category.
- Do not turn the review into generic skill evaluation. Focus on cartography-specific reliability.

## Files

- `scripts/score.py` - deterministic baseline scorer for cartography skill folders.
- `scripts/render_dashboard.py` - renders evaluation JSON with `assets/template.html`.
- `assets/template.html` - single-file cartography skill evaluation map template.
- `scripts/self_test.py` - smoke tests for scorer and renderer behavior.
- `references/rubric.md` - detailed scoring guidance and review prompts.
