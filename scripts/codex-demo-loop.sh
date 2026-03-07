#!/usr/bin/env bash
set -euo pipefail

# Continuous non-interactive demo run for Codex.
# Retries on transient failures until success.

TOPIC="${*:-}"

if [ -n "$TOPIC" ]; then
    PROMPT="Use the demo skill now with topic: $TOPIC"
else
    PROMPT="Use the demo skill now."
fi

attempt=1
while true; do
    echo "Starting Codex demo attempt #$attempt"
    if codex exec -a never -s workspace-write "$PROMPT"; then
        echo "Codex demo completed successfully on attempt #$attempt"
        exit 0
    fi

    echo "Codex demo attempt #$attempt failed. Retrying in 3 seconds..."
    attempt=$((attempt + 1))
    sleep 3
done
