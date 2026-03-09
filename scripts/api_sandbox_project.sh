#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-status}"
PROJECT_SLUG="${2:-taskstream}"
SPEC_PATH="${3:-./api/openapi.yaml}"
PORT="${4:-4010}"

export API_SANDBOX_NAME="api-sandbox-${PROJECT_SLUG}"
export API_SANDBOX_SPEC="${SPEC_PATH}"
export API_SANDBOX_PORT="${PORT}"

case "${ACTION}" in
  up)
    if [[ ! -f "${SPEC_PATH}" ]]; then
      echo "Error: OpenAPI spec path must be an existing file: ${SPEC_PATH}"
      exit 1
    fi
    LOG_FILE="$(mktemp)"
    if ! docker compose -f docker-compose.api-sandbox.yml up -d >"${LOG_FILE}" 2>&1; then
      echo "Sandbox startup failed. Last log lines:"
      tail -n 30 "${LOG_FILE}" || true
      rm -f "${LOG_FILE}" || true
      exit 1
    fi
    rm -f "${LOG_FILE}" || true
    echo "Sandbox up: name=${API_SANDBOX_NAME}, port=${API_SANDBOX_PORT}, spec=${API_SANDBOX_SPEC}"
    docker ps --filter "name=${API_SANDBOX_NAME}" --format "status={{.Status}} ports={{.Ports}}"
    ;;
  down)
    LOG_FILE="$(mktemp)"
    if ! docker compose -f docker-compose.api-sandbox.yml down >"${LOG_FILE}" 2>&1; then
      echo "Sandbox shutdown failed. Last log lines:"
      tail -n 30 "${LOG_FILE}" || true
      rm -f "${LOG_FILE}" || true
      exit 1
    fi
    rm -f "${LOG_FILE}" || true
    echo "Sandbox down: name=${API_SANDBOX_NAME}"
    ;;
  status)
    docker ps --filter "name=${API_SANDBOX_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    ;;
  *)
    echo "Usage: scripts/api_sandbox_project.sh {up|down|status} [project_slug] [spec_path] [port]"
    exit 2
    ;;
esac
