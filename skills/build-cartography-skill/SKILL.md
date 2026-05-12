---
name: build-cartography-skill
description: Create a new evidence-based cartography skill for evaluating any target domain with a 100-point rubric, heuristic scanner, JSON score output, single-file HTML dashboard, and ROI-ranked actions. Use when the user asks to build, scaffold, design, or improve a cartography-style skill for a new subject such as readiness, quality, risk, maturity, diligence, architecture, monetization, compliance, operations, or workflow evaluation.
---

# Build Cartography Skill

Use this skill to create a new cartography skill: a repeatable evaluation workflow that maps a target, scores it against evidence, renders a dashboard, and returns prioritized actions.

## What To Build

Default to this structure unless the user asks for something smaller:

```text
<domain>-cartography/
├── SKILL.md
├── agents/openai.yaml
├── references/<domain>-rubric.md
├── scripts/score.py
├── scripts/render_dashboard.py
├── scripts/self_test.py
└── assets/template.html
```

For a lightweight skill, `SKILL.md` and `references/<domain>-rubric.md` are acceptable. For a production cartography skill, include the scripts and dashboard template.

## Workflow

1. Define the cartography target.
   - What artifact or system is evaluated?
   - Who uses the result?
   - What decision does the score support?
   - What files, metrics, or signals can be inspected?

2. Name the skill.
   - Use `<domain>-cartography` unless the domain already implies a clearer name.
   - Keep it lowercase hyphen-case and under 64 characters.
   - Avoid vague names like `quality-cartography` unless the target is explicitly broad.

3. Model the domain expert's evaluation frame.
   - What would a competent practitioner in this domain inspect first?
   - What decision risks, failure modes, or disqualifiers matter most?
   - What signals are strong evidence, weak proxy evidence, or misleading evidence?
   - What cannot be inferred from files, metrics, or scanner output?
   - Why should each likely rubric category matter to the domain decision?
   - The rubric must reflect this expert decision model, not generic quality criteria.

4. Design the rubric.
   - Use a 100-point scale.
   - Prefer 5-10 categories.
   - Weight categories by decision impact, not by ease of detection.
   - Tie every category to the expert evaluation frame, including domain-specific red flags and manual judgment boundaries.
   - Explain why scanner-detectable signals are valid proxies for the category; weak proxies must not carry high scores.
   - Read `references/rubric-design.md` when designing or reviewing the rubric.

5. Write `SKILL.md`.
   - Frontmatter description must include strong trigger phrases and exclusions.
   - Body must include workflow, expert model summary, rubric summary, what the script checks, output rules, validation, common pitfalls, output format, and file inventory.
   - Make manual review explicit: scripts collect evidence, they are not oracles.

6. Write `references/<domain>-rubric.md`.
   - Include the expert evaluation model, category weights, full/partial/low evidence criteria, red flags, proxy-validity notes, and manual review guidance.
   - Keep category names action-oriented and non-overlapping.

7. Build `scripts/score.py`.
   - Use Python stdlib unless there is a clear reason not to.
   - Accept a target path and `--json <path>`.
   - Support `--markdown` when useful for quick terminal review.
   - Emit deterministic JSON with score, grade, categories, evidence, risks, actions, extraction gaps, and metadata.
   - Keep high-impact expert-only judgments as gaps or manual-review notes unless the scanner has defensible evidence.
   - Treat unsupported or binary inputs as extraction gaps, not as missing evidence.

8. Build `scripts/render_dashboard.py`.
   - Accept score JSON, `--template`, and `--out`.
   - Render a single HTML file from `assets/template.html`.
   - Fail if required fields are absent.

9. Build `assets/template.html`.
   - Keep it a restrained technical report: light surface, compact scorecards, bars, tables, no decorative map theme.
   - Include total score, grade, category bars, evidence highlights, risks, ROI actions, and extraction gaps.
   - Do not leave unresolved `{{PLACEHOLDER}}` tokens.

10. Build `scripts/self_test.py`.
   - Create a small temporary fixture with positive and negative evidence.
   - Run the scorer and renderer.
   - Assert JSON shape, non-empty HTML, no unresolved placeholders, and at least one action.
   - Include at least one fixture signal that should become a manual-review gap rather than an inflated score.

11. Validate before reporting completion.

```bash
python3 -m py_compile <skill-dir>/scripts/score.py <skill-dir>/scripts/render_dashboard.py <skill-dir>/scripts/self_test.py
python3 <skill-dir>/scripts/self_test.py
python3 <skill-dir>/scripts/score.py <target-or-fixture> --json /tmp/<domain>-score.json --markdown
python3 <skill-dir>/scripts/render_dashboard.py /tmp/<domain>-score.json \
  --template <skill-dir>/assets/template.html \
  --out /tmp/<domain>-map.html
```

Then confirm the HTML file is non-empty and contains no unresolved placeholders.

## Rubric Requirements

Every cartography rubric must answer:

- **Target:** what is being evaluated.
- **Decision:** what choice the score supports.
- **Expert model:** what a competent domain expert would inspect first, prioritize, and treat as disqualifying.
- **Evidence:** what observable signals count.
- **Weights:** why each category deserves its points.
- **Failure modes:** what domain-specific risks, red flags, or misleading signals must be surfaced.
- **Proxy validity:** why scanner-detected signals are reasonable evidence for each scored category.
- **Manual review:** what cannot be judged by scanner output alone.
- **Actions:** how low scores become ROI-ranked next steps.

Good categories are evidence-backed, independent, weighted, domain-specific, and actionable. Avoid categories that mostly restate each other or generic quality criteria that a domain expert would not prioritize.

## Scoring Model

Use this JSON shape unless the domain needs a documented variation:

```json
{
  "schema_version": "1.0",
  "target": "...",
  "generated_at": "...",
  "score": 72,
  "grade": "Evidence-Ready",
  "mode": "heuristic baseline + manual review",
  "categories": [
    {
      "id": "A",
      "name": "Category Name",
      "points": 15,
      "score": 10,
      "rationale": "...",
      "evidence": [{"path": "README.md", "detail": "..."}],
      "gaps": ["..."]
    }
  ],
  "risks": [{"severity": "high", "title": "...", "evidence": "..."}],
  "actions": [{"priority": 92, "effort": "M", "impact": "H", "action": "..."}],
  "extraction_gaps": [{"path": "deck.pdf", "reason": "text extraction unavailable"}]
}
```

Grades should be domain-specific, but must map cleanly to score bands.

## Output Rules

- Do not invent evidence, metrics, customers, policies, files, or benchmark results.
- Prefer concrete paths, counts, examples, and missing proof over generic advice.
- Separate scanner findings from manual judgment.
- Make exclusions explicit when the domain is adjacent to legal, medical, financial, or investment advice.
- Keep final reports short: score/grade, 1-2 findings, Top 3 actions, generated file paths.

## Common Pitfalls

- Building a keyword counter with no manual review path.
- Letting generic quality criteria replace the domain expert's actual evaluation frame.
- Giving high scores for weak proxy signals just because they are easy to scan.
- Making every category worth the same points when the decision does not support equal weighting.
- Scoring missing scanned PDFs as negative evidence without reporting extraction failure.
- Creating an attractive dashboard that does not expose evidence and gaps.
- Letting the output become a generic audit instead of a cartography: map, score, evidence, risks, actions.

## Files

- `references/rubric-design.md` - rubric design rules and examples for new cartography domains.
