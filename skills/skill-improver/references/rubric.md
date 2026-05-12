# Skill Improvement Cartography Rubric

Use this rubric when the target is a Codex/Claude-style skill and the user wants an evidence-backed improvement map, not only prose feedback.

## Categories

| Category | Evidence Criteria | Points |
| --- | --- | ---: |
| Trigger Accuracy | Description names the artifact and user intents, includes useful boundaries, and avoids broad false triggers. | 20 |
| Workflow Executability | Steps identify the target, gather evidence, edit scoped files, rerun checks, and define fallback behavior. | 20 |
| Evaluation Separation | Eval and improvement responsibilities are distinct, baseline results are saved before editing, and skipped findings are reported. | 15 |
| Validation Integrity | Required checks are explicit, passing evidence is named, and failures/blockers are reported without claiming success. | 15 |
| Progressive Disclosure | Always-loaded instructions stay concise, detailed examples live in references, and referenced files are connected. | 10 |
| Resource Design | Scripts, references, assets, and metadata materially support repeatable use without unnecessary files. | 10 |
| Output Usefulness | Final report includes before/after score, changed files, fixed findings, remaining risks, and verification commands. | 5 |
| Maintainability | Frontmatter is valid, file inventory is accurate, generated cache files are absent, and instructions avoid stale facts. | 5 |

Total: 100 points.

## Grade Bands

- 90-100: Production-ready skill improvement workflow.
- 80-89: Strong workflow with small reliability gaps.
- 70-79: Usable with targeted fixes.
- 60-69: Risky for autonomous edits; requires manual supervision.
- Below 60: Needs redesign before use.

## Manual Review Boundary

The scorer is a heuristic baseline, not an oracle. It can detect structure, required resources, references, and evidence terms, but a reviewer must judge whether the recommendations match the target skill's real purpose and whether added scripts are worth their maintenance cost.

## JSON Schema

The bundled scorer emits deterministic JSON with:

- `schema_version`, `generated_at`, `target`, `score`, `grade`, and `mode`.
- `categories` keyed by category id, each with `score`, `max`, `rationale`, `evidence`, and `gaps`.
- `findings`, `risks`, `extraction_gaps`, and ROI-ranked `actions` with `priority`, `effort`, `impact`, and `action`.

