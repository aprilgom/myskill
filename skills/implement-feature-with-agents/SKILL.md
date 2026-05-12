---
name: implement-feature-with-agents
description: Use when asked to implement a feature end-to-end with agents, delegation, or parallel work, including branch isolation, TDD, bounded subagent tasks, review gates, coherent commits, verification, and a GitHub pull request.
---

# Implement Feature With Agents

## Overview

Run feature implementation as a controlled delivery workflow: isolate the branch, plan the work, drive behavior with TDD, delegate independent tasks when authorized, review before integration, commit in coherent units, review the PR message, then publish a draft PR.

This is an orchestration skill. It does not replace the underlying skills; it requires using them in the order below.

## Preconditions

- If the user explicitly invokes `$implement-feature-with-agents`, or explicitly asks for multi-agent, delegated, or parallel-agent implementation, subagent use is authorized where it materially helps.
- If the user asks for ordinary feature work without mentioning this skill or subagents, do not spawn subagents yet. Ask for confirmation before using multi-agent execution.
- If the user provides multiple feature tasks and asks which can run concurrently, use `$parallel-feature-orchestrator` first to classify conflicts and sequencing.
- If the repository is not a git repository or has no GitHub remote, complete local work where possible and report the PR blocker.
- If the task is a small, tightly coupled change, use this workflow locally and explain why delegation was not useful.

## Workflow

### 1. Establish Scope

Use `superpowers:brainstorming` when requirements, UX, behavior, or acceptance criteria are unclear. Produce a short implementation plan with testable tasks before editing code.

Use `superpowers:writing-plans` for multi-step work where tasks need to be tracked across files or commits.

### 2. Isolate the Branch

Use `superpowers:using-git-worktrees` before implementation. Create an isolated worktree and feature branch, run project setup, and verify the baseline test command when the project exposes one.

If worktree setup is blocked, create or switch to an appropriate feature branch in the current checkout only after explaining the deviation.

### 3. Drive Each Behavior with TDD

Use `superpowers:test-driven-development` for every behavior change.

For each task:

1. Write the smallest meaningful failing test.
2. Run the focused test and confirm it fails for the expected reason.
3. Implement the smallest code change that passes.
4. Run the focused test and relevant broader checks.
5. Refactor only while tests stay green.

Do not allow implementation-only task prompts. Every implementer subagent must be told to show the RED and GREEN verification commands and outcomes.

### 4. Delegate Independent Tasks

Use `superpowers:subagent-driven-development` when the plan has independent tasks and subagent use is authorized.

Before spawning workers, identify:

- the immediate task the main agent will do locally
- independent tasks that can run in parallel without blocking that local task
- each worker's owned files, modules, or responsibility boundary
- the exact RED/GREEN evidence each worker must report

Assign each implementer a bounded ownership area. Tell workers they are not alone in the codebase, must not revert unrelated edits, and must adapt to concurrent changes.

For tightly coupled work, keep implementation local and use review subagents only after coherent checkpoints.

### 5. Review Gates

Use `superpowers:requesting-code-review` after each task or coherent checkpoint, and before final publication.

Review order:

1. Spec compliance: the implementation matches the requested behavior and adds no unrequested surface area.
2. Code quality: correctness, maintainability, error handling, tests, and integration risk.
3. Final review: the full branch is consistent after all commits are present.

Fix Critical and Important findings before continuing. If a reviewer is wrong, push back with code or test evidence rather than accepting blindly.

### 6. Commit Intentionally

Create commits at review-approved boundaries:

- One commit per coherent behavior or refactor.
- Keep test changes with the behavior they prove.
- Avoid mixing unrelated cleanup with feature work.
- Do not stage unrelated user changes.

Before each commit, inspect `git status -sb` and the staged diff. Prefer explicit file paths when staging.

### 7. Verify Before Publishing

Use `superpowers:verification-before-completion` before claiming the work is done.

Run the strongest practical validation available in the repo, typically:

- focused tests touched by the feature
- full unit test suite
- lint/typecheck/build where available
- browser verification for frontend behavior

Report any skipped checks with the concrete reason.

### 8. Preserve Codex Readiness

Before publishing, check whether the feature changed Codex-readiness surfaces:

- new or moved modules, packages, services, routes, commands, tests, fixtures, or public APIs
- changed setup, install, lint, test, typecheck, build, browser verification, known failures, or done criteria
- changed architecture, dependency boundaries, generated files, migrations, env vars, safety rules, ownership boundaries, or agent instructions

If any readiness-sensitive surface changed, update the relevant context before PR publication:

- `AGENTS.md` or `CODEX.md` for agent navigation, quick commands, ownership, known failures, done criteria, and safety boundaries
- `README.md` for user-facing setup or workflow changes
- `ARCHITECTURE.md` or `docs/architecture.md` for structure, public contracts, dependencies, or cross-module behavior
- PR body for RED/GREEN evidence, review gates, skipped checks, known limitations, and final verification results

When the repository uses `$codex-readiness-cartography`, treat readiness preservation as part of done criteria. Do not publish without either updating affected context/docs or explicitly recording why no update was needed. Do not run a full cartography audit unless the user asks for it; use existing cartography artifacts, context docs, and changed readiness surfaces as done-criteria signals.

### 9. Draft and Review the PR Message

Before publishing, write the PR title and body as a reviewable draft. The PR body must summarize:

- what changed
- why it changed
- user/developer impact
- validation commands and outcomes
- known limitations or skipped checks

Review the PR message before opening the PR. The review must check:

- accuracy against the final diff and commits
- clear explanation of user/developer impact
- complete validation evidence, including skipped checks and reasons
- honest known limitations or follow-up work
- when written in Korean, terminology that Korean developers commonly use for the project context, avoiding awkward literal translations unless the repository already uses them
- no overclaiming, unrelated detail, or missing review-gate outcomes

Fix Critical and Important PR message findings before publishing. If the PR is created with a known documentation gap, record the reason in the PR body and final summary.

### 10. Publish the PR

Use `github:yeet` only after scope, commits, verification, and PR message review are clear. Push the branch and open a draft PR unless the user explicitly asks for ready-for-review.

## Stop Conditions

Stop and ask the user before proceeding when:

- subagent use is needed but was not explicitly authorized
- baseline tests fail before implementation
- unrelated working-tree changes overlap with files that must be edited
- the implementation plan reveals a product or architecture decision the user has not made
- publishing requires credentials, remotes, or permissions that are unavailable

## Common Pitfalls

- Do not delegate the next blocking task if the main agent cannot continue until it returns.
- Do not ask implementer agents to make broad, repo-wide changes without a file or module boundary.
- Do not accept a worker result that lacks the failing RED run and passing GREEN run for its behavior change.
- Do not publish a PR with uncommitted implementation changes, unresolved review findings, or undocumented skipped checks.
- Do not publish a PR before the title and body have been reviewed for accuracy, evidence, limitations, and overclaiming.
- Do not publish after changing repo navigation, commands, public contracts, or safety boundaries without updating context/docs or stating why no update was needed.
- Do not let a draft PR replace the final local verification summary.

## Completion Criteria

The task is complete only when:

- branch isolation or a documented fallback is in place
- required behavior is covered by tests that were seen fail first
- implementation and reviews are complete
- commits are split into coherent units
- verification has been run and summarized
- Codex-readiness surfaces are updated or explicitly recorded as unchanged
- PR title/body draft has been reviewed and any blocking message findings are fixed
- a draft PR is open, or the exact PR blocker is reported

## Output Format

```markdown
**Branch/PR**
- Branch: <branch or documented fallback>
- PR: <draft PR URL or blocker>

**Changed**
- <coherent behavior or refactor shipped>
- <coherent behavior or refactor shipped>

**Validation**
- <command> - <RED/GREEN/broader check outcome>
- <command> - <outcome>

**Review**
- <review gate run and result>
- <PR message review run and result>
- <Critical/Important findings fixed, or "No blocking findings">

**Codex Readiness**
- Readiness-sensitive surfaces changed: <yes/no>
- Context/docs updated: <files or "not needed">
- Verification evidence preserved: <where recorded>
- Remaining readiness risk: <none / known gap>

**Notes**
- <skipped check, limitation, or "None">

**Follow-Up Actions**
- <next action for any blocker, skipped check, or "None">
```
