---
name: "todo:create"
description: Use when the user wants to add a new todo action, backlog item, follow-up action, next action, or not_started task to a split living-plan todo structure.
---

# Create Todo Action

## Purpose

Add a new todo action to a split living plan without making it current.

## CLI

Use `todo:init` first to ensure `TODO_CLI` is available. Then run:

```sh
"$TODO_CLI" create \
  --title "<title>" \
  --evidence "<user-provided reason or Needs evidence.>" \
  --next-check "<concrete next check>"
```

The CLI reads `.living-plan/living-plan.env`, chooses the next action rank,
creates `action/<rank>-<slug>.md`, adds a `not_started` backlog row, refreshes
plan state, and checks freshness.

## Status

New actions start as `not_started`. Do not add them to `current.md` unless the
user explicitly asks to start them now.

## No Manual Fallback

Do not manually edit living-plan files as a substitute for the CLI. If the CLI
or freshness gate fails, exits non-zero, reports `STALE_WORKTREE`, or cannot
determine freshness, stop and report the blocker. Unsupported custom ranks or
priority rationale changes are blocked until the CLI supports them or the user
authorizes a separate non-todo cleanup path.

## Guardrails

- Do not mark new actions `in_progress`.
- Do not invent evidence; ask or record "Needs evidence" if unclear.
- Do not renumber existing actions unless the user explicitly asks.
- Keep `current.md` unchanged unless the user explicitly asks to start the new action.

## Final Response

Report the CLI `action`, `detail`, and `freshness` fields, plus any missing
evidence.
