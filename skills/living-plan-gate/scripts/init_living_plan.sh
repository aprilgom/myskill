#!/usr/bin/env bash
set -euo pipefail

usage() {
	cat >&2 <<'EOF'
usage: init_living_plan.sh --scope NAME --plan-kind KIND --plan-path PATH --sensitive-path PATH --agent-link-path PATH [--no-git-hook] [--no-codex-hook]
EOF
	exit 2
}

scope=""
plan_kind=""
plan_path=""
sensitive_path=""
agent_link_path=""
install_git_hook=true
install_codex_hook=true

while [[ $# -gt 0 ]]; do
	case "$1" in
		--scope) scope="${2:-}"; shift 2 ;;
		--plan-kind) plan_kind="${2:-}"; shift 2 ;;
		--plan-path) plan_path="${2:-}"; shift 2 ;;
		--sensitive-path) sensitive_path="${2:-}"; shift 2 ;;
		--agent-link-path) agent_link_path="${2:-}"; shift 2 ;;
		--no-git-hook) install_git_hook=false; shift ;;
		--no-codex-hook) install_codex_hook=false; shift ;;
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

if [[ "$install_git_hook" == true ]]; then
	hooks_dir="$repo_root/.githooks"
	pre_commit="$hooks_dir/pre-commit"
	mkdir -p "$hooks_dir"
	if [[ ! -f "$pre_commit" ]]; then
		cat > "$pre_commit" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"

if [[ -x "$repo_root/.living-plan/scripts/pre_commit_plan_gate.sh" ]]; then
	"$repo_root/.living-plan/scripts/pre_commit_plan_gate.sh"
fi
EOF
	else
		python3 - "$pre_commit" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
needle = ".living-plan/scripts/pre_commit_plan_gate.sh"
if needle in text:
    raise SystemExit(0)

block = '''\

repo_root="$(git rev-parse --show-toplevel)"

if [[ -x "$repo_root/.living-plan/scripts/pre_commit_plan_gate.sh" ]]; then
\t"$repo_root/.living-plan/scripts/pre_commit_plan_gate.sh"
fi
'''

lines = text.splitlines()
insert_at = 1 if lines and lines[0].startswith("#!") else 0
for i, line in enumerate(lines):
    if line.strip() == "set -euo pipefail":
        insert_at = i + 1
        break
lines[insert_at:insert_at] = block.splitlines()
path.write_text("\n".join(lines) + "\n")
PY
	fi
	chmod +x "$pre_commit"
	git config core.hooksPath .githooks
fi

if [[ "$install_codex_hook" == true ]]; then
	codex_config="$repo_root/.codex/config.toml"
	mkdir -p "$(dirname "$codex_config")"
	if [[ ! -f "$codex_config" ]]; then
		cat > "$codex_config" <<'EOF'
[features]
hooks = true

[[hooks.UserPromptSubmit]]

[[hooks.UserPromptSubmit.hooks]]
type = "command"
command = "bash .living-plan/scripts/user_prompt_plan_gate.sh"
timeout = 10
statusMessage = "Checking living plan freshness"
EOF
	elif ! grep -Fq ".living-plan/scripts/user_prompt_plan_gate.sh" "$codex_config"; then
		python3 - "$codex_config" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
text = path.read_text()

if not re.search(r"(?m)^\[features\]\s*$", text):
    text = "[features]\nhooks = true\n\n" + text
elif re.search(r"(?ms)^\[features\]\s*$.*?^hooks\s*=", text):
    text = re.sub(
        r"(?ms)(^\[features\]\s*$.*?^hooks\s*=\s*)(?:true|false)",
        r"\1true",
        text,
        count=1,
    )
else:
    text = re.sub(
        r"(?m)^(\[features\]\s*)$",
        r"\1\nhooks = true",
        text,
        count=1,
    )

path.write_text(text.rstrip() + "\n")
PY
		cat >> "$codex_config" <<'EOF'

[[hooks.UserPromptSubmit]]

[[hooks.UserPromptSubmit.hooks]]
type = "command"
command = "bash .living-plan/scripts/user_prompt_plan_gate.sh"
timeout = 10
statusMessage = "Checking living plan freshness"
EOF
	fi
fi

"$script_dir/refresh_plan_state.sh"

cat <<EOF
installed living plan gate
  config: $install_dir/living-plan.env
  plan:   $plan_path
  state:  $state_path

Hook wiring:
  Git pre-commit: .githooks/pre-commit calls .living-plan/scripts/pre_commit_plan_gate.sh
  Codex UserPromptSubmit: .codex/config.toml calls .living-plan/scripts/user_prompt_plan_gate.sh
EOF
