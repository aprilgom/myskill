#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
config_path="${LIVING_PLAN_CONFIG:-$repo_root/.living-plan/living-plan.env}"

if [[ ! -f "$config_path" ]]; then
	echo "missing living plan config: $config_path" >&2
	exit 2
fi

# shellcheck disable=SC1090
source "$config_path"

strip_cr() {
	printf '%s' "${1%$'\r'}"
}

PLAN_SCOPE="$(strip_cr "$PLAN_SCOPE")"
PLAN_KIND="$(strip_cr "$PLAN_KIND")"
PLAN_PATH="$(strip_cr "$PLAN_PATH")"
STATE_PATH="$(strip_cr "$STATE_PATH")"
SENSITIVE_PATH="$(strip_cr "$SENSITIVE_PATH")"

: "${PLAN_PATH:?PLAN_PATH is required}"
: "${STATE_PATH:?STATE_PATH is required}"
: "${SENSITIVE_PATH:?SENSITIVE_PATH is required}"
: "${PLAN_SCOPE:?PLAN_SCOPE is required}"
: "${PLAN_KIND:?PLAN_KIND is required}"

cd "$repo_root"
mkdir -p "$(dirname "$STATE_PATH")"

python3 - "$STATE_PATH" "$PLAN_PATH" "$SENSITIVE_PATH" "$PLAN_SCOPE" "$PLAN_KIND" <<'PY'
import datetime
import hashlib
import json
import os
import subprocess
import sys

state_path, plan_path, sensitive_path, scope, plan_kind = sys.argv[1:6]

def run(args):
    return subprocess.check_output(args, text=True)

def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
head = run(["git", "rev-parse", "HEAD"]).strip()

tracked = run(["git", "ls-files", "-s", "--", sensitive_path])
tracked = "\n".join(
    line for line in tracked.splitlines()
    if not line.endswith("\t" + state_path) and not line.endswith("\t" + plan_path)
) + "\n"

status = run(["git", "status", "--porcelain", "--", sensitive_path, plan_path, state_path])
status = "\n".join(
    line for line in status.splitlines()
    if not line[3:] in {state_path, plan_path}
) + "\n"

with open(plan_path, "rb") as f:
    plan_hash = hashlib.sha256(f.read()).hexdigest()

state = {
    "schema_version": 1,
    "scope": scope,
    "plan_kind": plan_kind,
    "plan_path": plan_path,
    "sensitive_path": sensitive_path,
    "plan_updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "plan_branch": branch,
    "plan_base_ref": head,
    "tracked_tree_hash": sha(tracked),
    "dirty_status_hash": sha(status),
    "plan_hash": plan_hash,
}

with open(state_path, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2, sort_keys=True)
    f.write("\n")

print(f"refreshed {state_path} for {scope} at {head[:12]}")
PY
