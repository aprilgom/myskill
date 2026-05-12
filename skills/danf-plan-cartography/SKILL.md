---
name: danf-plan-cartography
description: Use when asked whether a DANN-FF/danf research or implementation plan is reasonable for the project's interneuron-as-negative-generator goal from neuroscience and ML expert viewpoints before execution.
---

# DANF Plan Cartography

Evaluate whether a DANN-FF/danf research or implementation plan is reasonable
for the project's stated goal from neuroscience and ML expert viewpoints. This
is stronger than generic execution-readiness review: it asks whether the plan is
aligned with `interneuron as negative generator`, defensible to the relevant
experts, falsifiable, implementable, and likely to produce interpretable
evidence.

Use this when the user wants a danf/DANN-FF plan judged by roles such as
"20-year neuroscientist and 20-year ML expert". Do not execute the plan.

## Workflow

1. Identify the target plan and confirm the relevant danf project goal. Default
   to `interneuron as negative generator` unless nearby handoff docs clearly
   say the user is evaluating a diagnostic control or different phase.
2. Use two default expert lenses unless the user asks otherwise:
   computational neuroscience and machine learning.
3. Read the plan and nearby context needed to judge it: goal docs, prior
   results, architecture notes, run logs, issue/PR links, verification commands,
   safety rules, and known non-goals.
4. Read `references/expert-plan-rubric.md` for detailed scoring criteria.
5. Score the plan on the 100-point rubric. Cite evidence. Treat section
   presence as weak evidence.
6. Produce separate expert passes, then reconcile them:
   - where experts agree
   - where they disagree
   - what would change their judgment
   - what must be fixed before execution
7. Return a short report in the user's language with score, verdict, category
   scores, expert findings, risks, and ROI-ranked edits.

## Expert Model

A strong expert plan reviewer asks:

- What project goal or research direction is this plan supposed to advance?
- Does the plan protect explicit non-goals and safety boundaries?
- Would each named expert consider the core mechanism plausible in their field?
- What observation would falsify the plan's central claim?
- Are success and stop gates quantitative enough to prevent wishful
  interpretation?
- Are contracts concrete: APIs, tensors, gradients, schemas, ownership,
  artifacts, metrics, interfaces, rollback behavior?
- Are baselines, controls, ablations, leakage checks, and comparison windows
  sufficient for the claim?
- Is the staging order safe, reversible, and informative if it fails?
- Does the plan confuse scientific framing, engineering mechanism, and
  narrative motivation?

For scientific plans, prioritize falsifiability, controls, confounds, and
interpretation discipline. For engineering plans, prioritize contracts,
sequencing, verification, and rollback. Hybrid plans need both.

## Rubric Summary

Total: 100 points. Detailed criteria are in
`references/expert-plan-rubric.md`.

| Cat | Category | Points |
|-----|----------|--------|
| A | Project Goal Fit & Non-Goal Protection | 16 |
| B | Expert Plausibility & Cross-Disciplinary Coherence | 14 |
| C | Decision Clarity & Scope Boundaries | 10 |
| D | Evidence Grounding & Prior State | 10 |
| E | Falsifiability & Quantitative Gates | 14 |
| F | Technical Contract Specificity | 12 |
| G | Validation Design, Controls & Confounds | 12 |
| H | Staging, Feasibility & Safety | 7 |
| I | Output Discipline & Handoff Quality | 5 |

Grades:

- 85-100: Expert-Ready
- 70-84: Reasonable With Revisions
- 55-69: Interesting But Under-Specified
- 35-54: Misaligned Or High-Risk
- 0-34: Not Reasonable For The Goal

## Dual-Expert Mode

Evaluate each role separately before writing the integrated verdict.

Neuroscience expert pass:

- Does the plan advance `interneuron as negative generator` rather than merely
  adding another supervised wrong-label objective?
- Is the biological/circuit interpretation plausible and not overclaimed?
- Does it distinguish diagnostic scaffolds from proposed mechanisms?
- Would a negative result be interpretable biologically?

ML expert pass:

- Is the objective operationally testable?
- Are baselines, controls, leakage checks, ablations, and promotion gates
  sufficient?
- Does it separate readout gains from true objective or energy-geometry
  progress?
- Are tensor, gradient, data, and metric contracts clear enough to implement?

Reconciliation:

- List shared approvals, shared blockers, and expert disagreements.
- A plan is not "reasonable for the project goal" if either core expert finds
  the central mechanism misaligned with the stated goal.

## Output Rules

- Cite plan sections, file paths, commands, artifacts, metrics, baselines, or
  quoted snippets as evidence.
- Do not invent missing thresholds, baselines, owners, controls, data, compute,
  run results, biological mechanisms, or implementation contracts.
- Penalize qualitative gates when numeric or artifact-based gates are necessary.
- Mark extraction gaps separately from missing evidence.
- Manual-review-only judgments must remain marked as manual judgment.
- A low score must lead to specific repairs, not generic advice.

## Output Format

```markdown
**Score**
<total>/100 - <grade>
Verdict: <Reasonable / Reasonable with revisions / Misaligned / Not ready>
Mode: evidence review + dual-expert judgment

**Category Scores**
- A. <name>: <score>/<points> - <short rationale>

**Expert Passes**
- <Expert 1>: <judgment with evidence>
- <Expert 2>: <judgment with evidence>

**Reconciliation**
- Agreement: <shared finding>
- Disagreement: <if any>
- Blocking fixes: <must-fix before execution>

**Top Risks**
- [<severity>] <risk> - <why it matters>

**Top Actions**
1. [<effort>, priority <0-100>] <specific repair> - improves <category>

**Manual Review Notes**
- <judgment or unknown that file evidence cannot decide>
```

## Common Pitfalls

- Treating generic execution readiness as goal fit.
- Letting a plan score well despite violating the project's stated research
  direction or non-goals.
- Scoring keyword or section presence as readiness.
- Letting "evaluate improvement" count as a measurable success gate.
- Missing leakage, confounds, and baseline fairness.
- Treating narrative scientific motivation as mechanistic proof.
- Ignoring tensor, gradient, schema, data, or API contracts.
- Approving plans with too many simultaneous moving parts.
- Failing to distinguish experiment failure from implementation failure.

## Files

- `references/expert-plan-rubric.md` - full rubric, expert-lens guidance,
  manual review boundary, red flags, and ROI action guidance.
