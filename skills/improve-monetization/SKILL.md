---
name: improve-monetization
description: Improve monetization readiness for a project, product, repo, README, pricing page, pitch packet, or business memo. Use when asked to improve monetization, revenue readiness, buyer clarity, pricing evidence, willingness-to-pay proof, revenue experiments, or monetization materials. Requires monetization-cartography as the baseline and separate evaluation and improvement agents.
---

# Improve Monetization

This skill improves monetization readiness while keeping assessment and editing separate. The baseline evaluator is always `$monetization-cartography`; this skill turns that evaluation into concrete project, product, documentation, pricing, or experiment improvements.

Do not treat this as investment, valuation, legal, or tax advice. The output is monetization evidence improvement and revenue experiment design.

## Core Rule

Use separate agents for evaluation and improvement.

- Evaluation agent: runs `$monetization-cartography`, verifies evidence, and produces score data, dashboard, findings, and ROI-ranked revenue actions. It must not edit target files.
- Improvement agent: uses the evaluation result as input and patches or drafts improvements. It must not redo the baseline from scratch unless the evaluation artifact is missing or invalid.
- Main agent: coordinates scope, preserves user changes, verifies before/after, and reports what changed.

If subagents are unavailable, stop and tell the user this skill requires separate agents for evaluation and improvement. Do not collapse the work into one agent.

## Workflow

1. Identify the target.
   - If the user gives a path, use it.
   - If no path is given, use the current working directory.
   - If the request names specific materials, limit edits to those files unless the user asks for broader project changes.
2. Start the evaluation agent.
   - The eval agent uses `$monetization-cartography` against the target.
   - Save outputs in the normal monetization-cartography output location unless the user gives another path.
   - Require `monetization-score.json` and, when feasible, `monetization-map.html`.
3. Review the evaluation artifact before editing.
   - Prioritize low scoring categories, missing proof signals, and top ROI revenue actions.
   - Prefer concrete buyer, pain, price, proof, conversion, and unit economics gaps over broad business advice.
   - Do not invent customers, revenue, price points, conversion rates, or margins.
4. Start the improvement agent.
   - Pass the evaluation output path(s), target path, requested scope, and any user constraints.
   - Patch target files directly when they are repo documents or app content.
   - Draft separate recommendations only when the source material should not be edited, is binary, or the user asked for advice rather than code/docs changes.
5. Rerun the evaluation agent after improvements.
   - Produce after-score artifacts separate from the baseline when possible, for example `/tmp/improve-monetization-after.json`.
   - Compare before and after scores, category shifts, and remaining evidence gaps.
6. Verify integrity.
   - Run relevant repository checks for edited files when available.
   - Confirm generated JSON and HTML artifacts are non-empty.
   - Confirm no unresolved dashboard placeholders remain.
7. Report in the user's language.
   - Include before/after score, changed files, highest-impact improvements, remaining monetization risks, and artifact paths.

## Evaluation Agent Prompt

Use this prompt when delegating evaluation:

```text
Evaluate the target with $monetization-cartography. Run the scorer and dashboard renderer if available. Produce JSON/Markdown with score, category breakdown, evidence paths, findings, extraction gaps, and ROI-ranked revenue actions. Do not edit files. Do not invent customers, revenue, prices, conversion rates, or margins. Mark unknowns explicitly.
```

## Improvement Agent Prompt

Use this prompt when delegating improvement:

```text
Improve the target's monetization readiness using the supplied monetization-cartography evaluation. Patch only the approved target files. Do not redo the baseline evaluation from scratch. Prioritize buyer clarity, painful use cases, pricing/package evidence, revenue proof, conversion path, unit economics, and next revenue experiments. Preserve user changes. List changed files and any evaluation findings intentionally left unresolved.
```

## Improvement Priorities

Apply improvements in this order:

1. Buyer clarity: ICP, buyer role, segment, job-to-be-done, and excluded non-buyers.
2. Pain and willingness to pay: urgent pain, budget owner, ROI, switching trigger, or paid pilot rationale.
3. Pricing and packaging: explicit packages, price anchors, billing unit, limits, and upgrade path.
4. Revenue proof: paid customers, pilots, LOIs, contracts, retention, conversion, or direct user interview evidence.
5. Unit economics: cost to serve, gross margin, CAC, LTV, payback, churn, ACV, or assumptions marked as unknown.
6. Distribution path: acquisition channel, sales motion, trial/onboarding, marketplace, partner, or checkout route.
7. Revenue experiments: next tests with owner, metric, success threshold, expected impact, effort, and priority.

## Editing Guardrails

- Keep claims evidence-backed. Mark assumptions as assumptions.
- Prefer adding measurable experiments over generic growth advice.
- Do not fabricate testimonials, customer logos, pricing validation, revenue, or traction.
- Do not drift into VC investability unless the user explicitly asks and a different skill is used.
- Preserve unrelated user edits and avoid broad rewrites of product voice unless necessary for monetization clarity.
- If the target is a codebase, keep product/docs changes consistent with existing architecture and content patterns.

## Validation Commands

Use the installed monetization-cartography skill directory when available:

```bash
python3 -m py_compile <monetization-skill-dir>/scripts/score.py \
  <monetization-skill-dir>/scripts/render_dashboard.py \
  <monetization-skill-dir>/scripts/self_test.py
python3 <monetization-skill-dir>/scripts/self_test.py
python3 <monetization-skill-dir>/scripts/score.py <target-path> --json /tmp/improve-monetization-score.json --markdown
python3 <monetization-skill-dir>/scripts/render_dashboard.py /tmp/improve-monetization-score.json \
  --template <monetization-skill-dir>/assets/template.html \
  --out /tmp/improve-monetization-map.html
test -s /tmp/improve-monetization-score.json
test -s /tmp/improve-monetization-map.html
```

Then verify `/tmp/improve-monetization-map.html` contains no unresolved `{{PLACEHOLDER}}` tokens.

## Output Format

```markdown
**Before/After**
- Before: <score>/100 - <grade>
- After: <score>/100 - <grade>

**Changed Files**
- <path>

**Monetization Improvements**
1. <highest-impact improvement and evidence basis>
2. <second improvement>
3. <third improvement>

**Remaining Risks**
- <unknown buyer/price/revenue/economics gap or "None found">

**Artifacts**
- <before score/dashboard>
- <after score/dashboard>

**Verification**
- <command> - <result>
```
