---
name: revise-sessions
description: Review recent Codex session logs to identify repeated user asks, repeated manual workflows, and automation candidates. Use when the user asks to look through recent Codex sessions, revise sessions, find recurring workflows, recommend or create skills, recommend or create custom subagents, or audit repeated CI, PR review, changelog, docs, release prep, debugging, and test-triage tasks.
---

# Revise Sessions

Use this skill to turn recent Codex history into a small set of practical automations. The goal is not to catalog everything; it is to identify repeated manual work and create only the useful skills or custom subagents.

## Workflow

1. Gather recent session evidence.
   - Prefer `scripts/summarize_sessions.py` with the default `~/.codex` sources.
   - If the script fails or the format has changed, inspect `~/.codex/history.jsonl`, `~/.codex/session_index.jsonl`, `~/.codex/archived_sessions/*.jsonl`, and relevant SQLite logs manually.
   - Focus on recent user asks, not assistant reasoning or boilerplate session metadata.
2. Cluster repeated asks.
   - Group by intent, not exact wording.
   - Give extra weight to CI failures, PR reviews, changelogs, docs updates, release prep, debugging, test triage, repo context maintenance, and repeated command sequences.
   - Ignore one-off curiosity, broad preferences, and tasks already covered well by an existing skill.
3. Decide the automation shape.
   - Suggest a skill when the repeat is a reusable workflow with steps, decision points, or durable instructions.
   - Suggest a custom subagent when the repeat is a bounded role or investigation task with a clear output, such as "inspect CI failure and report root cause" or "review PR for regressions".
   - Do not create both for the same need unless there is a clear division between orchestration and investigation.
4. Check for existing coverage.
   - Search `~/.codex/skills`, `~/.agents/skills`, project `AGENTS.md`, and available subagent configuration before creating anything.
   - Prefer updating or reusing an existing skill/subagent when it already covers most of the workflow.
5. Create only useful items.
   - Keep each new skill or subagent narrow, short, and easy to trigger.
   - Avoid speculative automations from weak evidence.
   - If evidence is suggestive but not strong, report it as a recommendation instead of creating files.
6. Validate and report.
   - For created skills, run `quick_validate.py` when available.
   - Re-read created files and check for placeholder text.
   - Summarize evidence, created items, skipped candidates, and validation.

## Evidence Standard

Treat a candidate as strong when at least two recent sessions show the same workflow or when one session shows a long manual sequence that is likely to recur.

For every created item, record:

- the repeated ask or workflow
- the evidence source, such as session IDs, dates, or representative prompt snippets
- why it should be a skill or subagent
- why existing skills/subagents were insufficient

Do not include secrets, private tokens, or long verbatim session transcripts in generated files.

## Script

Run:

```bash
python3 ~/.codex/skills/revise-sessions/scripts/summarize_sessions.py --days 21 --limit 80
```

Useful options:

- `--codex-home <path>`: read a non-default Codex home.
- `--days <n>`: restrict history by age when timestamps are available.
- `--limit <n>`: cap representative prompts in the report.
- `--json`: emit machine-readable JSON for follow-up processing.

Use the script output as evidence, then apply engineering judgment before creating anything.
