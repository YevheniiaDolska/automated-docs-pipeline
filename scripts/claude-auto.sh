#!/usr/bin/env bash
set -euo pipefail

# Run Claude with permissions bypassed (no interactive confirmation prompts).
exec claude --permission-mode bypassPermissions --dangerously-skip-permissions "$@"
