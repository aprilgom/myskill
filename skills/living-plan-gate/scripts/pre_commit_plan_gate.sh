#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
config_path="${LIVING_PLAN_CONFIG:-$repo_root/.living-plan/living-plan.env}"

if [[ ! -f "$config_path" ]]; then
	echo "living plan config missing: $config_path" >&2
	exit 2
fi

# shellcheck disable=SC1090
source "$config_path"

strip_cr() {
	printf '%s' "${1%$'\r'}"
}

PLAN_PATH="$(strip_cr "$PLAN_PATH")"
STATE_PATH="$(strip_cr "$STATE_PATH")"
SENSITIVE_PATH="$(strip_cr "$SENSITIVE_PATH")"

: "${PLAN_PATH:?PLAN_PATH is required}"
: "${STATE_PATH:?STATE_PATH is required}"
: "${SENSITIVE_PATH:?SENSITIVE_PATH is required}"

cd "$repo_root"

staged="$(git diff --cached --name-only -- "$SENSITIVE_PATH" "$PLAN_PATH" "$STATE_PATH")"
if [[ -z "$staged" ]]; then
	exit 0
fi

staged_sensitive="$(git diff --cached --name-only -- "$SENSITIVE_PATH")"
if [[ -z "$staged_sensitive" ]]; then
	exit 0
fi

plan_staged=false
state_staged=false
while IFS= read -r path; do
	[[ "$path" == "$PLAN_PATH" ]] && plan_staged=true
	[[ "$path" == "$STATE_PATH" ]] && state_staged=true
done <<< "$staged"

if [[ "$plan_staged" != true || "$state_staged" != true ]]; then
	echo "living plan gate rejected commit." >&2
	echo "Sensitive changes under $SENSITIVE_PATH require staged updates to:" >&2
	echo "  $PLAN_PATH" >&2
	echo "  $STATE_PATH" >&2
	echo "Run: .living-plan/scripts/refresh_plan_state.sh" >&2
	exit 1
fi

if ! "$repo_root/.living-plan/scripts/check_plan_freshness.sh" >/tmp/living-plan-precommit.out 2>&1; then
	cat /tmp/living-plan-precommit.out >&2
	echo "Refresh the plan state before committing." >&2
	exit 1
fi
