#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_SRC="$REPO_ROOT/.claude/commands/demo.md"
CLAUDE_SKILL_SRC="$REPO_ROOT/.claude/skills/demo/SKILL.md"
CODEX_SKILL_SRC="$REPO_ROOT/.codex/skills/demo/SKILL.md"

if [[ ! -f "$CLAUDE_SRC" ]]; then
  echo "Missing source command: $CLAUDE_SRC" >&2
  exit 1
fi

if [[ ! -f "$CLAUDE_SKILL_SRC" ]]; then
  echo "Missing source skill: $CLAUDE_SKILL_SRC" >&2
  exit 1
fi

if [[ ! -f "$CODEX_SKILL_SRC" ]]; then
  echo "Missing source skill: $CODEX_SKILL_SRC" >&2
  exit 1
fi

mkdir -p "$HOME/.claude/commands"
mkdir -p "$HOME/.claude/skills/demo"
mkdir -p "$HOME/.codex/skills/demo"

cp "$CLAUDE_SRC" "$HOME/.claude/commands/demo.md"
cp "$CLAUDE_SKILL_SRC" "$HOME/.claude/skills/demo/SKILL.md"
cp "$CODEX_SKILL_SRC" "$HOME/.codex/skills/demo/SKILL.md"

echo "Installed Claude command: $HOME/.claude/commands/demo.md"
echo "Installed Claude skill: $HOME/.claude/skills/demo/SKILL.md"
echo "Installed Codex skill: $HOME/.codex/skills/demo/SKILL.md"
echo "Claude usage: /demo"
echo "Codex usage: demo (or \$demo)"
