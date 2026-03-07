#!/usr/bin/env bash
set -euo pipefail

# Continuous non-interactive demo run with no permission prompts.
# Retries on transient failures until success.

TOPIC="${*:-}"
if [ -n "$TOPIC" ]; then
    PROMPT="/demo $TOPIC"
else
    PROMPT="/demo"
fi

attempt=1
while true; do
    echo "Starting demo attempt #$attempt"
    if claude --permission-mode bypassPermissions --dangerously-skip-permissions -p "$PROMPT"; then
        echo "Demo completed successfully on attempt #$attempt"
        exit 0
    fi

    echo "Demo attempt #$attempt failed. Retrying in 3 seconds..."
    attempt=$((attempt + 1))
    sleep 3
done
