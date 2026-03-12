#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-status}"
PROJECT_SLUG="${2:-taskstream}"
SPEC_PATH="${3:-./api/openapi.yaml}"
PORT="${4:-4010}"
BACKEND="${5:-${API_SANDBOX_BACKEND:-docker}}"
EXTERNAL_BASE_URL="${API_SANDBOX_EXTERNAL_BASE_URL:-}"

export API_SANDBOX_NAME="api-sandbox-${PROJECT_SLUG}"
export API_SANDBOX_SPEC="${SPEC_PATH}"
export API_SANDBOX_PORT="${PORT}"
PID_FILE=".tmp/${API_SANDBOX_NAME}.pid"
LOG_FILE=".tmp/${API_SANDBOX_NAME}.log"

mkdir -p .tmp

is_pid_running() {
  if [[ ! -f "${PID_FILE}" ]]; then
    return 1
  fi
  local pid
  pid="$(cat "${PID_FILE}")"
  [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null
}

up_prism() {
  if [[ ! -f "${SPEC_PATH}" ]]; then
    echo "Error: OpenAPI spec path must be an existing file: ${SPEC_PATH}"
    exit 1
  fi
  if is_pid_running; then
    echo "Prism sandbox already running: pid=$(cat "${PID_FILE}") port=${API_SANDBOX_PORT}"
    return
  fi
  nohup npx -y @stoplight/prism-cli mock "${SPEC_PATH}" --host 0.0.0.0 --port "${PORT}" >"${LOG_FILE}" 2>&1 &
  echo $! >"${PID_FILE}"
  sleep 1
  if ! is_pid_running; then
    echo "Prism sandbox startup failed. Last log lines:"
    /usr/bin/tail -n 30 "${LOG_FILE}" || true
    rm -f "${PID_FILE}" || true
    exit 1
  fi
  echo "Prism sandbox up: name=${API_SANDBOX_NAME}, pid=$(cat "${PID_FILE}"), port=${API_SANDBOX_PORT}, spec=${API_SANDBOX_SPEC}"
}

down_prism() {
  if ! is_pid_running; then
    echo "Prism sandbox not running: name=${API_SANDBOX_NAME}"
    rm -f "${PID_FILE}" || true
    return
  fi
  local pid
  pid="$(cat "${PID_FILE}")"
  kill "${pid}" 2>/dev/null || true
  rm -f "${PID_FILE}" || true
  echo "Prism sandbox down: name=${API_SANDBOX_NAME}"
}

status_prism() {
  if is_pid_running; then
    echo "name=${API_SANDBOX_NAME} status=running pid=$(cat "${PID_FILE}") port=${API_SANDBOX_PORT}"
  else
    echo "name=${API_SANDBOX_NAME} status=stopped"
  fi
}

case "${ACTION}" in
  up)
    case "${BACKEND}" in
      docker)
        if [[ ! -f "${SPEC_PATH}" ]]; then
          echo "Error: OpenAPI spec path must be an existing file: ${SPEC_PATH}"
          exit 1
        fi
        TMP_LOG="$(mktemp)"
        if ! docker compose -f docker-compose.api-sandbox.yml up -d >"${TMP_LOG}" 2>&1; then
          echo "Sandbox startup failed. Last log lines:"
          /usr/bin/tail -n 30 "${TMP_LOG}" || true
          rm -f "${TMP_LOG}" || true
          exit 1
        fi
        rm -f "${TMP_LOG}" || true
        echo "Sandbox up: backend=docker name=${API_SANDBOX_NAME}, port=${API_SANDBOX_PORT}, spec=${API_SANDBOX_SPEC}"
        docker ps --filter "name=${API_SANDBOX_NAME}" --format "status={{.Status}} ports={{.Ports}}"
        ;;
      prism)
        up_prism
        ;;
      external)
        if [[ -z "${EXTERNAL_BASE_URL}" ]]; then
          echo "Error: API_SANDBOX_EXTERNAL_BASE_URL is required for backend=external"
          exit 1
        fi
        echo "External sandbox mode enabled: ${EXTERNAL_BASE_URL}"
        ;;
      *)
        echo "Unsupported backend: ${BACKEND}. Use docker|prism|external."
        exit 2
        ;;
    esac
    ;;
  down)
    case "${BACKEND}" in
      docker)
        TMP_LOG="$(mktemp)"
        if ! docker compose -f docker-compose.api-sandbox.yml down >"${TMP_LOG}" 2>&1; then
          echo "Sandbox shutdown failed. Last log lines:"
          /usr/bin/tail -n 30 "${TMP_LOG}" || true
          rm -f "${TMP_LOG}" || true
          exit 1
        fi
        rm -f "${TMP_LOG}" || true
        echo "Sandbox down: name=${API_SANDBOX_NAME}"
        ;;
      prism)
        down_prism
        ;;
      external)
        echo "External sandbox mode: no local process to stop"
        ;;
      *)
        echo "Unsupported backend: ${BACKEND}. Use docker|prism|external."
        exit 2
        ;;
    esac
    ;;
  status)
    case "${BACKEND}" in
      docker)
        docker ps --filter "name=${API_SANDBOX_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        ;;
      prism)
        status_prism
        ;;
      external)
        if [[ -n "${EXTERNAL_BASE_URL}" ]]; then
          echo "External sandbox mode: ${EXTERNAL_BASE_URL}"
        else
          echo "External sandbox mode is configured, but API_SANDBOX_EXTERNAL_BASE_URL is empty"
        fi
        ;;
      *)
        echo "Unsupported backend: ${BACKEND}. Use docker|prism|external."
        exit 2
        ;;
    esac
    ;;
  *)
    echo "Usage: scripts/api_sandbox_project.sh {up|down|status} [project_slug] [spec_path] [port] [backend]"
    echo "Backend: docker (default), prism (no Docker), external (public hosted mock URL)"
    exit 2
    ;;
esac
