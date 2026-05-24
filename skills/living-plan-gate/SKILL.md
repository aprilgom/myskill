---
name: living-plan-gate
description: Use when a repository needs an action plan, ROI plan, migration plan, roadmap, or implementation plan kept current before agent work starts or before commits land.
---

# Living Plan Gate

## Overview

Use this skill to install or operate a deterministic gate around a living plan.
The plan stays outside `AGENTS.md`; `AGENTS.md` only links to it.

The gate has two enforcement points:
- user-prompt gate: blocks relevant agent requests when the plan is stale.
- pre-commit gate: blocks commits that change sensitive files without updating the plan state.

## Install

Run the bundled installer from the skill directory:

```sh
scripts/init_living_plan.sh \
  --scope <short-name> \
  --plan-kind <roi-action-plan|migration-plan|roadmap> \
  --plan-path <path/to/plan.md> \
  --sensitive-path <path-or-directory> \
  --agent-link-path <AGENTS.md>
```

Example:

```sh
scripts/init_living_plan.sh \
  --scope andex-go \
  --plan-kind roi-action-plan \
  --plan-path andex-go/docs/roi-action-plan.md \
  --sensitive-path andex-go \
  --agent-link-path andex-go/AGENTS.md
```

The installer creates `.living-plan/living-plan.env`, copies scripts into
`.living-plan/scripts/`, creates the plan and state files, and inserts a short
cross-link in the chosen agent context file.

## Operate

Use the project-local scripts after installation:

```sh
.living-plan/scripts/check_plan_freshness.sh
.living-plan/scripts/refresh_plan_state.sh
.living-plan/scripts/user_prompt_plan_gate.sh
.living-plan/scripts/pre_commit_plan_gate.sh
```

Hook wiring is project-specific:
- Git: call `.living-plan/scripts/pre_commit_plan_gate.sh` from `.githooks/pre-commit` or `.git/hooks/pre-commit`.
- Andex/Codex hooks: configure `UserPromptSubmit` to run `.living-plan/scripts/user_prompt_plan_gate.sh`.

## Rules

- Do not use file mtimes for freshness.
- Use git branch, `HEAD`, staged changes, tracked tree hash, dirty status hash,
  plan hash, and state JSON.
- The hook must run the check itself. Do not rely on an agent saying it checked.
- When an action is completed, skipped, reprioritized, or blocked, update the
  plan and run `refresh_plan_state.sh` before committing.

## Script Roles

- `init_living_plan.sh`: installs project-local plan files and scripts.
- `check_plan_freshness.sh`: reports `FRESH` or a concrete stale reason.
- `refresh_plan_state.sh`: rewrites the state JSON from current git state.
- `user_prompt_plan_gate.sh`: blocks relevant user prompts when the plan is stale.
- `pre_commit_plan_gate.sh`: blocks commits missing required plan/state updates.

## Common Mistakes

- Putting the whole plan in `AGENTS.md`. Keep only a link there.
- Hashing generated state files into their own state hash.
- Treating a stale `HEAD` as automatically wrong. It is a signal to inspect; the
  gate should name the mismatch so the next agent can refresh intentionally.
- Using a prompt keyword filter as the only control. The pre-commit hook is the
  stronger guard for repository changes.
