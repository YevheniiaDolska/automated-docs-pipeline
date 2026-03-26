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
while true; do
  if python3 docsops/scripts/run_weekly_gap_batch.py --docsops-root docsops --reports-dir reports --since 7; then
    break
  fi
  echo "[docsops] weekly run failed, retrying in 60s..."
  sleep 60
done
