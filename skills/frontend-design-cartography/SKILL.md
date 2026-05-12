---
name: frontend-design-cartography
description: Evaluate frontend design work for non-generic composition, brand presence, hero discipline, visual hierarchy, layout restraint, responsive quality, intentional motion, and design-system fit. Use for frontend design audits, landing page reviews, UI composition scoring, "does this look generic?", hero quality checks, visual direction reviews, and pre-ship frontend design cartography. Excludes deep accessibility, performance, SEO, and code architecture audits unless they directly affect frontend design quality.
---

# Frontend Design Cartography

Use this skill to evaluate a frontend page, app screen, component surface, or repository for design quality using evidence, screenshots, source inspection, and manual judgment. The goal is to identify whether the frontend feels intentional, branded, focused, and usable rather than generic, overbuilt, dashboard-like, or cluttered.

## Target

Evaluate frontend design artifacts such as:

- Built pages or local app routes.
- React/Vue/Svelte/Next source trees.
- HTML/CSS/static prototypes.
- Screenshots supplied by the user.
- Design-system-bound implementation work.

## Decision Supported

The score helps decide whether a frontend design is ready to ship, needs focused design revision, or should be reworked before further engineering investment.

## Expert Model

A strong frontend reviewer first looks at the first viewport, not isolated components. They ask whether the screen reads as one coherent composition, whether the brand or product is unmistakable, whether the visual anchor is real and relevant, whether typography and color create a specific direction, and whether content has been edited down to the few things the first viewport can carry.

They treat these as high-risk failures:

- The first viewport could belong to any brand after removing the nav.
- A landing page hero behaves like a dashboard or a grid of promos.
- The hero uses cards, floating badges, stat strips, pill clusters, or disconnected labels.
- The main visual is decorative rather than product, place, atmosphere, or context.
- The page defaults to system fonts, purple-on-white SaaS styling, or dark-mode-by-default aesthetics without reason.
- Desktop looks acceptable but mobile breaks the composition.
- Existing design-system work ignores established patterns.

Scanner output is a baseline. Final judgment must include visual review, preferably with desktop and mobile screenshots.

## Rubric Summary

The 100-point rubric:

- First-Viewport Composition: 18
- Brand Signal and Specificity: 14
- Hero Discipline and Content Budget: 14
- Visual Anchor and Atmosphere: 12
- Typography and Visual Direction: 12
- Restraint and Section Focus: 10
- Responsive Composition: 8
- Motion and Interaction Presence: 6
- Design-System Fit and React Practice: 6

See `references/frontend-design-rubric.md` for full criteria.

## What The Scorer Checks

`scripts/score.py` scans source files for baseline evidence:

- Hero, section, nav, CTA, media, card, badge, stats, schedule, and promo signals.
- Font stacks and default font usage.
- CSS variables and color direction.
- Background images, gradients, texture/pattern hints, and flat background risk.
- Motion evidence from CSS animations, transitions, animation libraries, and reduced-motion handling.
- Responsive evidence from media/container queries and viewport units.
- Design-system hints and React pattern usage.
- Test and screenshot verification signals.

It also records extraction gaps for binary files and unsupported artifacts.

## Workflow

1. Identify the target path, URL, screenshot, or design artifact.
2. If source is available, run the scorer:

   ```bash
   python3 scripts/score.py <target> --json /tmp/frontend-design-score.json --markdown
   ```

3. If possible, inspect desktop and mobile screenshots. Do not rely on source scanning alone for composition quality.
4. Render the dashboard:

   ```bash
   python3 scripts/render_dashboard.py /tmp/frontend-design-score.json \
     --template assets/template.html \
     --out /tmp/frontend-design-map.html
   ```

5. Report score, grade, evidence-backed risks, and the top three ROI actions.

## Manual Review Boundary

The scanner cannot determine whether a composition is visually beautiful, whether brand tone is strategically right, whether imagery is emotionally appropriate, or whether motion feels premium rather than noisy. It can only collect evidence and flag likely risks. Manual review should confirm:

- First viewport reads as one composition.
- Brand remains unmistakable without nav.
- Hero image is dominant and relevant.
- Cards and overlays are actually necessary.
- Typography feels intentional.
- Desktop and mobile both load and compose properly.

## Output Format

When reporting, keep the answer short:

- Score and grade.
- 2-4 highest-impact findings.
- Top 3 ROI actions.
- Generated JSON and HTML paths.
- Explicit manual-review gaps.

## Common Pitfalls

- Treating any polished UI as good even when it is generic.
- Rewarding decorative gradients as the main visual idea.
- Penalizing existing design-system work for preserving established patterns.
- Giving high scores from source inspection without screenshot review.
- Double-counting clutter under both hero discipline and section focus.

## Files

- `references/frontend-design-rubric.md`: full rubric and evidence model.
- `scripts/score.py`: heuristic evidence collector and scorer.
- `scripts/render_dashboard.py`: JSON-to-HTML dashboard renderer.
- `scripts/self_test.py`: fixture-based validation.
- `assets/template.html`: single-file dashboard template.
