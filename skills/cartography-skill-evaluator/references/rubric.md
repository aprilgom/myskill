# Cartography Skill Evaluation Rubric

Use this reference to refine the baseline score from `scripts/score.py`.

## A. Cartography Contract & Trigger Fit (15)

Strong evidence:
- The description names cartography-style tasks and specific triggers.
- The skill clearly states what target it evaluates and what decision it supports.
- Exclusions are present for adjacent domains where misuse is likely.

Weak evidence:
- The description says "audit" or "evaluate" but does not promise map/score/evidence/actions.
- The trigger overlaps heavily with a generic skill evaluator.
- The target or user decision is unclear.

## B. Rubric Design Quality (20)

Strong evidence:
- Rubric totals exactly 100 points.
- It has 5-10 non-overlapping categories.
- Weights reflect decision impact.
- The rubric starts from a credible domain expert evaluation model: what experts inspect first, what they treat as decisive, and what risks lower confidence.
- Category names and criteria are domain-specific rather than generic labels such as "quality", "clarity", or "professionalism".
- Red flags, disqualifiers, and misleading signals are documented for the domain.
- Each category has observable evidence criteria and manual review notes.

Weak evidence:
- Equal weights without rationale.
- Categories restate each other.
- Categories are vague, such as "quality" or "professionalism", without observable criteria.
- Category weights appear based on what is easy to scan rather than what matters to the decision.
- No expert-priority model or domain-specific failure modes are described.
- No grade bands or interpretation.

## C. Evidence Collection & Scanner Fit (15)

Strong evidence:
- `score.py` scans the target artifacts the skill promises to evaluate.
- Scanner reports evidence paths, counts, gaps, and confidence limits.
- Unsupported binary or scanned inputs are reported as extraction gaps.
- The skill says the scanner is not an oracle.
- Scanner-detected signals are justified as valid proxies for the scored category.
- High-impact judgments that require domain expertise are reported as manual-review gaps unless the scanner has defensible evidence.

Weak evidence:
- Keyword counting dominates the score.
- Missing extraction is treated as negative evidence.
- Scanner ignores important target file types.
- There is no path from evidence to category scoring.
- Weak proxy signals receive high scores just because they are easy to detect.
- Scanner output blurs evidence collection with expert judgment.

## D. JSON Schema & Output Stability (10)

Strong evidence:
- JSON includes metadata, total score, grade, categories, evidence, risks, actions, and extraction gaps.
- Schema is deterministic enough for dashboards and comparisons.
- Renderer validates required fields.

Weak evidence:
- Output shape is undocumented.
- Dashboard relies on fields not emitted by scorer.
- Scores are only printed as prose.

## E. Dashboard Decision Usefulness (10)

Strong evidence:
- Dashboard shows score, category bars, evidence highlights, risks, actions, and gaps.
- It is a single-file technical report.
- It avoids decorative visuals that obscure findings.
- Placeholder checks are part of validation.

Weak evidence:
- Dashboard is only a scorecard with no evidence.
- Important caveats are hidden.
- Template contains unresolved placeholders or fragile assumptions.

## F. Validation Integrity (15)

Strong evidence:
- Validation compiles scripts, runs scorer, renders dashboard, checks no unresolved placeholders, and verifies non-empty output.
- `self_test.py` uses fixtures with positive and negative evidence.
- Validation tests realistic failure modes.
- Fixtures include at least one weak-proxy or expert-only signal that should become a gap/manual-review note rather than an inflated score.

Weak evidence:
- Validation is only "open the HTML".
- No self-test or fixture exists for a production scorer.
- Tests depend on external services without fallback.
- Validation only tests happy-path keyword matches and would not catch misleading expert-looking scores.

## G. ROI Action Quality (10)

Strong evidence:
- Actions include effort, impact, priority, and evidence.
- Actions address high-weight gaps or severe risks.
- The top actions are concrete and scoped.

Weak evidence:
- Actions are generic advice.
- Priority is not tied to score or evidence.
- Actions recommend rewrites before smaller fixes.

## H. Progressive Disclosure & Maintainability (5)

Strong evidence:
- `SKILL.md` stays concise and links to references only when needed.
- Scripts use standard libraries where possible.
- File inventory matches actual files.
- UI metadata matches the skill's purpose.

Weak evidence:
- Long duplicated rubric content in multiple files.
- Missing referenced files.
- Extraneous docs such as README or changelog inside the skill.

## Manual Review Prompts

Ask:

1. Could an agent know when to use this skill from the description alone?
2. Does the skill state the domain expert's evaluation frame before defining the rubric?
3. Would a competent practitioner in this domain recognize the category weights as decision-relevant?
4. Are domain-specific red flags, disqualifiers, and misleading signals represented?
5. Would two reviewers score the same target similarly from this rubric?
6. Can the scanner collect meaningful evidence for the domain?
7. Are scanner signals valid proxies, or are weak signals being over-scored?
8. Can the dashboard support a decision without reading raw JSON?
9. Would validation catch a broken scorer, renderer, template, or misleading expert-looking score?
10. Do recommended actions improve the score-driving gaps?
