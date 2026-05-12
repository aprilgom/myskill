---
name: revise-agents-md
description: Capture useful learnings from the current Codex session into AGENTS.md, CODEX.md, .agents.md, .codex.md, or a local agent notes file. Use when the user says revise AGENTS.md, revise context, record what we learned, update memory, session learnings, 세션 학습, 오늘 배운 것, or asks to preserve discoveries from this conversation. Do not audit or restructure the whole context file.
---

# Revise AGENTS.md

Use this skill as a lightweight session-end memory capture workflow. It turns discoveries from the current conversation into short, durable context-file edits for future Codex runs.

## Boundary

Handle:

- Capture commands that were run or verified in this session.
- Capture repo-specific gotchas, hidden conventions, setup details, known failures, and safety boundaries discovered in this session.
- Add or update only the smallest relevant section in `AGENTS.md`, `CODEX.md`, `.agents.md`, `.codex.md`, or a local context file.

Do not:

- Audit, score, or restructure the whole context file; use `agents-md-maintainer` for that.
- Add broad best practices or generic Codex behavior.
- Add speculation, one-off debugging trails, or temporary failures without a stable cause.
- Write secrets, credentials, private local paths, or machine-specific details into shared files.

## Workflow

1. Review the current session.
   - Identify commands that succeeded, commands that failed for stable reasons, repo structure discoveries, hidden project rules, and user instructions that should persist.
   - Prefer facts grounded in command output, file inspection, test results, or explicit user direction.
2. Filter aggressively.
   - Keep only learnings likely to help a future Codex session.
   - Drop facts already obvious from README or existing context unless the existing context is wrong.
   - Drop anything that cannot be stated in one or two concise bullets.
3. Pick the target file.
   - Prefer an explicitly named file.
   - Otherwise use repo-root `AGENTS.md` if present, then `CODEX.md`, then `.agents.md` or `.codex.md`.
   - If no shared context file exists, propose creating `AGENTS.md`.
   - If the learning is local-only, prefer a clearly local file such as `.codex.local.md` when it exists; otherwise ask before writing local-only details.
4. Inspect before editing.
   - Avoid duplicates.
   - Update stale related bullets instead of appending a conflicting note.
   - Preserve the file's existing style and section names.
5. Propose the revision when more than a trivial one-line addition is needed.
   - Show candidate bullets and the target section.
   - Ask before writing if the target file does not exist or the learning may be sensitive/local-only.
6. Apply the minimal edit.
   - Add concise bullets under the closest existing section.
   - If no section fits, add a small section such as `Session Learnings`, `Working Rules`, `Testing Notes`, or `Commands`, matching the file's style.
7. Verify.
   - Re-read the changed area.
   - Confirm there are no duplicate or contradictory bullets.
   - Confirm any referenced paths or commands are accurate when possible.

## Learning Filter

Add the learning only if all are true:

- It is specific to this repo, workspace, or user workflow.
- It is likely to recur.
- It reduces future discovery time or prevents a likely mistake.
- It has evidence from this session or direct user instruction.
- It is concise enough to fit as one or two bullets.

Good examples:

- `./scripts/sync-to-codex.sh` installs tracked skills into `~/.codex/skills`.
- `quick_validate.py` needs `PyYAML`; if unavailable, use a frontmatter/TODO/manual file-existence smoke check and report the limitation.
- For this repo, new skills should live under `skills/<name>/SKILL.md` and be synced with `scripts/sync-to-codex.sh`.

Bad examples:

- "Be careful when editing files."
- "The test failed once."
- "Maybe the architecture should be refactored later."
- Long transcripts of debugging steps.

## Output Format

```markdown
**Changed**
- <path or "None">

**Captured**
- <learning added or updated>

**Skipped**
- <notable candidate skipped and why, if useful>

**Verification**
- <changed area re-read / duplicate check / path or command check>
```

