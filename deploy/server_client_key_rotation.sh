#!/usr/bin/env bash
# Run per-client key rotation and JWT re-issuance batch.

set -euo pipefail

ROOT_DIR="${1:-/opt/veridoc}"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

stamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "[key-rotation] start ${stamp}" | tee -a "$LOG_DIR/client_key_rotation.log"

cd "$ROOT_DIR"

if docker ps --format '{{.Names}}' | grep -q '^veridoc-api'; then
  api_container="$(docker ps --format '{{.Names}}' | grep '^veridoc-api' | head -n 1)"
  docker exec "$api_container" \
    python3 scripts/run_client_key_rotation.py \
      --registry config/licensing/clients.yml \
      --report reports/client_key_rotation_report.json \
    | tee -a "$LOG_DIR/client_key_rotation.log"
else
  echo "[key-rotation] ERROR: veridoc api container is not running." | tee -a "$LOG_DIR/client_key_rotation.log"
  exit 1
fi

echo "[key-rotation] done $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG_DIR/client_key_rotation.log"
