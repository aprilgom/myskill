# Rubric Design For Cartography Skills

Use this reference when designing the 100-point rubric for a new cartography skill.

## Core Basis

A cartography rubric is based on decision evidence: the observable signals a user needs before deciding whether a target is ready, risky, mature, investable, monetizable, compliant, maintainable, or worth improving.

Start with these questions:

1. What target is evaluated?
2. What decision will the score inform?
3. What does excellent look like?
4. What failure modes matter most?
5. What evidence can be collected from files, code, metrics, docs, or user-provided materials?
6. Which judgments require manual review?
7. What actions should a low score naturally produce?

## Category Selection

Choose 5-10 categories. Each category must be:

- **Observable:** supported by files, metrics, text, structure, or explicit user input.
- **Independent:** not a restatement of another category.
- **Decision-relevant:** material to the decision the cartography supports.
- **Actionable:** a weak score points to a concrete improvement.
- **Scannable:** at least some evidence can be detected heuristically, even if final scoring needs judgment.

Avoid categories that are purely vibes, such as "professionalism", unless they are decomposed into observable criteria.

## Weighting

Assign 100 total points. Weight by decision impact:

- 15-25 points: make-or-break categories.
- 10-15 points: important but not decisive alone.
- 5-10 points: supporting or risk-adjusting categories.

Do not use equal weights by default. Equal weighting is appropriate only when the decision genuinely treats categories symmetrically.

## Evidence Levels

For each category, define at least three evidence levels:

- **Strong evidence:** direct, recent, specific proof.
- **Partial evidence:** indirect, stale, incomplete, or unvalidated proof.
- **Weak or missing evidence:** absent proof, contradictory signals, or only keyword-level hints.

For example, in a monetization rubric:

- Strong: named buyer segment, price point, payment flow, paid pilots or revenue metric.
- Partial: buyer persona and pricing idea, but no payment or traction proof.
- Weak: broad user claims with no buyer, budget, or pricing path.

## Manual Review Boundary

Every rubric must say what the scanner cannot know. Examples:

- Strategic quality of a pricing model.
- Whether architecture tradeoffs were intentional.
- Whether market size claims are credible.
- Whether policy controls are actually enforced.
- Whether benchmark data is representative.

The scorer can collect evidence and flag confidence. The skill user must make final judgment for these areas.

## Grade Bands

Create domain-specific grade names with clear interpretation. A common pattern:

- 85-100: ready for the intended decision or next stage.
- 70-84: strong enough for targeted follow-up.
- 55-69: plausible but evidence is incomplete.
- 35-54: high risk or thin evidence.
- <35: not ready for the intended decision.

Use names that match the domain, such as `Revenue Experiment Ready`, `Architecture-Fragile`, or `IC-Ready`.

## ROI Actions

Each action should include:

- effort: `S`, `M`, or `L`
- impact: `L`, `M`, or `H`
- priority: numeric rank, usually 0-100
- action: specific next step
- evidence: why this action matters

Prioritize actions that improve high-weight categories, unblock manual review, or reduce severe risks.

## Rubric Quality Checklist

Before finalizing, verify:

- The total is exactly 100 points.
- No two categories score the same evidence twice.
- At least one category captures downside risk.
- At least one category captures execution/readiness proof.
- The scorer can collect useful baseline evidence.
- Manual review requirements are explicit.
- Low scores map to specific actions.
- The final report can be written from the JSON without extra hidden context.
