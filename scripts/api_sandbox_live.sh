#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-status}"
PROJECT_SLUG="${2:-taskstream}"
SPEC_PATH="${3:-./api/openapi.yaml}"
PORT="${4:-4010}"

export API_SANDBOX_NAME="api-sandbox-live-${PROJECT_SLUG}"
export API_SANDBOX_SPEC="${SPEC_PATH}"
export API_SANDBOX_PORT="${PORT}"

case "${ACTION}" in
  up)
    docker compose -f docker-compose.api-sandbox.live.yml up -d
    echo "Live sandbox up: name=${API_SANDBOX_NAME}, port=${API_SANDBOX_PORT}, spec=${API_SANDBOX_SPEC}"
    ;;
  down)
    docker compose -f docker-compose.api-sandbox.live.yml down
    echo "Live sandbox down: name=${API_SANDBOX_NAME}"
    ;;
  restart)
    docker compose -f docker-compose.api-sandbox.live.yml down
    docker compose -f docker-compose.api-sandbox.live.yml up -d
    echo "Live sandbox restarted: name=${API_SANDBOX_NAME}"
    ;;
  status)
    docker ps --filter "name=${API_SANDBOX_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    ;;
  logs)
    docker logs -f "${API_SANDBOX_NAME}"
    ;;
  *)
    echo "Usage: scripts/api_sandbox_live.sh {up|down|restart|status|logs} [project_slug] [spec_path] [port]"
    exit 2
    ;;
esac
