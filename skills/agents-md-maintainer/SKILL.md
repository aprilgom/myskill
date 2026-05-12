---
name: agents-md-maintainer
description: Maintain Codex project context files such as AGENTS.md, CODEX.md, .agents.md, or local agent notes. Use when asked to audit, review, improve, refresh, trim, restructure, or maintain AGENTS.md as a context file; preserve concise, current, actionable instructions for future Codex runs without doing a full repository readiness dashboard. For current-session learning capture or "revise" requests, prefer revise-agents-md.
---

# AGENTS.md Maintainer

Use this skill to keep Codex-facing repository context accurate and useful through periodic review and targeted cleanup. The output should be a focused context-file change, not a broad architecture audit, code-quality report, dashboard, or session-end memory capture.

## Scope

Handle:

- Find and inspect `AGENTS.md`, `CODEX.md`, `.agents.md`, `.codex.md`, or explicitly provided agent context files.
- Add verified commands, setup notes, test/lint/build workflows, known failures, architecture pointers, safety boundaries, and project-specific conventions.
- Remove stale, duplicated, overly generic, or non-actionable text.
- Restructure a context file when the current organization makes future Codex work slower or riskier.

Do not:

- Score the whole repo for Codex readiness; use `codex-readiness-cartography` for that.
- Produce HTML dashboards or JSON score maps.
- Capture only the current session's learnings; use `revise-agents-md` for that.
- Rewrite README, architecture docs, or code unless the user explicitly asks.
- Add generic coding advice that belongs in global instructions rather than this repo.

## Workflow

1. Identify the target context file.
   - Prefer an explicitly named file.
   - Otherwise look for `AGENTS.md`, then `CODEX.md`, then `.agents.md` or `.codex.md`.
   - If none exists, propose creating `AGENTS.md` at the repo root.
2. Read existing context before editing.
   - Preserve accurate project-specific guidance.
   - Note stale commands, vague claims, missing critical workflows, and duplicated sections.
3. Verify facts against the repository.
   - Check manifests and scripts such as `package.json`, `pyproject.toml`, `Makefile`, `Cargo.toml`, `go.mod`, CI files, README, and docs.
   - Prefer commands that are visible in repo files or were actually run in the current session.
   - Mark uncertain items as candidates; do not write them as facts.
   - For detailed scoring guidance, read `references/quality-criteria.md` when a simple review is not enough.
4. Prepare a short change plan.
   - List what will be added, changed, removed, and why.
   - For non-trivial edits, show the plan before modifying the file.
5. Edit minimally.
   - Keep sections short and scannable.
   - Use concrete paths and commands.
   - Prefer bullets over prose.
   - Keep local-only or machine-specific details out of shared files unless the filename is clearly local.
   - For new files or major restructures, read `references/templates.md` and adapt the smallest matching template.
6. Validate the result.
   - Re-read the edited file.
   - Check that referenced paths still exist when possible.
   - Check that commands are copied exactly from verified sources or clearly labeled as known workflows.
7. Report changed file paths, the main updates, and any facts that still need manual confirmation.

## Reference Files

- Read `references/quality-criteria.md` for detailed AGENTS.md quality criteria, category weights, and review questions.
- Read `references/templates.md` when creating a new file, restructuring a weak file, or choosing sections for repo root versus package-level context.

## Output Format

For review-only requests:

```markdown
**Findings**
- <specific issue in the context file>

**Recommended Edits**
- <high-ROI edit>

**Not Edited**
- <why no file change was made, if applicable>
```

For edit requests:

```markdown
**Changed**
- <path>

**Updates**
- <main update>
- <main update>

**Verification**
- <what was checked>

**Needs Confirmation**
- <uncertain item or "None">
```
