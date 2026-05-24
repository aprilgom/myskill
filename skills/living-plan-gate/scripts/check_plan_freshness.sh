#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
config_path="${LIVING_PLAN_CONFIG:-$repo_root/.living-plan/living-plan.env}"

if [[ ! -f "$config_path" ]]; then
	echo "MISSING_CONFIG: $config_path"
	exit 2
fi

# shellcheck disable=SC1090
source "$config_path"

: "${PLAN_PATH:?PLAN_PATH is required}"
: "${STATE_PATH:?STATE_PATH is required}"
: "${SENSITIVE_PATH:?SENSITIVE_PATH is required}"

cd "$repo_root"

if [[ ! -f "$PLAN_PATH" ]]; then
	echo "MISSING_PLAN: $PLAN_PATH"
	exit 2
fi

if [[ ! -f "$STATE_PATH" ]]; then
	echo "MISSING_STATE: $STATE_PATH"
	exit 2
fi

python3 - "$STATE_PATH" "$PLAN_PATH" "$SENSITIVE_PATH" <<'PY'
import hashlib
import json
import subprocess
import sys

state_path, plan_path, sensitive_path = sys.argv[1:4]

def run(args):
    return subprocess.check_output(args, text=True)

def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def state_get(state, key):
    value = state.get(key, "")
    return "" if value is None else str(value)

with open(state_path, "r", encoding="utf-8") as f:
    state = json.load(f)

branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
head = run(["git", "rev-parse", "HEAD"]).strip()

tracked = run(["git", "ls-files", "-s", "--", sensitive_path])
tracked = "\n".join(
    line for line in tracked.splitlines()
    if not line.endswith("\t" + state_path) and not line.endswith("\t" + plan_path)
) + "\n"
tracked_hash = sha(tracked)

status = run(["git", "status", "--porcelain", "--", sensitive_path, plan_path, state_path])
status = "\n".join(
    line for line in status.splitlines()
    if not line[3:] in {state_path}
) + "\n"
dirty_hash = sha(status)

with open(plan_path, "rb") as f:
    plan_hash = hashlib.sha256(f.read()).hexdigest()

failures = []
if state_get(state, "plan_branch") != branch:
    failures.append(f"STALE_BRANCH: state={state_get(state, 'plan_branch')} current={branch}")
if state_get(state, "plan_base_ref") != head:
    failures.append(f"STALE_HEAD: state={state_get(state, 'plan_base_ref')} current={head}")
if state_get(state, "tracked_tree_hash") != tracked_hash:
    failures.append("STALE_TRACKED_TREE")
if state_get(state, "dirty_status_hash") != dirty_hash:
    failures.append("STALE_WORKTREE")
if state_get(state, "plan_hash") != plan_hash:
    failures.append("STALE_PLAN_HASH")

if failures:
    print("\n".join(failures))
    sys.exit(1)

print(f"FRESH: scope={state_get(state, 'scope')} plan={plan_path} head={head[:12]}")
PY
