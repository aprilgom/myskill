# Refero Design Adherence Rubric

## Target

A frontend implementation evaluated against a user-supplied Refero-style markdown reference document.

## Decision

Decide whether the implementation is aligned enough to keep building, needs focused correction, or should be redesigned against the supplied reference.

## Expert Evaluation Model

An expert reviewer treats the reference as a contract with two layers:

1. **Concrete tokens and component rules**: colors, fonts, type scale, spacing, radius, shadows, surfaces, component padding, and CSS/Tailwind custom properties.
2. **Intent and role guidance**: theme, density, layout model, imagery, visual language, `Do` rules, and `Don't` rules.

The scanner can inspect layer 1 and parts of layer 2. Manual review is required for final judgment on composition, imagery quality, responsive behavior, and whether implementation choices feel intentionally adapted.

## Grade Bands

- 85-100: Reference-Aligned
- 70-84: Mostly Aligned
- 55-69: Partially Aligned
- 35-54: Drift Risk
- 0-34: Reference Not Followed

## Categories

### A. Reference Parse Completeness — 10

Strong evidence: the parser extracts brand/title, theme, color tokens, typography, spacing, radius, components, `Do` / `Don't`, layout, and Quick Start tokens when present.

Partial evidence: core token tables parse but prose guidance or components are incomplete.

Weak evidence: the reference is missing, not Refero-like, or only a title and prose can be extracted.

Proxy validity: scoring cannot be meaningful unless the reference is parsed. Optional sections such as shadows or elevation are not required.

### B. Token Implementation — 15

Strong evidence: reference CSS variables, Tailwind theme tokens, or equivalent implementation tokens appear in source and are used near relevant UI code.

Partial evidence: values appear as raw hexes/classes, or tokens are defined but usage is thin.

Weak evidence: few or no extracted token values appear in implementation.

Proxy validity: source token presence is direct evidence of implementation intent, but unused tokens must not receive full credit.

### C. Color Role Adherence — 15

Strong evidence: background, text, border, accent, and primary action colors from the reference appear in appropriate roles, especially CTAs and page surfaces.

Partial evidence: correct colors are present but role mapping is unclear or incomplete.

Weak evidence: unrelated palettes dominate, theme is inverted without justification, or primary action color is absent from CTAs.

Proxy validity: color roles are explicitly documented in Refero tables and Agent Prompt Guide. Scanner evidence must be paired with manual visual review.

### D. Typography Adherence — 15

Strong evidence: primary font token/family, fallback intent, weights, type scale, line height, and letter spacing appear in CSS or component classes.

Partial evidence: font variables or sizes are present but weights/tracking/scale are incomplete.

Weak evidence: implementation defaults to generic system styles with little sign of the reference's type system.

Proxy validity: typography is central to Refero references and is strongly detectable from CSS and class names, but browser font loading requires manual confirmation.

### E. Spacing, Radius, and Elevation — 10

Strong evidence: spacing scale, section gap, card padding, element gap, border radius, shadow, and elevation rules are followed when present.

Partial evidence: some values appear, but major component shapes or layout rhythm differ.

Weak evidence: arbitrary spacing/radius/shadow values dominate or explicit no-shadow/flat-surface guidance is violated.

Proxy validity: dimensional values are detectable in source. Visual rhythm still requires screenshot review.

### F. Component Pattern Match — 15

Strong evidence: documented button, card, navigation, input, badge, FAQ, strip, or product panel patterns are implemented with matching roles, color, shape, padding, and type.

Partial evidence: component names or some rules match, but role-specific treatment is inconsistent.

Weak evidence: generic components ignore the reference's documented patterns.

Proxy validity: component prose is domain-specific and decision-relevant. Scanner can detect names and values, but manual review must verify exact application.

### G. Layout and Density Match — 10

Strong evidence: implementation follows the documented full-bleed or contained model, max-width, section rhythm, density, grids/stacks, and navigation layout.

Partial evidence: broad layout direction matches but key spacing or structure differs.

Weak evidence: implementation uses an unrelated page model or density.

Proxy validity: layout terms and values are partially detectable; final judgment is visual.

### H. Imagery and Visual Language — 5

Strong evidence: imagery, gradients, textures, product renders, screenshots, or photography follow the reference guidance.

Partial evidence: some visual language signals appear but assets are placeholders or weakly related.

Weak evidence: imagery is absent where central to the reference, or decorative visuals contradict the guidance.

Proxy validity: source scan can detect asset types and gradient/image usage. Relevance and quality require manual review.

### I. Explicit Don't Violation Control — 5

Strong evidence: implementation avoids explicit forbidden patterns in the reference, such as extra saturated colors, wrong fonts, wrong radii, heavy shadows, gradients, or generic blues.

Partial evidence: no obvious violations are detected, but scanner confidence is limited.

Weak evidence: direct conflicts with `Don't` rules are found.

Proxy validity: `Don't` rules are explicit risk controls. Some are detectable by text/value scan; others need manual review.

## Manual Review Guidance

Always separate:

- **Evidence**: exact files, tokens, values, and detected matches.
- **Risks**: likely violations or missing proof.
- **Manual gaps**: visual or browser-dependent judgments the script cannot make.

Do not invent screenshots, font load status, asset quality, or rendered behavior.

## ROI Actions

Prioritize actions that:

- Implement missing reference tokens.
- Replace unrelated palette/type/radius values.
- Fix primary CTA and surface role mapping.
- Align components with documented patterns.
- Add screenshot verification for manual gaps.
