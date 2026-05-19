# TLDR Cheatsheet Rubric

## Target

Markdown `.tldr.md` files intended to appear as concise cheat sheets for longer documentation pages.

## Decision

The score answers whether the cheat sheet is useful enough to publish and which edits would most improve reader utility.

## Scoring

### A. Source Coverage & Prioritization - 20

Full credit:
- Covers the source's major sections or intentionally collapses them into equivalent decision areas.
- Preserves high-impact rules, examples, caveats, and "when to use" guidance.
- Omits low-value exposition without losing the source's main meaning.

Partial:
- Covers some headings but misses important caveats or examples.
- Mirrors source order but does not prioritize reader needs.

Low:
- Generic summary with little relationship to the source.
- Empty or near-empty sidecar.

Manual review:
- Heading overlap is only a proxy. A renamed heading can still be faithful; copied headings can still miss the point.

### B. Cheat Sheet Density & Scanability - 16

Full credit:
- Uses compact headings, bullets, short paragraphs, and grouped examples.
- A reader can scan the whole file quickly and find rules, examples, and gotchas.
- Avoids long blocks of prose copied from the source.

Partial:
- Generally concise but has bloated paragraphs or unclear grouping.

Low:
- Reads like a mini-article rather than a cheat sheet, or is too terse to be useful.

### C. Code Snippet Usefulness - 18

Full credit:
- Includes focused, idiomatic, copy-pasteable snippets for code-heavy source sections.
- Snippets demonstrate the decision or pitfall, not incidental syntax.
- Code fences have language tags where useful.

Partial:
- Has snippets, but some are too large, incomplete, or not tied to a rule.

Low:
- No snippets for a code-heavy document, or snippets are misleading.

Manual review:
- The scanner can count code blocks, but a human must judge correctness and teaching value.

### D. Correctness & Source Faithfulness - 18

Full credit:
- Does not distort source guidance.
- Keeps version-sensitive statements, API names, and behavior accurate.
- Makes caveats visible where missing them would cause wrong code.

Partial:
- Mostly faithful but loses nuance in one or two places.

Low:
- Contradicts source guidance, introduces unsupported recommendations, or includes stale syntax.

Red flags:
- Unsupported "always/never" rules.
- Snippets that do not compile when presented as complete examples.
- Version claims without source support.

### E. Actionability & Decision Cues - 14

Full credit:
- Tells the reader what to do, when to do it, and what to avoid.
- Includes comparison cues such as "prefer X when...", "use Y if...", and "avoid Z because...".
- Highlights failure modes and review checks.

Partial:
- Good facts, weak decision guidance.

Low:
- Descriptive summary without operational guidance.

### F. Integration With Site Conventions - 8

Full credit:
- Keeps required front matter and `build.render: never` conventions when used by the Hugo TLDR partial.
- Uses Markdown that the site can render cleanly.
- Avoids direct `.md` links from published content unless the repository convention allows them.

Partial:
- Minor convention mismatch that does not break rendering.

Low:
- Missing front matter or structure causes rendering/test failures.

### G. Maintainability & Edit Safety - 6

Full credit:
- Compact enough to maintain next to the source.
- Does not duplicate large source sections.
- Localizes examples and avoids fragile generated artifacts.

Partial:
- Useful but too long or too close to copied source text.

Low:
- Hard to update, generated-looking, or full of stale placeholders.

## Manual Review Checklist

- Compare source headings and cheat sheet headings.
- Identify the top 3 source decisions a reader must remember.
- Check that at least one snippet teaches each code-heavy decision area.
- Verify snippets use current syntax for the repository's intended Go version.
- Check that caveats are not softened into vague advice.
- Look for unsupported additions not present in source or accepted project conventions.

## ROI Action Guidance

High-impact actions:
- Add missing snippets for source sections that are code-heavy.
- Add "when to use / avoid" cues around advanced patterns.
- Restore required TLDR front matter.
- Remove copied prose and replace it with bullets plus examples.

Medium-impact actions:
- Rename headings for scanability.
- Split long code blocks into focused examples.
- Add language tags to code fences.

Low-impact actions:
- Minor wording polish after coverage and correctness are already good.
