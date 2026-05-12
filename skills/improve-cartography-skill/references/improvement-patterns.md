# Cartography Skill Improvement Patterns

Use these patterns after reading a `cartography-skill-evaluator` result.

## Contract & Trigger Fit

Symptoms:
- Description says only "evaluate" or "audit".
- Target and decision are unclear.
- Adjacent misuse is likely.

Patch:
- Add trigger nouns: `cartography`, `readiness map`, `100-point rubric`, `evidence`, `dashboard`, `ROI actions`.
- State what the skill evaluates and what decision the score supports.
- Add exclusions for adjacent legal, medical, financial, investment, or generic audit use when relevant.

## Rubric Design Quality

Symptoms:
- Point total is not 100.
- Categories overlap.
- Equal weights lack rationale.
- No grade bands.

Patch:
- Use 5-10 categories totaling exactly 100.
- Give highest weights to decision-critical evidence.
- Add strong/partial/weak evidence criteria for each category.
- Add manual review boundary and domain-specific grade names.

## Evidence Collection & Scanner Fit

Symptoms:
- Scorer is mostly keyword counting.
- Evidence paths are missing.
- Extraction failures are invisible.
- Scanner ignores promised artifact types.

Patch:
- Emit evidence items with path and detail.
- Emit gaps separately from negative evidence.
- Treat unsupported binaries/scans as extraction gaps.
- Add domain-specific artifact handlers only when practical.
- Keep scanner output as heuristic baseline plus manual review.

## JSON Schema & Output Stability

Symptoms:
- JSON shape is undocumented.
- Renderer expects fields the scorer does not emit.
- Scores appear only in prose.

Patch:
- Document a stable schema in `SKILL.md`.
- Include metadata, total score, grade, categories, evidence, risks, actions, extraction gaps.
- Make renderer validate required fields and fail clearly.

## Dashboard Decision Usefulness

Symptoms:
- Dashboard is visually polished but evidence-thin.
- Category bars lack rationale.
- Risks/actions/gaps are missing.
- Template placeholders can leak.

Patch:
- Show total score, grade, category bars, top evidence, risks, ROI actions, and extraction gaps.
- Keep the dashboard compact and technical.
- Add a no-unresolved-placeholder validation step.

## Validation Integrity

Symptoms:
- No self-test.
- Tests do not exercise scorer and renderer.
- Validation relies on opening HTML manually.

Patch:
- Add a self-test script with temporary fixtures.
- Include one high-evidence and one low-evidence fixture.
- Assert JSON shape, score direction, actions, HTML non-empty, and no `{{...}}` placeholders.
- Run `python3 -m py_compile` on scripts.

## ROI Action Quality

Symptoms:
- Actions are generic advice.
- No effort, impact, or priority.
- Actions do not map to low-scoring categories.

Patch:
- Each action includes effort, impact, priority, and evidence.
- Prioritize high-weight category gaps and severe risks.
- Prefer specific, bounded fixes before large rewrites.

## Progressive Disclosure & Maintainability

Symptoms:
- `SKILL.md` is long and repeats rubric detail.
- Referenced files are missing.
- UI metadata is stale.

Patch:
- Keep `SKILL.md` as workflow and routing.
- Move detailed scoring criteria into `references/*rubric*.md`.
- Keep file inventory accurate.
- Remove cache files and auxiliary docs.
