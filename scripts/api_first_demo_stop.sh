#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
SANDBOX_BACKEND="${API_FIRST_DEMO_SANDBOX_BACKEND:-docker}"
if [[ "${SANDBOX_BACKEND}" == "external" ]]; then
  echo "External demo sandbox mode: no local process to stop."
  exit 0
fi
bash scripts/api_sandbox_project.sh down taskstream ./api/openapi.yaml 4010 "${SANDBOX_BACKEND}"
