# DANF Plan Cartography Rubric

Use this reference to score whether a DANN-FF/danf research, implementation,
experiment, technical roadmap, PR, or hybrid science-engineering plan is
reasonable for the project's `interneuron as negative generator` direction from
computational neuroscience and ML expert viewpoints.

## Target And Decision

Target:

```text
a written DANN-FF/danf plan or plan-like artifact that is being considered for
execution
```

Decision supported:

```text
Would a 20-year computational neuroscientist and a 20-year ML expert consider
this plan reasonable for the danf project goal, and what revisions would most
improve its goal fit, execution readiness, and interpretability?
```

This rubric does not score final results. It scores whether executing the plan
is a defensible next move.

## Manual Review Boundary

File evidence can find goals, headings, commands, metrics, baselines,
thresholds, artifacts, controls, phases, risk language, and weak-plan signals.
It cannot fully judge:

- whether a hypothesis is scientifically meaningful
- whether a biological, theoretical, product, or architecture framing is valid
- whether thresholds are stringent enough
- whether controls actually rule out the intended confound
- whether baselines are fair
- whether the actual codebase makes the proposed implementation order safe
- whether the project goal itself is wise

Treat automated or heuristic signals as evidence, not an oracle.

## Grade Bands

- 85-100: Expert-Ready. Relevant experts would likely approve execution with
  normal review.
- 70-84: Reasonable With Revisions. Direction is sound, but targeted fixes
  should be made before execution.
- 55-69: Interesting But Under-Specified. The idea may be valuable, but current
  evidence, gates, contracts, or controls are too weak.
- 35-54: Misaligned Or High-Risk. Execution is likely to produce ambiguous,
  misleading, or goal-misaligned outcomes.
- 0-34: Not Reasonable For The Goal. The plan violates the goal, lacks evidence,
  or is not execution-ready.

## Expert Lens Selection

Default expert roles:

- 20-year computational neuroscientist
- 20-year machine learning expert

Each expert pass should answer:

```text
What would this expert approve?
What would this expert reject or require before execution?
What evidence would change this expert's judgment?
```

## A. Project Goal Fit & Non-Goal Protection - 16 points

Why it matters:
A plan can be executable but still wrong for the project. This category checks
whether the plan advances the stated goal and protects explicit non-goals.

Strong evidence, 13-16:

- States the project goal or research direction and ties the plan to it.
- Names non-goals, diagnostic-only paths, safety boundaries, or forbidden
  shortcuts.
- Explains why this plan is the next rational move given current evidence.
- Defines what claims will not be made after execution.

Partial evidence, 7-12:

- Goal fit is plausible but implicit.
- Non-goals or safety boundaries are mentioned but not operationalized.
- The plan advances an adjacent goal but not clearly the stated goal.

Weak or missing, 0-6:

- No project goal or goal evidence.
- Plan optimizes an adjacent metric while claiming to solve the main goal.
- Violates known non-goals or safety boundaries.

Red flags:

- A plan for `interneuron as negative generator` that makes externally supplied
  wrong labels the main mechanism rather than a diagnostic scaffold.

## B. Expert Plausibility & Cross-Disciplinary Coherence - 14 points

Why it matters:
Hybrid plans fail when one discipline's story is used to decorate another
discipline's mechanism. This category checks whether relevant experts would
find the mechanism plausible and the interpretation disciplined.

Strong evidence, 12-14:

- Names the expert-relevant mechanism and why it is plausible.
- Separates measurement tools from causal mechanisms.
- Identifies where expert views may disagree.
- Avoids overclaiming beyond the evidence available.

Partial evidence, 6-11:

- Mechanism is plausible but not sharply distinguished from a scaffold,
  diagnostic, proxy, or engineering helper.
- Expert-specific risks are mentioned but not tied to gates.

Weak or missing, 0-5:

- Uses domain language as narrative gloss.
- One expert lens would reject the central mechanism as misframed.
- Cross-disciplinary claims cannot be falsified separately.

Red flags:

- Biological, scientific, product, or architecture language that sounds
  plausible but maps to no operational test or circuit/system mechanism.

## C. Decision Clarity & Scope Boundaries - 10 points

Strong evidence, 8-10:

- Names the plan target, intended decision, concrete next state, exclusions,
  and phase boundaries.

Partial evidence, 4-7:

- Has a goal but weak decision framing, exclusions, or phase separation.

Weak or missing, 0-3:

- Broad aspiration with no execution decision or clear endpoint.

Red flags:

- One plan mixes implementation, interpretation, publication framing, and future
  research without boundaries.

## D. Evidence Grounding & Prior State - 10 points

Strong evidence, 8-10:

- Cites prior artifacts, run results, baselines, issues, PRs, logs, architecture
  docs, or code paths.
- Explains how prior findings constrain the new plan.
- Separates confirmed facts from assumptions.

Partial evidence, 4-7:

- Mentions prior work but lacks artifact paths, exact settings, or baseline
  comparisons.

Weak or missing, 0-3:

- No prior state, unsupported claims, or stale evidence.

Red flags:

- "Previous work showed..." without artifact path, settings, or evidence.

## E. Falsifiability & Quantitative Gates - 14 points

Strong evidence, 12-14:

- Defines success, failure, and stop/revise criteria.
- Uses numeric thresholds, artifact-based gates, or explicit pass/fail tests.
- Names baselines and comparison windows.
- States what negative results would mean.

Partial evidence, 6-11:

- Has acceptance criteria but some are qualitative.
- Names metrics but not thresholds.
- Has success criteria but weak failure interpretation.

Weak or missing, 0-5:

- Only says "evaluate", "improve", "see whether", or "avoid degradation".
- No thresholds, baselines, stop rules, or negative outcome interpretation.

Red flags:

- "Materially worse", "near", "stable", "meaningful", or "good enough" without
  a predeclared band when numeric evidence is available.

## F. Technical Contract Specificity - 12 points

Strong evidence, 10-12:

- Specifies relevant APIs, data schemas, tensor shapes, gradient flow, config
  knobs, metrics, state ownership, artifacts, side effects, and invariants.
- Defines safe defaults and no-op behavior.
- Identifies files/modules likely to change and their responsibilities.

Partial evidence, 5-9:

- Lists files or components but not exact behavior.
- Specifies concepts but omits shapes, detach rules, schemas, or side effects.

Weak or missing, 0-4:

- No interface or data contract.
- Key mechanism is described only in prose.
- Implementation can be interpreted multiple incompatible ways.

Red flags:

- New objective, API, migration, tensor operation, or data flow with no contract.

## G. Validation Design, Controls & Confounds - 12 points

Strong evidence, 10-12:

- Names baselines, controls, ablations, negative controls, regression tests, and
  comparison fairness criteria.
- Addresses leakage, train/test isolation, confounds, seed variance, and
  failure signatures where relevant.
- Defines which control falsifies which interpretation.

Partial evidence, 5-9:

- Includes tests or controls but not enough to isolate causes.
- Mentions ablations without required variants.
- Has baselines but weak comparability details.

Weak or missing, 0-4:

- Only validates the happy path.
- No leakage/confound handling for research or data-heavy work.
- No baseline or regression comparison.

Red flags:

- A plan can "succeed" by label leakage, shortcut learning, migration side
  effect, benchmark overfit, or readout-only improvement.

## H. Staging, Feasibility & Safety - 7 points

Strong evidence, 6-7:

- Breaks work into stages with dependencies and gates.
- Starts with diagnostics or no-op behavior before active behavior changes.
- States resource constraints, environment assumptions, and safety boundaries.
- Includes rollback, supersede, or stop paths.

Partial evidence, 3-5:

- Has phases but weak dependencies, resource constraints, or gates.

Weak or missing, 0-2:

- Big-bang execution, unavailable resources, unsafe parallelism, or no stop
  point.

Red flags:

- Reducing a safety anchor before an auxiliary mechanism proves stable.

## I. Output Discipline & Handoff Quality - 5 points

Strong evidence, 4-5:

- Names expected outputs, artifact paths, logs, dashboards, run settings,
  documentation updates, commit/PR expectations, and review checkpoints.
- Specifies what should be reported and what should not be claimed.

Partial evidence, 2-3:

- Names outputs but lacks paths, formats, or reporting criteria.

Weak or missing, 0-1:

- No durable output or handoff.

Red flags:

- Research-result claims without artifact path, settings, seed count, epoch
  count, baseline, or paired comparison.

## Scanner-Detectable Signals

Useful heuristic signals:

- headings: goal, non-goal, hypothesis, acceptance criteria, expert review,
  risk, validation, tests, baseline, controls, ablations, rollback, artifacts
- numeric gates: thresholds, tolerances, seed counts, epoch counts, error
  budgets, time windows
- goal anchors: project goal, research direction, non-goal, diagnostic-only,
  safety boundary, "do not claim", "do not run"
- evidence anchors: file paths, issue/PR links, artifact paths, commands,
  commit hashes, run settings, dataset names
- implementation contracts: schema, tensor, gradient, API, CLI, config,
  migration, state, side effect, ownership
- verification signals: test commands, CI, expected output, dashboards,
  reproducibility instructions
- risk signals: leakage, confound, stop, fail, rollback, guardrail,
  collapse, baseline fairness
- weak-plan signals: TODO, TBD, "later", "near", "materially", "some",
  "appropriate", "improve", "optimize", "evaluate" without gate

These signals should guide review, not determine final score automatically.

## Manual Review Questions

Ask these when evidence is unclear:

- Is the plan's central claim meaningful for the project goal?
- Would each named expert find the mechanism plausible?
- Would a negative result be interpretable?
- Are the baselines and controls actually fair?
- Are the thresholds strict enough for the risk level?
- Are the contracts sufficient for the specific codebase or domain?
- Is the scope too large for one execution cycle?
- Are scientific, product, or architecture claims separated from measurement
  artifacts?
- Does the plan hide a high-risk assumption behind a familiar phrase?
- Does the plan preserve the danf-specific boundary that all-label or
  wrong-label objectives are diagnostic controls, not the main path?

## ROI Action Guidance

Each action should include:

- effort: `S`, `M`, or `L`
- impact: `L`, `M`, or `H`
- priority: 0-100
- action: a concrete repair
- evidence: the gap or risk that motivated it
- category: rubric category improved

Prioritize actions that:

1. realign the plan with the stated project goal or non-goals
2. add measurable success/failure gates
3. clarify expert-specific mechanism and overclaim boundaries
4. clarify technical contracts
5. add missing controls or ablations
6. split an oversized plan into stages
7. add reproducible commands or artifact paths

## JSON Shape For Future Automation

When scripts are added, use this shape:

```json
{
  "schema_version": "1.0",
  "target": "...",
  "project_goal": "...",
  "expert_lenses": ["...", "..."],
  "generated_at": "...",
  "score": 78,
  "grade": "Reasonable With Revisions",
  "verdict": "Reasonable with revisions",
  "mode": "evidence review + dual-expert judgment",
  "categories": [
    {
      "id": "A",
      "name": "Project Goal Fit & Non-Goal Protection",
      "points": 16,
      "score": 12,
      "rationale": "...",
      "evidence": [{"path": "docs/plan.md", "detail": "..."}],
      "gaps": ["..."]
    }
  ],
  "expert_passes": [
    {
      "expert": "20-year computational neuroscientist",
      "judgment": "reasonable with revisions",
      "approvals": ["..."],
      "blockers": ["..."]
    }
  ],
  "reconciliation": {
    "agreements": ["..."],
    "disagreements": ["..."],
    "blocking_fixes": ["..."]
  },
  "risks": [{"severity": "high", "title": "...", "evidence": "..."}],
  "manual_review": [{"question": "...", "why": "..."}],
  "actions": [
    {
      "priority": 92,
      "effort": "S",
      "impact": "H",
      "category": "E",
      "action": "Add numeric promotion gates for energy and readout metrics.",
      "evidence": "Success criteria use qualitative language."
    }
  ],
  "extraction_gaps": [{"path": "artifact.pdf", "reason": "text unavailable"}]
}
```
