#!/usr/bin/env bash
set -euo pipefail

TOPIC="${*:-}"
PROMPT_FILE=".claude/commands/demo.md"

if [ ! -f "$PROMPT_FILE" ]; then
    echo "Missing $PROMPT_FILE" >&2
    exit 1
fi

if [ -n "$TOPIC" ]; then
    exec codex exec -a never -s workspace-write "Use the demo skill now with topic: $TOPIC"
fi

exec codex exec -a never -s workspace-write "Use the demo skill now."
