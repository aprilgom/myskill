---
name: refero-design-adherence-cartography
description: Evaluate whether a frontend project follows a user-provided Refero style reference document such as design.md, DESIGN.md, or style reference markdown. Use when asked to score design.md adherence, Refero style compliance, design token implementation, style reference conformance, or whether a project followed a supplied design reference. Excludes general frontend taste audits unless a reference document is provided.
---

# Refero Design Adherence Cartography

Use this skill to evaluate how well a frontend implementation follows a user-provided Refero style reference document. The reference document is the source of truth; do not hard-code a brand, palette, typeface, or component set.

## Target

Evaluate a frontend project, page, or component implementation against a Refero-style markdown document that usually contains:

- `Tokens — Colors`
- `Tokens — Typography`
- `Tokens — Spacing & Shapes`
- `Components`
- `Do's and Don'ts`
- `Surfaces`, `Elevation`, `Imagery`, `Layout`
- `Agent Prompt Guide`
- `Quick Start` CSS and Tailwind token blocks

Some sections are optional. Missing optional sections should become extraction gaps, not automatic failures.

## Decision Supported

The score helps decide whether implementation should be treated as design-reference aligned, needs focused token/component cleanup, or requires a visual redesign before shipping.

## Expert Model

A strong reviewer first turns the Refero document into rules, then checks whether the implementation follows those rules in code and rendered behavior. They prioritize role fidelity over raw token presence: using a primary action color for actual CTAs matters more than defining an unused variable.

High-risk failures:

- The project uses unrelated colors, fonts, radii, or shadows despite the reference providing explicit tokens.
- Primary action, background, and text roles are swapped or treated as generic decorative colors.
- Components such as buttons, cards, navigation, inputs, or badges ignore the documented shape, padding, and visual hierarchy.
- The implementation violates explicit `Don't` rules.
- A dark reference is implemented as a light UI, or a contained reference becomes an unrelated full-bleed marketing layout.
- Scanner output is treated as final visual proof without manual screenshot review.

## Rubric Summary

The 100-point rubric:

- Reference Parse Completeness: 10
- Token Implementation: 15
- Color Role Adherence: 15
- Typography Adherence: 15
- Spacing, Radius, and Elevation: 10
- Component Pattern Match: 15
- Layout and Density Match: 10
- Imagery and Visual Language: 5
- Explicit Don't Violation Control: 5

See `references/refero-design-adherence-rubric.md` for full criteria.

## What The Scorer Checks

`scripts/score.py` accepts a project path and `--reference <design.md>`. It extracts rules from the reference and scans project files for baseline evidence:

- Color hexes, CSS variables, gradients, and Tailwind/theme tokens.
- Font family names, font variables, weights, line heights, and letter spacing.
- Spacing, padding, max-width, border radius, shadow, and elevation values.
- Component hints for buttons, cards, navigation, inputs, badges, FAQ, strips, and CTAs.
- Theme, layout, density, imagery, and `Do` / `Don't` text signals.
- Unsupported or binary files as extraction gaps.

The script is a heuristic baseline. It does not replace visual review.

## Workflow

1. Identify the supplied Refero reference file and target project.
2. Run the scorer:

   ```bash
   python3 scripts/score.py <project-path> --reference <design.md> --json /tmp/refero-design-score.json --markdown
   ```

3. Review extraction gaps and manual-review notes. If possible, inspect desktop and mobile screenshots.
4. Render the dashboard:

   ```bash
   python3 scripts/render_dashboard.py /tmp/refero-design-score.json \
     --template assets/template.html \
     --out /tmp/refero-design-map.html
   ```

5. Report score, grade, 2-4 highest-impact findings, top 3 actions, and generated paths.

## Manual Review Boundary

The scanner cannot determine visual polish, exact layout composition, font availability in the browser, image suitability, responsive quality, or whether a component feels intentionally adapted. It can collect evidence and flag likely adherence risks. Manual review should confirm:

- The first viewport visually matches the reference mood and theme.
- CTA, text, and background roles are correctly assigned.
- Component shapes and spacing look aligned, not merely token-defined.
- Imagery follows the reference's product, photography, gradient, or texture guidance.
- Desktop and mobile render without layout drift.

## Output Format

Keep reports short:

- Score and grade.
- Reference path and project path.
- Highest-impact adherence findings.
- Top 3 ROI actions.
- JSON and HTML output paths.
- Explicit manual-review gaps.

## Common Pitfalls

- Hard-coding Stripe, Hyer, ORYZO, Shares, or any other sampled brand.
- Giving full credit for tokens defined but unused.
- Penalizing absent optional sections such as `Elevation` when the reference omits them.
- Treating source scans as visual proof.
- Double-counting the same missing token under color, component, and layout.
- Ignoring `Don't` rules because they are prose rather than token tables.

## Files

- `references/refero-design-adherence-rubric.md`: full rubric and evidence model.
- `scripts/score.py`: reference parser, heuristic project scanner, JSON scorer.
- `scripts/render_dashboard.py`: JSON-to-HTML dashboard renderer.
- `scripts/self_test.py`: fixture-based validation.
- `assets/template.html`: single-file dashboard template.
