---
name: source-to-cheatsheet
description: Use when the user asks to create, rewrite, or improve a cheatsheet from a source document, article, manual, README, specification, transcript, notes, or pasted text. Produces a concise, source-grounded, task-focused reference that preserves important commands, APIs, definitions, workflows, gotchas, examples, and decision rules without inventing unsupported content.
---

# Source To Cheatsheet

## Purpose

Turn source material into a practical cheatsheet that helps a reader act quickly. Preserve the source's meaning, compress aggressively, and make uncertainty explicit.

## Workflow

1. Identify the target reader and use case from the user's request. If unspecified, assume a busy practitioner who needs a fast operational reference.
2. Identify the conversion mode:
   - Single-source mode: one document, pasted source, transcript, or page.
   - Bulk mode: many related files, sidecars, documentation trees, split chapters, or parallel language versions.
   If more than five source files are in scope, do not start writing immediately unless the user explicitly asked for bulk conversion. First define the conversion strategy, source groups, target files, skip/aggregate rules, and sample-validation plan. In bulk mode, preserve one output per requested source, define a shared quality bar before writing, and sample-check each document family before declaring the batch complete.
3. Inspect the source structure before summarizing: headings, tables, code blocks, examples, warnings, prerequisites, repeated concepts, front matter, split-document navigation, and language/locale.
4. Classify the source type and choose the output strategy:
   - Concept/API guide: mental model, key APIs, examples, errors, migration notes.
   - Style/rules guide: rules, decision criteria, do/don't examples, exceptions, gotchas.
   - Procedure/SOP: prerequisites, ordered workflow, validation checks, escalation.
   - Navigation/index/license/source-note page: concise orientation and references; do not force full cheatsheet sections.
   - Split-document parent/child set: avoid duplicating the parent table of contents in every child; summarize the child page's actionable content.
   - Localized mirror: keep each output in the source language and avoid adding facts from the other locale unless the user requests cross-language reconciliation.
5. Extract the highest-value material:
   - commands, flags, parameters, API names, configuration keys, file paths
   - definitions and distinctions the reader must not confuse
   - workflows, checklists, sequences, and decision rules
   - constraints, warnings, edge cases, defaults, and version notes
   - complete minimal examples that clarify real usage
6. Convert source claims into actionable reference material. Do not merely restate the table of contents or copy the opening paragraphs unless they are themselves the practical rule.
7. Group content by task or concept, not by the source's original order, unless the source order is itself the workflow.
8. Write in compact Markdown using tables, bullets, and fenced code blocks where they improve scanning.
9. Verify the cheatsheet against the source before finalizing. Remove unsupported additions and mark unclear items as "source unclear" rather than guessing.

## Output Shape

Prefer this structure unless the user asks for another format:

```markdown
# [Topic] Cheatsheet

## Core Mental Model
[3-6 bullets that explain how to think about the topic]

## Common Tasks
| Task | Use | Notes |
|---|---|---|

## Commands / APIs / Syntax
| Item | Pattern | Key options |
|---|---|---|

## Workflows
1. ...

## Gotchas
- ...

## Source Gaps
- ...
```

Omit sections that do not fit the source. For non-technical material, replace "Commands / APIs / Syntax" with "Key Concepts", "Rules", or "Examples".

Do not include low-information section maps as filler. A `Key Sections` table is useful only when each row tells the reader what decision, task, or risk that section helps with. Avoid rows like `Main topic`, `Subtopic`, `Reference`, or repeated heading labels with no actionable use.

For rule-heavy sources, prefer this shape:

```markdown
# [Topic] Cheatsheet

## Rules
| Situation | Do | Avoid | Why |
|---|---|---|---|

## Decision Criteria
- If ..., choose ...

## Examples
```[language]
[complete minimal example or preserved good/bad pair]
```

## Gotchas
- ...
```

For navigation, index, license, or very short pages, prefer this shape:

```markdown
# [Topic] Reference Note

## What This Page Is For
- ...

## Use This When
- ...

## Links / Source Notes
| Item | Target | Notes |
|---|---|---|
```

## Quality Bar

- Source-grounded: do not add external facts unless the user explicitly asks for enrichment.
- No hidden enrichment: do not modernize, update versions, add best practices, or import outside knowledge during ordinary cheatsheet generation. If the user requests enrichment, put it in a clearly labeled section separate from source-derived content.
- Dense but readable: prefer short noun phrases and concrete examples over prose explanation.
- Actionable: every section should help the reader decide, do, check, or remember something.
- Faithful: preserve important qualifiers such as "only", "must", "default", "deprecated", "experimental", "recommended", and version requirements.
- Skimmable: use consistent labels, parallel phrasing, and compact tables for repeated patterns.
- Traceable when needed: if the source has page numbers, section names, anchors, or line numbers, include lightweight references for high-risk claims.
- Non-extractive: transform the source into operational guidance. A sequence of first sentences, heading names, or code-block first lines is not sufficient.
- Example integrity: preserve good/bad pairs together, keep code fences balanced, and avoid truncated code snippets that cannot communicate the point.
- Locale-preserving: keep the output language aligned with the source unless the user asks for translation.

## Handling Source Types

- For code or API docs: prioritize signatures, parameters, return values, examples, errors, and migration notes.
- For programming style guides: prioritize required/recommended/avoid rules, exceptions, tradeoffs, local-consistency guidance, and good/bad examples.
- For manuals or SOPs: prioritize prerequisites, ordered steps, roles, validation checks, and escalation conditions.
- For policy or legal-like text: keep exact obligations and exceptions visible; avoid over-compressing qualifiers.
- For long-form articles: extract the argument, framework, key terms, evidence, and practical takeaways.
- For meeting notes or transcripts: separate decisions, action items, open questions, and reusable context.

## Bulk Conversion Gates

When converting multiple files:

1. Confirm the user asked for bulk output or approve a strategy before generating more than five files.
2. Confirm source/target coverage, for example every `*.md` source has the expected `*.tldr.md` target and no accidental extras.
3. Reject metadata-only outputs. Every non-trivial source should produce body content beyond front matter.
4. Run structural checks appropriate to the output format: balanced fences, non-empty tables, no placeholder labels, no `TODO`, no unsupported `source unclear` unless the source is genuinely ambiguous.
5. Detect repeated boilerplate and low-information patterns across files, including identical section names with generic rows such as `Main topic`, `Subtopic`, or `Reference`.
6. Sample at least one output from each document family or source type. Include short pages, long pages, index/navigation pages, localized pages, and pages with examples when present. Compare each sample to the source for missing rules, warnings, examples, and invented claims.
7. If random samples reveal systematic issues, revise the conversion approach and regenerate or patch the affected family before finalizing.
8. Run repo-specific validation when the outputs are part of a build, documentation site, or test suite.

Shell-safe structural checks can include:

```bash
find <target-root> -name '*.md' -type f -print0 | xargs -0 awk '
  /^```/ { fences[FILENAME]++ }
  /Main topic|Subtopic|Reference/ { bad[FILENAME]=1 }
  /TODO|FIXME|source unclear/ { todo[FILENAME]=1 }
  END {
    for (f in fences) if (fences[f] % 2) print f ": unbalanced code fences"
    for (f in bad) print f ": low-information table label"
    for (f in todo) print f ": unresolved placeholder"
  }'
```

## Sidecar Mode

Use sidecar files such as `*.tldr.md` only when the user asks for sidecars or the repository already has that convention.

- Preserve required front matter deliberately; do not cargo-cult hidden-build settings unless the site needs them.
- For Hugo hidden sidecars, use `build.render: never`, `list: never`, and `publishResources: false` only when the sidecar should be embedded or consumed without standalone publication.
- Avoid sidecars for navigation-only, license, landing, duplicate aggregate, or generated index pages unless the user explicitly wants full coverage or the site feature requires a sidecar for every source.
- When sidecars are required for all files, use a lighter "Reference Note" shape for short/navigation/license pages instead of forcing rule/API sections.
- Treat existing sidecars as implementation examples or anti-pattern evidence, not as source truth. Validate claims against the primary source document unless the user explicitly asks to revise an existing sidecar in place.
- When producing drafts outside a repository, state the filename policy. Prefer mirroring the source-relative directory under the temporary/output root and converting `source.md` to `source.tldr.md`.
- Preserve repository front matter only when the output will be consumed by that repository. For standalone sample drafts, omit front matter unless the user asks to preview the exact sidecar artifact.

## Localized and Annotated Sources

Some sources contain translator notes, editor explanations, changelog sections, or rationale added around the primary content.

- Keep the output in the source language unless translation is requested.
- Separate primary source rules from translator/editor notes when both are useful.
- Do not let commentary override the source's rule unless the commentary explicitly states a correction or local adaptation.
- In mirrored language trees, avoid reconciling differences across locales unless the user asks for cross-language consistency work.

## Final Check

Before responding, compare the draft against the source and answer:

- Are all high-risk commands, limits, warnings, and prerequisites preserved?
- Did any table cell become too vague to act on?
- Did I invent a relationship, recommendation, or example not present in the source?
- Did I include a heading map, opening-paragraph extract, or truncated example instead of an actionable rule or example?
- For bulk work, did each document family pass at least one source-to-output sample review?
- Is the result shorter and easier to use than the original?
