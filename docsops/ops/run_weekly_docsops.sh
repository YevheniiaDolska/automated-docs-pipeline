#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"
mkdir -p reports
if [[ -f ".env.docsops.local" ]]; then
  set -a
  . ".env.docsops.local"
  set +a
fi
MAX_ATTEMPTS=3
attempt=1
while true; do
  if python3 docsops/scripts/run_autopipeline.py --docsops-root docsops --reports-dir reports --since 7 --runtime-config docsops/config/client_runtime.yml --mode operator --auto-generate --local-engine auto; then
    break
  fi
  if [[ $attempt -ge $MAX_ATTEMPTS ]]; then
    echo "[docsops] weekly run failed after $MAX_ATTEMPTS attempts; see reports/AUTOPIPELINE_OUTPUT_INDEX.md" >&2
    exit 1
  fi
  attempt=$((attempt + 1))
  echo "[docsops] weekly run failed, retrying in 60s (attempt $attempt/$MAX_ATTEMPTS)..."
  sleep 60
done
