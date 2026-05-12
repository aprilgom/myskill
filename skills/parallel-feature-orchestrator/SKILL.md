---
name: parallel-feature-orchestrator
description: Use when a user wants multiple feature requests or implementation tasks evaluated for safe parallel execution, especially when some tasks may conflict and low-conflict tasks should proceed with agent-based delivery.
---

# Parallel Feature Orchestrator

## Overview

Use this skill to triage a batch of feature tasks, run low-conflict groups in parallel, and handle medium- or high-conflict groups sequentially after notifying the user.

This is a coordination skill. It does not replace `$implement-feature-with-agents`; it decides task grouping, sequencing, and stop conditions before invoking it.

Do not use this skill for a single feature implementation unless the user asks whether parts of that feature should be split for concurrent execution.

## Inputs to Establish

Before implementation, identify:

- the requested task list and expected outcomes
- repository root, current branch, and dirty working tree state
- likely files, modules, packages, migrations, APIs, tests, and docs each task touches
- shared runtime surfaces such as schemas, config, auth, routing, build tooling, generated files, global styles, and public contracts
- Codex-readiness surfaces such as `AGENTS.md`, `CODEX.md`, setup/test/build commands, architecture docs, safety boundaries, known failures, and done criteria
- whether the user explicitly authorized subagents, delegated execution, or parallel implementation

If task intent or acceptance criteria are unclear, use `superpowers:brainstorming` before classifying conflicts.

## Conflict Classification

Classify each task pair as `low`, `medium`, or `high` conflict risk.

`low` risk:

- disjoint files or clearly separate modules
- independent tests and fixtures
- no shared API, schema, state, build config, generated artifact, or migration ordering
- one task can merge without forcing semantic changes in the other

`medium` risk:

- adjacent modules or shared helpers
- overlapping UI routes, styles, fixtures, mocks, or package-level exports
- possible integration contract changes
- likely mergeable, but requires an integration checkpoint before final review

`high` risk:

- same files or same public interfaces
- database migrations, generated clients, lockfiles, build config, or dependency changes
- cross-cutting refactors, auth/session changes, routing changes, global state changes, design system primitives, shared test harnesses
- one task depends on decisions or code from another

Treat unknown ownership as `medium` until inspected. Treat unclear product or architecture choices as a stop condition.

## Readiness Regression Risk

Classify Codex-readiness regression risk while classifying implementation conflict risk.

Treat a task as at least `medium` risk when it may change:

- agent or repo context files such as `AGENTS.md`, `CODEX.md`, `README.md`, architecture docs, PR templates, or CODEOWNERS
- setup, install, test, lint, typecheck, build, browser verification, known failures, or done criteria
- apps, packages, services, routes, public APIs, schemas, generated files, migrations, env vars, or safety boundaries

Treat readiness-sensitive tasks as `high` risk when two groups may update the same context file, command contract, public API, generated artifact, migration sequence, or architecture boundary.

Low-conflict implementation groups may still require one shared final readiness checkpoint when they change repo navigation, commands, architecture, safety guidance, or agent instructions.

## Grouping Rules

Create execution groups:

- Put `low` risk tasks in separate parallel groups when their ownership areas are bounded.
- Put `medium` and `high` risk tasks in sequential groups. Notify the user which tasks are not being parallelized and why before implementation starts.
- Split `high` risk tasks into prerequisite and follow-up tasks only when that reduces conflict risk without hiding a shared contract decision.
- Never assign two workers the same file, generated output, migration sequence, or shared contract unless one is explicitly read-only.

For each group, write:

- task name
- ownership area and expected files
- likely tests
- dependencies on other groups
- integration checkpoint
- readiness-sensitive surfaces changed, or "none expected"
- reason it is safe or unsafe to parallelize

## Workflow

1. Inspect the repository enough to map task ownership. Prefer `rg`, `rg --files`, package manifests, test directories, routes, and module exports.
2. Produce a short conflict matrix or grouped plan before editing code.
3. Ask the user before proceeding if parallel or delegated execution was not explicitly authorized.
4. Tell the user which groups will run in parallel and which `medium` or `high` groups will run sequentially, including the conflict reason for each sequential group.
5. For each low-conflict group, invoke `$implement-feature-with-agents` in parallel with the group's bounded scope and ownership.
6. After the parallel low-conflict groups finish and pass their checks, run all `medium` and `high` groups through `$implement-feature-with-agents` sequentially, in dependency order.
7. For every sequential group, run an integration checkpoint before starting the next group.
8. Integrate worker outputs into one final branch or PR sequence only after each group reports its branch/worktree, changed files, RED/GREEN evidence, and review status.
9. After all groups finish, run a readiness preservation checkpoint:
   - confirm context docs still point to valid files, commands, and ownership boundaries
   - update `AGENTS.md`, `CODEX.md`, README, architecture docs, or PR metadata when task groups changed navigation, workflows, shared contracts, or safety guidance
   - collect RED/GREEN, integration checkpoint, review, skipped-check, and final verification evidence
   - report whether readiness-sensitive surfaces changed and where the evidence was preserved
10. Run a final branch-level review and verification pass.

When invoking implementer agents, include:

- "You are not alone in the codebase."
- "Do not revert unrelated edits."
- "Keep changes inside this ownership area unless you report a blocker first."
- "Use TDD and report RED and GREEN commands and outcomes."
- "Adapt to concurrent changes rather than overwriting them."

## Stop Conditions

Stop and ask the user before implementation when:

- parallelism was not explicitly authorized
- tasks cannot be mapped to bounded ownership areas
- two or more tasks require the same files or shared contract
- baseline tests fail before implementation
- unrelated dirty changes overlap with required files
- a product, API, migration, or architecture decision is unresolved
- GitHub publishing is required but credentials, remotes, or permissions are unavailable

## Completion Criteria

The orchestration is complete only when:

- tasks are classified and grouped with conflict rationale
- Codex-readiness regression risk is classified for each group
- low-conflict groups have been routed through `$implement-feature-with-agents` in parallel where authorized
- medium/high-risk work has been announced to the user and handled sequentially with checkpoints
- readiness-sensitive docs, commands, and evidence have been updated or explicitly marked unchanged
- final integration review and verification have run
- draft PRs are opened where possible, or blockers are reported exactly

## Output Format

```markdown
**Groups**
- <task/group>: <parallel/sequential> - <conflict reason>

**Readiness Risk**
- <task/group>: <low/medium/high> - <readiness-sensitive surfaces or "none expected">

**Execution**
- Parallel groups: <completed / skipped with reason>
- Sequential groups: <completed / skipped with reason>
- Integration checkpoints: <summary>

**Validation**
- <command or review gate> - <outcome>

**Codex Readiness**
- Context/docs updated: <files or "not needed">
- Evidence preserved: <where RED/GREEN, review, skipped checks, and final verification are recorded>
- Remaining readiness risk: <none / known gap>

**PR/Blockers**
- <draft PR URL or exact blocker>
```
