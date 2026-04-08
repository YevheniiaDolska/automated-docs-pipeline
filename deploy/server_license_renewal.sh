#!/usr/bin/env bash
# Run server-side license auto-renew batch (hybrid/cloud clients).
#
# Expected server layout:
#   /opt/veridoc (repo root)
#   docker compose -f docker-compose.production.yml

set -euo pipefail

ROOT_DIR="${1:-/opt/veridoc}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
LOG_DIR="/var/log/veridoc"
mkdir -p "$LOG_DIR"

cd "$ROOT_DIR"

stamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "[license-renew] start ${stamp}" | tee -a "$LOG_DIR/license_renewal.log"

docker compose -f "$COMPOSE_FILE" exec -T api python3 -c \
  "import json; from gitspeak_core.api.billing import run_license_autorenew_batch; from gitspeak_core.db.engine import get_session; session=get_session(); print(json.dumps(run_license_autorenew_batch(session), ensure_ascii=True)); session.close()" \
  | tee -a "$LOG_DIR/license_renewal.log"

echo "[license-renew] done $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG_DIR/license_renewal.log"
