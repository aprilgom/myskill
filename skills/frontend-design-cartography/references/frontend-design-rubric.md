# Frontend Design Cartography Rubric

## Target

Frontend pages, app surfaces, landing pages, promotional pages, prototypes, screenshots, and source trees.

## Decision

Determine whether the frontend design is specific, composed, restrained, brand-led, responsive, and ready for user-facing review or shipment.

## Expert Evaluation Model

Frontend design quality is judged first through the assembled experience, especially the first viewport. Component polish matters, but it cannot rescue a generic hero, weak brand signal, cluttered composition, or broken mobile layout.

Excellent work has:

- One clear first-viewport composition.
- Brand or product name as a hero-level signal on branded pages.
- A dominant real visual anchor.
- Edited hero content with no secondary clutter.
- Purposeful typography and color direction.
- Sections that each do one job.
- Responsive layouts that preserve the composition.
- Intentional motion that supports presence and hierarchy.
- Respect for established design systems when they exist.

## Scoring Categories

### A. First-Viewport Composition, 18 points

Strong evidence: First viewport reads as one coherent composition, with a clear focal point and no dashboard-like fragmentation unless the product is a dashboard.

Partial evidence: Hero and page structure exist, but source suggests multiple competing blocks, grids, or panels in the first viewport.

Low evidence: First viewport appears to be a dashboard, card wall, promo stack, or unrelated component assembly.

Proxy validity: Source can reveal hero structure, grid/card density, and competing content blocks, but screenshot review is required for final judgment.

### B. Brand Signal and Specificity, 14 points

Strong evidence: Brand or product name is represented as a major visual element, and source/content shows specific product, venue, person, or offer language.

Partial evidence: Brand appears in nav or metadata, but not clearly in hero-level content.

Low evidence: Hero copy could apply to another brand after nav removal; generic SaaS or template language dominates.

Proxy validity: Text hierarchy and brand string occurrences are useful proxies, but visual size and emphasis require screenshot review.

### C. Hero Discipline and Content Budget, 14 points

Strong evidence: Hero contains a small set of primary elements: brand, one headline, one short supporting sentence, one CTA group, and one dominant visual.

Partial evidence: Hero is recognizable but includes extra stats, metadata, promos, event snippets, boxed callouts, or secondary marketing blocks.

Low evidence: Hero includes cards, floating badges, stat strips, pill clusters, schedule snippets, or multiple competing text groups.

Proxy validity: Class names and text patterns reveal likely clutter, but some terms may be legitimate outside the first viewport.

### D. Visual Anchor and Atmosphere, 12 points

Strong evidence: Imagery, video, canvas, or media shows product, place, atmosphere, or context, with full-bleed or dominant hero treatment for promotional surfaces.

Partial evidence: Uses gradients, patterns, or background treatment but no clear real visual anchor.

Low evidence: Flat single-color background or abstract decoration carries the page without real product/context imagery.

Proxy validity: Source can detect images, video, canvas, gradients, and background treatment, but relevance of the image is manual.

### E. Typography and Visual Direction, 12 points

Strong evidence: Purposeful non-default type choices, CSS variables, coherent visual direction, and no obvious purple-on-white or dark-mode bias by default.

Partial evidence: Some custom styling and variables, but default font stacks or generic palette remain prominent.

Low evidence: Inter/Roboto/Arial/system defaults dominate, little color system exists, or styling reads like a generic template.

Proxy validity: CSS font and color tokens are scannable; taste and fit require manual review.

### F. Restraint and Section Focus, 10 points

Strong evidence: Sections have one job, one headline, and concise support copy; cards are used only for real interaction containers.

Partial evidence: Sections are clear but include extra icon rows, pill clusters, boxed promos, or repeated cards.

Low evidence: Page is overloaded with many repeated visual containers and competing content.

Proxy validity: Source can estimate repeated cards and clutter signals; semantic purpose must be reviewed.

### G. Responsive Composition, 8 points

Strong evidence: Mobile and desktop layout evidence exists, including media/container queries or verified screenshots.

Partial evidence: Some responsive CSS exists, but no visible verification evidence.

Low evidence: Fixed desktop-first layout, overflow-prone values, or no responsive handling.

Proxy validity: CSS queries and test artifacts are good baseline evidence, but actual device rendering must be verified.

### H. Motion and Interaction Presence, 6 points

Strong evidence: At least 2-3 intentional motion cues exist for visual work, with reduced-motion handling where appropriate.

Partial evidence: Transitions or animation library usage exists but intent is unclear.

Low evidence: No motion in a visually led page, or noisy animation without accessibility consideration.

Proxy validity: Source can detect motion declarations, but hierarchy and taste are manual.

### I. Design-System Fit and React Practice, 6 points

Strong evidence: Existing design-system patterns are preserved; React code follows repo conventions and avoids unnecessary memoization.

Partial evidence: Some design-system or component reuse appears, but consistency is unclear.

Low evidence: Implementation invents a disconnected visual language inside an existing system or adds generic React optimization patterns without need.

Proxy validity: Imports and code patterns are scannable; whether the system was intentionally followed needs human context.

## Grade Bands

- 85-100: Distinctive and Ship-Ready
- 70-84: Strong With Targeted Revisions
- 55-69: Directionally Plausible
- 35-54: Generic or Overbuilt
- 0-34: Rework First

## Manual Review Requirements

Always mark these as manual-review items unless screenshots or explicit user evidence are available:

- Brand test after removing nav.
- Whether first viewport reads as one composition.
- Whether imagery is relevant and dominant.
- Whether typography feels purposeful.
- Whether motion improves hierarchy rather than adding noise.
- Whether existing design-system constraints justify exceptions.

## ROI Action Rules

High-priority actions should:

- Fix first-viewport composition before tuning lower sections.
- Strengthen brand signal before rewriting secondary copy.
- Remove hero clutter before adding visual effects.
- Replace decorative visuals with a real visual anchor.
- Verify desktop and mobile with screenshots before claiming readiness.
