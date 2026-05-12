---
name: build-mission
description: Create, refine, rewrite, or stress-test a clear mission statement for a project, product, startup, nonprofit, team, community, or internal initiative. Use when the user asks to write a mission, clarify purpose, define a north star, improve project purpose, align positioning around a mission, generate mission options, or turn messy project evidence into a concise mission. Do not use for scoring or dashboard audits; use mission-cartography for evaluation.
---

# Build Mission

Use this skill to help a user create or improve a mission statement that is specific, actionable, evidence-backed, and useful for product or strategy decisions.

## When To Use

Use this skill when the user wants to:

- create a new mission from project materials
- rewrite or sharpen an existing mission
- define a north star for a product, team, nonprofit, community, or initiative
- turn README, pitch, roadmap, research, or notes into mission options
- compare mission alternatives and recommend one
- produce supporting README, website, or internal strategy wording

If the user wants a score, evidence map, HTML dashboard, or rubric-based audit, use `mission-cartography` instead.

## Workflow

1. Identify the target.
   - What is the project, product, team, organization, or initiative?
   - What decision should the mission guide?
   - Is there an existing mission, tagline, vision, or north-star statement?

2. Gather evidence before drafting.
   - Read local README/docs/pitch/roadmap/research files when available.
   - Ask for missing context only when it materially changes the mission.
   - Extract the mission components: audience, problem, intended change, mechanism, boundary, and success signal.

3. Read `references/mission-patterns.md` when choosing mission shapes, diagnosing weak wording, or explaining trade-offs between options.

4. Draft mission components before writing final prose.
   - Audience: who the mission serves or mobilizes.
   - Problem: what pain, unmet need, or change matters.
   - Intended change: what becomes meaningfully different.
   - Mechanism: how the project creates that change.
   - Boundary: what the mission does not try to cover.
   - Success signal: how progress could be recognized.

5. Produce three mission options unless the user asks for one.
   - Clear/direct: plain and operational.
   - Strategic/product-led: emphasizes product mechanism and positioning.
   - Aspirational but concrete: more memorable, but still specific.

6. Stress-test each option.
   - Can target users recognize themselves?
   - Does it name a real problem or intended change?
   - Can it guide what not to build?
   - Can progress be measured?
   - Does it match the product, roadmap, and evidence?
   - Does it avoid generic language like “empower everyone” without specifics?

7. Recommend one mission.
   - Explain why it is strongest.
   - Include a refined final sentence.
   - Include supporting copy for README, website, or internal strategy if useful.
   - Include 2-4 next alignment actions.

## Output Rules

- Do not invent target users, customer evidence, metrics, founder intent, market facts, or roadmap items.
- Mark assumptions explicitly when evidence is missing.
- Prefer a mission sentence that can guide trade-offs over one that only sounds inspiring.
- Keep mission statements short enough to remember, usually one sentence.
- Avoid empty mission verbs unless grounded by specific audience/problem/change: empower, transform, revolutionize, unlock, enable, impact.
- Do not produce only a slogan. Include the reasoning and stress test.
- If the project has serious evidence gaps, give provisional options and list the questions that would most improve the mission.

## Output Format

Use this shape unless the user asks for something else:

```markdown
**Mission Components**
Audience:
Problem:
Intended Change:
Mechanism:
Boundary:
Success Signal:

**Mission Options**
1. Clear:
2. Strategic:
3. Aspirational:

**Recommended Mission**
<one sentence>

**Why This Works**
<short rationale>

**Stress Test**
- Trade-off power:
- Audience clarity:
- Evidence fit:
- Measurement:

**Next Alignment Actions**
1.
2.
3.
```

For longer engagements, use `templates/mission-brief.md` as the structure for a saved mission brief.

## Common Pitfalls

- Starting with clever wording before clarifying audience and problem.
- Writing a mission broad enough to cover any project.
- Confusing mission with vision, tagline, values, or feature list.
- Using “for everyone” when the product has a narrower primary audience.
- Treating the current roadmap as automatically mission-aligned.
- Choosing an inspirational option that cannot guide roadmap trade-offs.

## Files

- `references/mission-patterns.md` - mission shapes, examples, and stress-test guidance
- `templates/mission-brief.md` - reusable mission brief structure
