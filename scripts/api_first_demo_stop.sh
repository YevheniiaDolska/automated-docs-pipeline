#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
bash scripts/api_sandbox_project.sh down taskstream ./api/openapi.yaml 4010
