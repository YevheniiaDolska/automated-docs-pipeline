#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-status}"
PROJECT_SLUG="${2:-taskstream}"
PORT="${3:-4011}"
DATA_DIR="${4:-./.data/prodlike-${PROJECT_SLUG}}"

export API_PRODLIKE_NAME="api-prodlike-${PROJECT_SLUG}"
export API_PRODLIKE_PORT="${PORT}"
export API_PRODLIKE_DATA_DIR="${DATA_DIR}"

case "${ACTION}" in
  up)
    mkdir -p "${API_PRODLIKE_DATA_DIR}"
    LOG_FILE="$(mktemp)"
    if ! docker compose -f docker-compose.api-sandbox.prodlike.yml up -d >"${LOG_FILE}" 2>&1; then
      echo "Prod-like sandbox startup failed. Last log lines:"
      tail -n 40 "${LOG_FILE}" || true
      rm -f "${LOG_FILE}" || true
      exit 1
    fi
    rm -f "${LOG_FILE}" || true
    echo "Prod-like sandbox up: name=${API_PRODLIKE_NAME}, port=${API_PRODLIKE_PORT}, data=${API_PRODLIKE_DATA_DIR}"
    docker ps --filter "name=${API_PRODLIKE_NAME}" --format "status={{.Status}} ports={{.Ports}}"
    ;;
  down)
    LOG_FILE="$(mktemp)"
    if ! docker compose -f docker-compose.api-sandbox.prodlike.yml down >"${LOG_FILE}" 2>&1; then
      echo "Prod-like sandbox shutdown failed. Last log lines:"
      tail -n 40 "${LOG_FILE}" || true
      rm -f "${LOG_FILE}" || true
      exit 1
    fi
    rm -f "${LOG_FILE}" || true
    echo "Prod-like sandbox down: name=${API_PRODLIKE_NAME}"
    ;;
  status)
    docker ps --filter "name=${API_PRODLIKE_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    ;;
  logs)
    docker logs --tail 120 "${API_PRODLIKE_NAME}"
    ;;
  *)
    echo "Usage: scripts/api_prodlike_project.sh {up|down|status|logs} [project_slug] [port] [data_dir]"
    exit 2
    ;;
esac
