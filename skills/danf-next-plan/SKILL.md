---
name: danf-next-plan
description: Use when asked to decide, design, debate, or write the next DANN-FF/danf research or implementation plan using 20-year neuroscience and ML expert viewpoints before execution.
---

# DANF Next Plan

Create the next DANN-FF/danf research or implementation plan by delegating to
two separate expert agents whenever agent delegation is available: a 20-year
computational neuroscientist and a 20-year machine learning expert. The output
is a concrete next plan, not execution.

Use this when the user asks what to do next, wants a bold or conservative next
phase, asks two experts to debate the next direction, or wants a plan after
Phase 13/14/15 evidence.

## Required Context

Read the minimum needed project context before planning:

- `docs/dann-ff-handoff/00-start-here.md`
- `docs/dann-ff-handoff/02-current-code-state.md`
- `docs/dann-ff-handoff/03-key-results.md`
- `docs/dann-ff-handoff/04-decision-log.md`
- the relevant `docs/dann-ff-handoff/next/*.md` phase plan
- `ARCHITECTURE.md` when implementation scope is involved

If the user names a specific phase or artifact, read that first.

## Research Guardrails

Default project goal:

```text
interneuron as negative generator
```

Protect these boundaries:

- Do not make all-label or externally wrong-label objectives the main path.
  They are diagnostic controls.
- Do not jump to internal-only negatives before mixed or replacement evidence
  supports it.
- Do not claim DANN improvement without artifact path, settings, seed count,
  epoch count, baseline, and paired deltas where appropriate.
- Do not launch WSL/GPU jobs from this skill. Write the plan only.
- Treat readout-only gains as representation regularization unless energy
  geometry is preserved.

## Workflow

0. Use strict separate-agent planning:
   - If the environment supports subagents and the user asked for expert-agent
     planning, spawn two separate agents before drafting the plan.
   - Agent A owns the computational neuroscience proposal.
   - Agent B owns the ML proposal.
   - Do not replace this with one blended internal monologue.
   - If subagents are unavailable, say the strict two-agent workflow cannot be
     fully executed and ask whether to continue with a fallback.
1. Identify the current frontier locally before delegation:
   - latest completed phase
   - current baseline
   - strongest evidence
   - unresolved conflict
   - active next action
2. Give both agents the same compact evidence packet:
   - project goal: `interneuron as negative generator`
   - current frontier summary
   - relevant phase/artifact paths
   - guardrails and forbidden claims
   - required output format for their proposal
3. Require independent proposals:
   - neuroscience agent proposes the next plan from circuit plausibility,
     mismatch generation, E/I dynamics, and biological interpretability.
   - ML agent proposes the next plan from objective design, controls, leakage,
     ablations, metrics, and promotion gates.
4. Relay each proposal to the other agent and require critique:
   - what is compelling
   - what is misleading or under-specified
   - what would make the plan falsifiable
   - what must be measured before promotion
5. Reconcile locally:
   - shared approvals
   - shared blockers
   - expert disagreements
   - decision points that should remain explicit
6. Write the final next plan.
7. Recommend evaluating the plan with `danf-plan-cartography` before
   implementation.

## Agent Delegation Prompts

Use these as task templates when spawning agents.

Neuroscience agent:

```text
You are acting as a 20-year computational/systems neuroscientist reviewing the
DANN-FF project goal: interneuron as negative generator. Given the evidence
packet, propose the next research or implementation plan. Focus on circuit
plausibility, inhibitory mismatch generation, E/I balance, residual signals,
biological interpretability, and what would make a negative result meaningful.
Do not optimize for readout-only gains. Return: proposed plan name, hypothesis,
mechanism, required measurements, promotion gates, failure signatures, and
risks.
```

ML agent:

```text
You are acting as a 20-year ML research expert reviewing the DANN-FF project
goal: interneuron as negative generator. Given the evidence packet, propose the
next research or implementation plan. Focus on objective design, baselines,
controls, leakage checks, ablations, tensor/config contracts, metrics,
statistical evidence, and staged failure. Do not turn wrong-label or all-label
objectives into the main path. Return: proposed plan name, hypothesis,
objective, required controls, promotion gates, failure signatures, and risks.
```

Critique relay:

```text
Here is the other expert's proposal. Critique it from your expertise. Identify
what is compelling, what is misleading or under-specified, what measurements or
controls are missing, and what must change before this becomes the next plan.
```

## Expert Lenses

Computational neuroscience lens:

- Does the plan advance interneuron-generated mismatch or negative pressure?
- Is the circuit interpretation plausible and not just ML decoration?
- Does it distinguish diagnostic scaffolds from proposed mechanisms?
- Would a negative result be biologically interpretable?
- Are inhibition, residuals, E/I balance, and activity collapse interpreted
  carefully?

ML lens:

- Is the objective operationally testable?
- Are baselines, controls, leakage checks, ablations, and promotion gates
  sufficient?
- Are tensor, gradient, data, metric, and config contracts clear enough?
- Does the plan distinguish readout gains from true FF energy progress?
- Is the experiment ladder staged to fail informatively?

## Final Plan Shape

Use this structure unless the user asks for a different artifact:

```markdown
# Phase N Plan: <name>

## Goal
<one clear goal>

## Core Hypothesis
<falsifiable claim>

## Why This Is Next
<prior evidence and what it rules out>

## Expert Reconciliation
<what neuroscience and ML agreed on, and remaining disagreement>

## Objective Or Mechanism
<objective form, circuit mechanism, or implementation mechanism>

## Implementation Scope
<files/modules/scripts likely to change, or "no code changes">

## Experiment Ladder
<smallest screen, promotion, seed count, epoch count, baselines>

## Promotion Gates
<numeric gates and artifact-based gates>

## Failure Signatures
<what result stops or redirects the plan>

## Documentation And Artifacts
<where results, settings, seeds, baselines, and conclusions go>

## Do Not Claim
<explicit overclaim boundaries>
```

## Common Pitfalls

- Writing one blended expert voice instead of two independent passes.
- Simulating two agents in one answer when separate agent delegation was
  available.
- Letting the ML objective solve readout while weakening the stated research
  mechanism.
- Letting biological language justify an objective without operational tests.
- Adding too many mechanisms before a minimal diagnostic stage.
- Treating a scalar internal penalty as proof of internal negative generation.
- Forgetting to define what failure means.
- Planning GPU sweeps in parallel despite the single-target constraint.

## Output

Keep the final response concise:

- recommended next plan name
- why it is next
- neuroscience view
- ML view
- cross-agent critique summary
- reconciled plan
- first executable step
- whether `danf-plan-cartography` review is needed before execution
