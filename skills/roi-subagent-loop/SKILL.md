---
name: roi-subagent-loop
description: Turn architecture/cartography ROI actions into small, bounded subagent tasks with read-only discovery, low-risk implementation slices, verification, and documentation follow-up. Use when the user asks to continue an ROI item, proceed with low-risk subagent work, split a large refactor by responsibility, or convert audit findings into safe incremental changes.
---

# ROI Subagent Loop

Use this skill to avoid re-writing the same long subagent prompt for every ROI action.

## Workflow

1. Restate the ROI item in one sentence.
2. Classify the next slice:
   - `read-only`: investigate boundaries, dependencies, tests, or risk.
   - `test-only`: add characterization or architecture tests without production edits.
   - `mechanical`: rename, move, extract, or constant cleanup with no behavior change.
   - `production`: one narrow behavior-preserving production split backed by tests.
   - `docs`: update architecture/context docs after completed code movement.
3. Define the safety box:
   - exact working directory
   - allowed files or packages
   - explicitly forbidden edits
   - expected verification command
   - rollback boundary, usually "do not touch unrelated dirty worktree changes"
4. Prefer read-only discovery before production edits when the next slice is unclear.
5. Keep each subagent task small enough to finish in one turn.
6. Require output with: changes made, commands run, risks, and next ROI slice.

## Prompt Template

```text
You are working in <absolute-working-directory>.

Goal: <one narrow ROI slice>.

Context:
- ROI item: <source audit/plan item>.
- Current known state: <brief facts only>.
- Dirty worktree policy: do not revert or rewrite unrelated changes.

Scope:
- Allowed: <files/packages/tests>.
- Forbidden: <files/packages/actions>.

Task:
1. Inspect only the needed files.
2. Make the smallest behavior-preserving change that satisfies the goal.
3. Add or update focused tests when appropriate.
4. Run <verification command>.

Report:
- Files changed
- Verification result
- Any residual risk
- Suggested next bounded slice
```

## When To Stop

Stop and report instead of editing when:

- the slice needs broad ownership decisions;
- the same file has unrelated active edits that would be hard to preserve;
- no focused verification command exists;
- the change would mix test cleanup, production movement, and docs in one task.
