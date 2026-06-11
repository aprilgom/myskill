---
name: living-plan-gate
description: Use when a repository needs an action plan, objective plan, migration plan, roadmap, current-work tracker, backlog, or implementation plan kept current before agent work starts or before commits land.
---

# Living Plan Gate

## Overview

Use this skill to install or operate a deterministic gate around a living plan.
The plan stays outside `AGENTS.md`; `AGENTS.md` only links to it.

The gate has two enforcement points:
- user-prompt gate: blocks relevant agent requests when the plan is stale.
- pre-commit gate: blocks commits that change sensitive files without updating the plan state.

## Plan Shape

The gate tracks one canonical `PLAN_PATH`, but that file may be an index. For
low-token agent work, prefer this split layout:

```text
docs/objective/action-plan.md     # canonical gate target and navigation index
docs/objective/current.md         # only the task currently in progress
docs/objective/backlog.md         # not_started work
docs/objective/action/*.md        # per-action evidence and next check
docs/objective/completed.md       # completed title index
docs/objective/completed/*.md     # completed evidence
docs/objective/decision.md        # decision title index
docs/objective/decision/*.md      # decision rationale
```

Use the split layout when a plan is expected to live across many sessions. Keep
`current.md` tiny; it should name only the active task and link to details. Move
`not_started` items to backlog. Keep completed and decision indexes at
title/link level, with evidence in dated detail files.

## Status Values

Use these exact English status values:

- `in_progress`: the task currently being worked.
- `not_started`: planned work that has not begun.
- `paused`: work that started but is intentionally stopped for now.

`current.md` should contain only `in_progress` work. `backlog.md` should contain
`not_started` work by default; use `paused` only when there is evidence that the
task was actually started and then stopped.

## Install

Run the bundled installer from the skill directory:

```sh
scripts/init_living_plan.sh \
  --scope <short-name> \
  --plan-kind <objective-action-plan|migration-plan|roadmap> \
  --plan-path <path/to/plan.md> \
  --sensitive-path <path-or-directory> \
  --agent-link-path <AGENTS.md>
```

Example:

```sh
scripts/init_living_plan.sh \
  --scope andex-go \
  --plan-kind objective-action-plan \
  --plan-path andex-go/docs/objective/action-plan.md \
  --sensitive-path andex-go \
  --agent-link-path andex-go/AGENTS.md
```

The installer creates `.living-plan/living-plan.env`, copies this skill's
bundled scripts into `.living-plan/scripts/`, creates the plan and state files,
inserts a short cross-link in the chosen agent context file, installs
`.githooks/pre-commit`, sets `core.hooksPath` to `.githooks`, and installs the
Codex prompt hook in `.codex/config.toml`. Hooks should call the copied
project-local scripts, not files under the skill directory. Use `--no-git-hook`
or `--no-codex-hook` only when the repository intentionally manages that hook
another way.

## Workflow

1. Run `.living-plan/scripts/check_plan_freshness.sh`.
2. If it fails, is missing, reports stale, reports `STALE_WORKTREE`, or cannot
   determine freshness, stop before editing code or plan files and report the
   blocker. Do not perform manual freshness fallback.
3. Read the canonical `PLAN_PATH`.
4. If the plan links to `current.md`, read `current.md` next and only follow its
   detail link unless the current task is blocked or complete.
5. Work on the active task. Do not read backlog, completed, or decision detail
   files unless needed for the current decision.
6. When an action is completed, skipped, reprioritized, or blocked, update the
   relevant index and detail file:
   - current work changes: update `current.md` and the active `action/*.md`.
   - future work changes: update `backlog.md`.
   - completion evidence: update `completed.md` and `completed/*.md`.
   - durable rationale: update `decision.md` and `decision/*.md`.
7. Run `.living-plan/scripts/refresh_plan_state.sh`.
8. Run `.living-plan/scripts/check_plan_freshness.sh` again and report the
   result.

## Goal Alias

The prompt hook supports a portable goal alias:

```text
/goal objective-current
/goal objective:current
```

When the prompt contains this alias, `user_prompt_plan_gate.sh` derives paths
from `PLAN_PATH` and injects a compact current/backlog/completed transition
summary. Keep this hook context short; detailed rules belong in the plan files
and the `objective` skill's nested workflows.

## Commands

Use the project-local scripts after installation:

```sh
.living-plan/scripts/check_plan_freshness.sh
.living-plan/scripts/refresh_plan_state.sh
.living-plan/scripts/user_prompt_plan_gate.sh
.living-plan/scripts/pre_commit_plan_gate.sh
```

Hook wiring is project-specific:
- Git: installed by default into `.githooks/pre-commit`.
- Codex hooks: installed by default into `.codex/config.toml`.

## Rules

- Do not use file mtimes for freshness.
- Do not manually edit living-plan files as a substitute for a successful
  project-local gate result.
- Treat `STALE_WORKTREE`, `STALE_PLAN`, `UNKNOWN`, `ERROR`, missing scripts,
  and non-zero exits as blocked states, not as invitations to inspect files and
  continue.
- Use git branch, `HEAD`, staged changes, tracked tree hash, dirty status hash,
  plan hash, and state JSON.
- The hook must run the check itself. Do not rely on an agent saying it checked.
- When an action is completed, skipped, reprioritized, or blocked, update the
  plan and run `refresh_plan_state.sh` before committing.
- For split plans, keep the canonical `PLAN_PATH` stable as the top-level
  navigation index; move detailed content to linked files.

## Validation

Before reporting success:

- `check_plan_freshness.sh` must report `FRESH`.
- `git diff --check` must pass for touched plan files.
- `current.md`, when present, must contain only `in_progress` work.
- `backlog.md`, when present, must contain `not_started` work unless a task is
  genuinely `paused`.
- Any detail link added to an index must point to an existing file.

## Script Roles

- `init_living_plan.sh`: installs project-local plan files and scripts.
- `check_plan_freshness.sh`: reports `FRESH` or a concrete stale reason.
- `refresh_plan_state.sh`: rewrites the state JSON from current git state.
- `user_prompt_plan_gate.sh`: blocks relevant user prompts when the plan is stale.
- `pre_commit_plan_gate.sh`: blocks commits missing required plan/state updates.

## Common Mistakes

- Putting the whole plan in `AGENTS.md`. Keep only a link there.
- Putting every plan detail in `action-plan.md`. Use it as an index when the
  plan grows.
- Letting `current.md` become a backlog. It should contain only active work.
- Hashing generated state files into their own state hash.
- Treating a stale `HEAD` as automatically wrong. It is a signal to inspect; the
  gate should name the mismatch so the next agent can refresh intentionally.
- Using a prompt keyword filter as the only control. The pre-commit hook is the
  stronger guard for repository changes.

## Report Shape

In the final response, include:

- plan files changed
- freshness result
- validation commands run
- any remaining stale reason or skipped check
