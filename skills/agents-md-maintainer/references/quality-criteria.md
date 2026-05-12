# AGENTS.md Quality Criteria

Use this reference when a light edit is not enough and the context file needs a structured review. Treat scores as review aids, not a dashboard requirement.

## Categories

Total: 100 points.

| Category | Points | What Good Looks Like |
|---|---:|---|
| Commands and workflows | 20 | Exact install, test, lint, typecheck, build, sync, or deploy commands that match repo files or observed successful runs. |
| Architecture and navigation | 20 | Clear pointers to key directories, entrypoints, package boundaries, generated files, docs, and ownership areas. |
| Project-specific rules | 15 | Non-obvious conventions, gotchas, safety boundaries, local scripts, CI quirks, and change constraints future Codex runs should not rediscover. |
| Verification and done criteria | 15 | Concrete checks to run before completion, known failures, expected outputs, and when manual verification is needed. |
| Currency and evidence | 15 | Claims match manifests, CI, README, docs, or current session evidence; stale or speculative notes are removed or marked. |
| Concision and signal | 15 | Short, scannable bullets; little duplicated README content; no generic coding advice or long onboarding prose. |

## Review Questions

Commands and workflows:

- Are commands copied from `package.json`, `Makefile`, `pyproject.toml`, `Cargo.toml`, CI files, scripts, or verified shell history?
- Are package-manager assumptions explicit when the repo has multiple lockfiles or workspaces?
- Are slow, flaky, or environment-dependent checks labeled honestly?

Architecture and navigation:

- Can future Codex find the main source, tests, docs, generated output, and configuration without re-mapping the repo?
- Are monorepo package boundaries or app/service ownership rules visible?
- Are key files listed because they matter, not because they are obvious from `ls`?

Project-specific rules:

- Does the file capture rules that are easy to violate, such as generated files, migration policy, styling conventions, API boundaries, or forbidden edits?
- Are local gotchas stated as facts only when verified?
- Are secrets, credentials, destructive commands, and external services handled cautiously?

Verification and done criteria:

- Does the file say which checks matter for common changes?
- Does it distinguish unit, integration, browser, typecheck, lint, build, and manual checks when relevant?
- Are known failures paired with cause, scope, or date when that prevents confusion?

Currency and evidence:

- Do referenced paths still exist?
- Do command names still exist?
- Are old TODOs, temporary workarounds, and historical notes still useful?

Concision and signal:

- Can a future agent scan the file in under a minute?
- Would removing a paragraph lose actionable repo-specific knowledge?
- Is global advice removed unless the repo requires it?

## Severity Guide

- P1: Incorrect command, false safety guidance, stale path to core files, or missing critical verification command.
- P2: Missing architecture boundary, unclear setup path, duplicated/conflicting guidance, or broad stale section.
- P3: Minor wording, section ordering, small duplication, or template polish.

