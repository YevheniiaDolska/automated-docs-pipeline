#!/usr/bin/env bash
set -euo pipefail

# Run Codex with no approval prompts inside workspace-write sandbox.
exec codex -a never -s workspace-write "$@"
