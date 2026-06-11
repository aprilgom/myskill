---
name: codex-current-session-token-efficiency
description: Use when the user asks where tokens were spent or wasted in the current Codex session, current thread, this conversation, or a just-finished goal, especially after seeing unexpectedly high usage.
---

# Codex Current Session Token Efficiency

Analyze only the active/current Codex session JSONL. Do not run the broader
project token-efficiency skill unless the user explicitly asks for project-wide
or historical analysis.

## Default Workflow

1. Run the bundled analyzer against the current repo:

```bash
python3 "$HOME/.codex/skills/codex-current-session-token-efficiency/scripts/analyze_current_session.py" \
  --repo "$(pwd)" \
  --out /tmp/codex_current_session_tokens.json
```

2. If the current thread id is known from a goal/update result, pass it:

```bash
python3 "$HOME/.codex/skills/codex-current-session-token-efficiency/scripts/analyze_current_session.py" \
  --thread-id "<thread-id>" \
  --out /tmp/codex_current_session_tokens.json
```

3. Report the `phase_totals` sorted by `total_tokens`, then the largest
   `events`. Mention `cached_input_tokens` separately so large total-token
   numbers are not mistaken for all-new context.

## What Counts As Waste

Treat these as likely waste, ordered by confidence:

- Scope mismatch: analyzing project/all sessions when the user asked current
  session/thread.
- Giant tool output: broad `rg`, `find`, `git diff`, or test output that was
  later truncated or only lightly used.
- Repeated verification after evidence was already enough for the exact scope.
- Subagent use for a task that was already effectively complete, unless the
  user explicitly requested subagents.
- Whole-repo tests when focused tests already prove a narrow docs or package
  change, unless final confidence requires the broad gate.

## Output Shape

Keep Korean final reports short:

```markdown
현재 세션 기준 총 <n> tokens입니다. cached input은 <n>이라 대부분은 재사용 컨텍스트였습니다.

낭비 가능성이 큰 순서:
1. <phase> - <tokens>, 이유 <waste_signal>
2. ...

가장 큰 단일 호출:
- line <line>: <tokens>, <label>
```

If the analyzer cannot find a current session, ask for a session file path or
thread id. Do not silently fall back to all project sessions.
