#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SKILL_NAME="supersplat-workflow"
TARGET="${CODEX_HOME:-$HOME/.codex}/skills/$SKILL_NAME"
SOURCE="$ROOT/plugins/splat-transform-for-lcc/skills/$SKILL_NAME"

mkdir -p "$(dirname "$TARGET")"

if [[ -e "$TARGET" && ! -L "$TARGET" ]]; then
  echo "Refusing to overwrite non-symlink target: $TARGET" >&2
  exit 1
fi

ln -sfn "$SOURCE" "$TARGET"
echo "Installed $SKILL_NAME -> $TARGET"
