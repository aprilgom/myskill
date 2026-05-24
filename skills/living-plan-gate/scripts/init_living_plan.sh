#!/usr/bin/env bash
set -euo pipefail

usage() {
	cat >&2 <<'EOF'
usage: init_living_plan.sh --scope NAME --plan-kind KIND --plan-path PATH --sensitive-path PATH --agent-link-path PATH
EOF
	exit 2
}

scope=""
plan_kind=""
plan_path=""
sensitive_path=""
agent_link_path=""

while [[ $# -gt 0 ]]; do
	case "$1" in
		--scope) scope="${2:-}"; shift 2 ;;
		--plan-kind) plan_kind="${2:-}"; shift 2 ;;
		--plan-path) plan_path="${2:-}"; shift 2 ;;
		--sensitive-path) sensitive_path="${2:-}"; shift 2 ;;
		--agent-link-path) agent_link_path="${2:-}"; shift 2 ;;
		*) usage ;;
	esac
done

[[ -n "$scope" && -n "$plan_kind" && -n "$plan_path" && -n "$sensitive_path" && -n "$agent_link_path" ]] || usage

repo_root="$(git rev-parse --show-toplevel)"
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
install_dir="$repo_root/.living-plan"
script_dir="$install_dir/scripts"
state_path=".living-plan/${scope}-${plan_kind}.state.json"

cd "$repo_root"
mkdir -p "$script_dir" "$(dirname "$plan_path")" "$(dirname "$agent_link_path")"
cp "$skill_dir"/scripts/*.sh "$script_dir"/
chmod +x "$script_dir"/*.sh

cat > "$install_dir/living-plan.env" <<EOF
PLAN_SCOPE="$scope"
PLAN_KIND="$plan_kind"
PLAN_PATH="$plan_path"
STATE_PATH="$state_path"
SENSITIVE_PATH="$sensitive_path"
EOF

if [[ ! -f "$plan_path" ]]; then
	sed \
		-e "s/^# Living Plan/# ${scope} ${plan_kind}/" \
		-e "s/- scope:/- scope: ${scope}/" \
		-e "s/- plan_kind:/- plan_kind: ${plan_kind}/" \
		-e "s|- state_file:|- state_file: ${state_path}|" \
		-e "s|- freshness_check:|- freshness_check: .living-plan/scripts/check_plan_freshness.sh|" \
		"$skill_dir/assets/plan-template.md" > "$plan_path"
fi

if [[ ! -f "$agent_link_path" ]]; then
	touch "$agent_link_path"
fi

if ! grep -Fq "$plan_path" "$agent_link_path"; then
	{
		printf '\n'
		sed "s|PLAN_PATH|$plan_path|g" "$skill_dir/assets/agents-link-snippet.md"
	} >> "$agent_link_path"
fi

"$script_dir/refresh_plan_state.sh"

cat <<EOF
installed living plan gate
  config: $install_dir/living-plan.env
  plan:   $plan_path
  state:  $state_path

Optional hook wiring:
  Git pre-commit: call .living-plan/scripts/pre_commit_plan_gate.sh
  UserPromptSubmit: call .living-plan/scripts/user_prompt_plan_gate.sh
EOF
