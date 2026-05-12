---
name: improve-mission
description: Improve mission clarity and alignment for a project, product, startup, nonprofit, team, community, README, pitch packet, strategy memo, roadmap, or documentation set. Use when asked to improve a mission, sharpen purpose, fix mission drift, align product narrative, strengthen a north star, rewrite mission materials, or turn mission-cartography findings into concrete documentation or strategy improvements. Requires mission-cartography as the baseline; use build-mission for drafting mission options when needed.
---

# Improve Mission

This skill improves mission clarity and alignment while keeping assessment and editing separate. The baseline evaluator is always `$mission-cartography`; this skill turns that evaluation into concrete mission, documentation, roadmap, positioning, or strategy improvements.

The goal is not to make prettier copy. The goal is to make the mission specific, evidence-backed, aligned with the product or work, and useful for real trade-offs.

## Core Rule

Always run or obtain a baseline mission-cartography evaluation before editing.

- Evaluation phase: uses `$mission-cartography` against the target and produces score data, category breakdown, evidence paths, findings, extraction gaps, and ROI-ranked alignment actions. It does not edit files.
- Improvement phase: uses the evaluation result to patch or draft mission improvements. It should use `$build-mission` patterns when a new or rewritten mission statement is needed.
- Verification phase: reruns `$mission-cartography` after improvements and compares before/after evidence, score, and remaining gaps.

If the user only wants advice and no file edits, still separate the phases: produce a baseline read first, then recommendations.

## Workflow

1. Identify the target.
   - If the user gives a path, use it.
   - If no path is given, use the current working directory.
   - If the request names specific materials, limit edits to those files unless the user asks for broader project changes.

2. Capture baseline mission-cartography.

```bash
python3 <mission-cartography-dir>/scripts/score.py <target-path> \
  --json /tmp/improve-mission-before.json --markdown
python3 <mission-cartography-dir>/scripts/render_dashboard.py /tmp/improve-mission-before.json \
  --template <mission-cartography-dir>/assets/template.html \
  --out /tmp/improve-mission-before.html
```

3. Review the baseline before editing.
   - Prioritize low-scoring categories by weight and decision impact.
   - Read `references/improvement-patterns.md` for concrete patch patterns.
   - Do not rewrite a mission from vibes; every improvement should address an evidence gap or alignment risk.

4. Choose the improvement mode.
   - Patch target files directly when they are repo documents, web copy, strategy docs, roadmap docs, or app content.
   - Draft a separate mission brief when the source material should not be edited, is binary, or the user asks for recommendations.
   - Use `templates/mission-improvement-brief.md` for separate deliverables.

5. Improve in priority order.
   - Mission clarity and specificity.
   - Audience and stakeholder definition.
   - Problem evidence and urgency.
   - Product and roadmap alignment.
   - Strategic trade-off power.
   - Measurement and feedback loops.
   - Narrative consistency across artifacts.

6. Rerun mission-cartography after improvements.
   - Save after-score artifacts separately, for example `/tmp/improve-mission-after.json` and `/tmp/improve-mission-after.html`.
   - Compare category shifts, evidence paths, actions, extraction gaps, and manual-review checks.

7. Verify integrity.
   - Run relevant repository checks for edited files when available.
   - Confirm generated JSON and HTML artifacts are non-empty.
   - Confirm generated HTML contains no unresolved template tokens.
   - Confirm mission claims remain evidence-backed and assumptions are marked.

8. Report in the user's language.
   - Include before/after score, changed files, highest-impact improvements, remaining mission risks, and artifact paths.

## Evaluation Prompt

Use this prompt when delegating or structuring the evaluation phase:

```text
Evaluate the target with $mission-cartography. Run the scorer and dashboard renderer if available. Produce JSON/Markdown with score, category breakdown, evidence paths, findings, extraction gaps, and ROI-ranked mission alignment actions. Do not edit files. Do not invent users, customer research, metrics, founder intent, strategy, or product plans. Mark unknowns explicitly.
```

## Improvement Prompt

Use this prompt when delegating or structuring the improvement phase:

```text
Improve the target's mission clarity and alignment using the supplied mission-cartography evaluation. Patch only the approved target files or draft a separate mission brief if editing is not appropriate. Do not redo the baseline evaluation from scratch. Prioritize audience clarity, problem evidence, mission specificity, product and roadmap alignment, trade-off power, mission metrics, and narrative consistency. Use $build-mission patterns when drafting new mission options. Preserve user changes. List changed files and any evaluation findings intentionally left unresolved.
```

## Improvement Priorities

Apply improvements in this order:

1. Mission clarity: write or refine one mission sentence with audience, problem, intended change, and scope.
2. Audience clarity: name the primary user, beneficiary, buyer, stakeholder, or community; avoid “everyone” unless evidence supports it.
3. Problem evidence: connect the mission to pain, urgency, research, observed behavior, operational cost, risk, or user quotes.
4. Product alignment: map current capabilities, workflows, roadmap items, or scope boundaries to mission outcomes.
5. Trade-off power: add focus principles, “we will not” boundaries, decision criteria, or sequencing rules.
6. Measurement: define mission progress metrics, success signals, feedback loops, or learning checkpoints.
7. Narrative consistency: consolidate conflicting mission-like statements across README, pitch, website, roadmap, and strategy docs.

## Editing Guardrails

- Do not invent target users, interviews, metrics, customer proof, founder intent, roadmap items, or market facts.
- Mark assumptions as assumptions.
- Keep the mission short and concrete; supporting copy can carry detail.
- Prefer evidence-linked language over motivational language.
- Do not erase a distinctive product voice unless it blocks clarity.
- Preserve unrelated user edits and local formatting conventions.
- If evidence is too thin to justify a final mission, produce provisional options and the smallest research/actions needed to finalize.

## Validation Commands

Use the installed mission-cartography skill directory when available:

```bash
python3 -m py_compile <mission-cartography-dir>/scripts/score.py \
  <mission-cartography-dir>/scripts/render_dashboard.py \
  <mission-cartography-dir>/scripts/self_test.py
python3 <mission-cartography-dir>/scripts/self_test.py
python3 <mission-cartography-dir>/scripts/score.py <target-path> \
  --json /tmp/improve-mission-score.json --markdown
python3 <mission-cartography-dir>/scripts/render_dashboard.py /tmp/improve-mission-score.json \
  --template <mission-cartography-dir>/assets/template.html \
  --out /tmp/improve-mission-map.html
test -s /tmp/improve-mission-score.json
test -s /tmp/improve-mission-map.html
```

Then verify `/tmp/improve-mission-map.html` contains no unresolved template tokens.

## Output Format

```markdown
**Before/After**
- Before: <score>/100 - <grade>
- After: <score>/100 - <grade>

**Changed Files**
- <path>

**Mission Improvements**
1. <highest-impact improvement and evidence basis>
2. <second improvement>
3. <third improvement>

**Recommended Mission**
<mission sentence, if changed or drafted>

**Remaining Risks**
- <manual-review/evidence gap or "None found">

**Artifacts**
- <before score/dashboard>
- <after score/dashboard>

**Verification**
- <command> - <result>
```

## Files

- `references/improvement-patterns.md` - category-specific mission improvement patterns
- `templates/mission-improvement-brief.md` - standalone brief for advice-only or non-editable targets
