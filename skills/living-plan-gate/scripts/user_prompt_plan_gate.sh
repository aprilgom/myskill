#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
config_path="${LIVING_PLAN_CONFIG:-$repo_root/.living-plan/living-plan.env}"

if [[ ! -f "$config_path" ]]; then
	printf '{"continue":true}\n'
	exit 0
fi

# shellcheck disable=SC1090
source "$config_path"

prompt="$(cat)"
scope="${PLAN_SCOPE:-}"
sensitive="${SENSITIVE_PATH:-}"

if [[ -n "$scope" || -n "$sensitive" ]]; then
	if ! printf '%s' "$prompt" | grep -Eiq "(${scope}|${sensitive}|living plan|roi plan|migration plan|roadmap|action plan)"; then
		printf '{"continue":true}\n'
		exit 0
	fi
fi

if output="$("$repo_root/.living-plan/scripts/check_plan_freshness.sh" 2>&1)"; then
	python3 - "$output" <<'PY'
import json
import sys
print(json.dumps({
    "continue": True,
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": "Living plan freshness check passed. " + sys.argv[1],
    },
}))
PY
else
	python3 - "$output" <<'PY'
import json
import sys
print(json.dumps({
    "decision": "block",
    "reason": "Living plan is stale or missing:\n" + sys.argv[1],
}))
PY
	exit 0
fi
