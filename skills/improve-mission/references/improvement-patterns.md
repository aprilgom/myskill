# Mission Improvement Patterns

Use these patterns after reading a `mission-cartography` baseline. Each improvement should address a concrete category gap, not just make the writing sound better.

## A. Mission Clarity & Specificity

Symptoms:

- No explicit mission statement.
- Mission is a slogan or aspiration.
- Mission does not name a concrete change.
- Multiple mission-like statements compete.

Patch patterns:

- Add a `Mission` section near the top of README or strategy docs.
- Replace broad wording with audience + problem + intended change.
- Keep the final mission one sentence; move supporting evidence below it.

Example shape:

```text
Help <audience> <achieve/change outcome> by <mechanism> without <specific pain>.
```

## B. Audience & Stakeholder Definition

Symptoms:

- Mission says “everyone”, “teams”, “users”, or “the world” without a primary audience.
- Buyer, beneficiary, and user are conflated.
- Different docs imply different audiences.

Patch patterns:

- Add a primary audience sentence after the mission.
- Separate user, buyer, beneficiary, and excluded audience when relevant.
- Use concrete roles or segments already supported by the project.

Example:

```text
Primary audience: independent clinic nurses who complete visit documentation under shift-time pressure. Secondary stakeholder: supervising physicians who review summaries for accuracy.
```

## C. Problem Evidence & Urgency

Symptoms:

- The mission names an outcome but not the pain behind it.
- Problem claims are generic or unsupported.
- Research exists but is not linked to the mission.

Patch patterns:

- Add a short evidence paragraph under the mission.
- Link the mission to interviews, operational metrics, observed workflows, user complaints, support tickets, or documented risks.
- Mark unknowns instead of inventing proof.

Example:

```text
Evidence: support notes and pilot interviews show that teams lose time reconciling duplicated records before reporting deadlines. The next review should quantify frequency and cost.
```

## D. Product & Roadmap Alignment

Symptoms:

- Feature list does not explain how features advance the mission.
- Roadmap contains disconnected priorities.
- Scope is unclear.

Patch patterns:

- Add a mission-to-product mapping table.
- Group features by mission outcome.
- Add scope boundaries for tempting but off-mission work.

Example:

```markdown
| Mission outcome | Product support |
| --- | --- |
| Same-day summary completion | OCR intake, review workflow, physician approval queue |
```

## E. Strategic Trade-off Power

Symptoms:

- Mission cannot help decide what not to build.
- Roadmap priorities are additive with no sequencing logic.
- Product principles are missing.

Patch patterns:

- Add 3-5 decision principles.
- Add “we will not” boundaries.
- Add prioritization criteria tied to the mission.

Example:

```text
We prioritize work that improves same-day summary accuracy before analytics, billing, or general EHR replacement features.
```

## F. Measurement & Feedback Loops

Symptoms:

- Mission progress is not measurable.
- Metrics exist but measure activity, not mission outcomes.
- Feedback loops are absent.

Patch patterns:

- Add 2-3 mission progress metrics.
- Define feedback source and review cadence.
- Separate leading indicators from lagging outcomes.

Example:

```text
Mission metrics: same-day completion rate, correction rate after review, weekly time saved, and monthly user feedback review.
```

## G. Narrative Consistency Across Artifacts

Symptoms:

- README, pitch, website, and roadmap use different mission language.
- Old taglines remain in some files.
- Mission exists only in one artifact.

Patch patterns:

- Choose one canonical mission sentence.
- Update repeated intro sections to use the same audience/problem/change.
- Preserve channel-specific tone while keeping the core mission stable.

Example:

```text
Canonical mission: <one sentence>
README version: <same core, more technical>
Website version: <same core, more public-facing>
Internal version: <same core, includes trade-offs and metrics>
```

## When To Draft Instead Of Patch

Draft a separate mission brief when:

- the source artifact is binary or not safely editable
- the user asks for recommendations only
- evidence gaps make a final mission premature
- multiple stakeholders need to review options first

Use `templates/mission-improvement-brief.md` for this case.

## Before/After Review

After improvements, rerun `mission-cartography` and compare:

- total score and grade
- category movement, especially A, B, C, D, and F
- remaining manual-review checks
- extraction gaps
- whether actions became more specific or fewer

Do not claim the mission is final when after-score is high but key evidence still requires manual review.
