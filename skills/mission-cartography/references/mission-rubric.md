# Mission Cartography Rubric

Total: 100 points.

This rubric evaluates whether a project mission is clear enough to guide product, roadmap, positioning, and execution trade-offs. It is not a copywriting review. Use automatic scanner evidence as a baseline, then adjust only when human judgment has concrete evidence.

## Target

The target can be a project repository, product documentation set, startup pitch packet, strategy memo, website export, roadmap folder, or user-provided mission artifact.

## Decision

The score supports decisions such as:

- whether the current mission is clear enough to keep
- whether the mission needs rewriting before roadmap or positioning work
- whether product, docs, and metrics need alignment work
- which mission gaps should be fixed first

## Expert Evaluation Model

A competent mission reviewer first looks for the exact mission statement, then checks whether it answers:

1. Who is this for?
2. What real problem or change does it address?
3. Why does it matter now?
4. What product or work actually supports the mission?
5. What trade-offs would this mission help the team make?
6. How would progress be measured?
7. Is the same mission expressed consistently across artifacts?

Strong evidence is direct, specific, and repeated in execution artifacts. Weak evidence is aspirational wording without audience, problem proof, product alignment, or measurement.

## A. Mission Clarity & Specificity - 18

- 16-18: A concise mission or north-star statement names the intended change, scope, and value in concrete terms.
- 11-15: A mission exists and is mostly understandable, but contains vague impact language or incomplete scope.
- 5-10: Purpose is implied through product description but not stated as a usable mission.
- 0-4: No clear mission, only generic taglines or broad aspirations.

Evidence:
- `mission`, `purpose`, `north star`, `why we exist`, `vision`, `intended change`
- explicit mission sections in README, docs, pitch, website, or strategy files
- repeated mission phrase across artifacts

Proxy validity:
- Mission headings and repeated exact phrases are reasonable scanner signals, but clarity of the statement needs manual review.

Manual review:
- Judge whether the mission is specific enough to exclude plausible alternatives.

## B. Audience & Stakeholder Definition - 14

- 13-14: Target users, beneficiaries, buyers, or stakeholders are named with enough specificity to guide decisions.
- 9-12: Audience is named but broad, mixed, or missing stakeholder roles.
- 4-8: Audience is inferable from product context but not explicit.
- 0-3: No meaningful audience or stakeholder definition.

Evidence:
- target user, customer, beneficiary, stakeholder, persona, segment, buyer, community
- named user roles or use contexts

Proxy validity:
- Audience terms are useful only when paired with concrete segments or roles, not generic “users”.

Manual review:
- Validate whether the named audience matches the actual project and decision-maker.

## C. Problem Evidence & Urgency - 16

- 14-16: Mission is tied to concrete pain, unmet need, user research, operational data, complaints, risks, or urgency.
- 10-13: Problem is stated clearly but evidence is thin or not recent.
- 5-9: Problem is implied, mostly anecdotal, or described in generic market language.
- 0-4: No concrete problem or urgency behind the mission.

Evidence:
- problem, pain, urgency, unmet need, risk, evidence, interview, research, survey, complaint, support ticket
- quantified or named evidence sources

Proxy validity:
- Problem keywords are weak by themselves. Strong scoring requires evidence source hints or concrete examples.

Manual review:
- Assess whether problem evidence is credible, representative, and connected to the mission.

## D. Product & Roadmap Alignment - 18

- 16-18: Product capabilities, roadmap priorities, workflows, and scope explicitly reinforce the mission.
- 11-15: Main product direction aligns, but some features or roadmap items are disconnected.
- 5-10: Alignment is implied through feature lists but not explained.
- 0-4: Product/roadmap artifacts are absent or appear disconnected from the mission.

Evidence:
- roadmap, feature, use case, workflow, value proposition, scope, priority, release plan
- explicit links between mission language and product decisions

Proxy validity:
- Roadmap and feature terms indicate available execution artifacts, but manual review must judge actual alignment.

Manual review:
- Identify features that contradict or dilute the mission.

## E. Strategic Trade-off Power - 12

- 11-12: Mission clearly guides what to prioritize, decline, sequence, or constrain.
- 8-10: Some principles or focus areas exist, but trade-off use is incomplete.
- 4-7: Strategy is broad and does not clearly resolve conflicts.
- 0-3: Mission cannot help decide what not to do.

Evidence:
- principles, focus, not doing, trade-off, prioritization, decision criteria, constraints, scope, strategy
- explicit exclusions or sequencing rules

Proxy validity:
- Strategy keywords are weak unless paired with concrete “do/not do” or prioritization language.

Manual review:
- Test the mission against a plausible roadmap conflict.

## F. Measurement & Feedback Loops - 12

- 11-12: Mission has success metrics, feedback loops, OKRs, or learning mechanisms tied to the intended change.
- 8-10: Metrics exist but are incomplete, lagging, or not clearly tied to the mission.
- 4-7: Some success language exists without measurement discipline.
- 0-3: No measurement or feedback loop.

Evidence:
- KPI, metric, OKR, north-star metric, success criteria, adoption, retention, feedback loop, survey, cohort
- explicit measurement of mission outcomes

Proxy validity:
- Metric terms are good signals only when they measure mission outcomes, not generic activity.

Manual review:
- Confirm whether selected metrics would actually prove mission progress.

## G. Narrative Consistency Across Artifacts - 10

- 9-10: Mission is consistently expressed across README, docs, roadmap, pitch, website, and strategy artifacts.
- 7-8: Mostly consistent, with minor wording drift.
- 4-6: Multiple mission-like statements compete or omit key elements.
- 0-3: Mission narrative changes materially across artifacts or appears only once.

Evidence:
- repeated mission phrases, consistent audience/problem/product language, mission headings across multiple files

Proxy validity:
- Repetition across files is observable, but semantic consistency needs manual review.

Manual review:
- Compare the primary mission against outward-facing and execution-facing artifacts.

## Red Flags

- A slogan uses “empower”, “transform”, “revolutionize”, or “impact” without naming a user, problem, or change.
- The mission names everyone as the audience.
- Product roadmap contains many priorities that do not connect to the mission.
- Metrics optimize activity while ignoring the intended mission outcome.
- Pitch, README, website, and roadmap each imply different missions.
- The mission cannot answer a “what should we not build?” question.

## Manual Adjustment Rules

Adjust the automatic baseline when:

- a mission is clear but avoids keyword patterns the scanner can detect
- domain-specific language names the audience or problem without generic audience/problem terms
- a deck or document contains strong visual evidence that text extraction missed
- mission quality depends on market, community, or founder context outside the files
- product alignment is intentional but requires domain knowledge to interpret

Record adjustment rationale when changing the score by 5+ points or crossing a grade band.

## ROI Actions

Actions should be small enough to execute without a full strategy rewrite. Prefer:

- write a one-sentence mission with audience, problem, and intended change
- add a `docs/mission.md` or README mission section with evidence links
- map top features or roadmap items to mission outcomes
- define 2-3 mission metrics and the feedback source for each
- add explicit “we will not” or priority rules for trade-offs
- consolidate competing mission statements across docs

Effort:
- S: less than 1 hour
- M: 1-4 hours
- L: 4+ hours

Priority:
- `impact_score / effort_hours`
