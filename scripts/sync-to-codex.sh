#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$repo_root/skills"
target_dir="${CODEX_HOME:-$HOME/.codex}/skills"

mkdir -p "$target_dir"
rsync -a --delete --exclude='.system/' "$source_dir/" "$target_dir/"

echo "Synced skills to $target_dir"
