#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export PYTHONUNBUFFERED=1

stage() {
  echo ""
  echo "============================================================"
  echo "$1"
  echo "============================================================"
}

say() {
  echo "[demo] $1"
}

stage "API-FIRST LIVE DEMO: TASKSTREAM"
say "I will run a six-stage API-first flow."
say "You will see planning notes, OpenAPI generation, contract/lint checks, stub generation, user-path verification, and the multilingual examples baseline."

stage "INPUT ARTIFACT: PLANNING NOTES PREVIEW"
say "This is the exact notes format the pipeline consumes."
echo "[demo] Notes header:"
sed -n '1,18p' demos/api-first/taskstream-planning-notes.md
echo ""
echo "[demo] Notes endpoint sample:"
sed -n '40,62p' demos/api-first/taskstream-planning-notes.md
echo ""
echo "[demo] Notes quality gates sample:"
sed -n '145,175p' demos/api-first/taskstream-planning-notes.md

stage "STAGE 0/5: GENERATE OPENAPI FROM PLANNING NOTES"
say "Generating OpenAPI files from planning notes."
python3 -u scripts/generate_openapi_from_planning_notes.py \
  --notes demos/api-first/taskstream-planning-notes.md \
  --spec api/openapi.yaml \
  --spec-tree api/taskstream

stage "STAGE 1/5: START PROJECT MOCK SANDBOX"
say "Starting a product-specific mock server for TaskStream on port 4010."
bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010
say "Mock server is running. I will now execute the production flow."

stage "STAGE 2-5/6: RUN UNIVERSAL API-FIRST FLOW"
python3 -u scripts/run_api_first_flow.py \
  --project-slug taskstream \
  --notes demos/api-first/taskstream-planning-notes.md \
  --spec api/openapi.yaml \
  --spec-tree api/taskstream \
  --docs-provider mkdocs \
  --inject-demo-nav \
  --verify-user-path \
  --mock-base-url http://localhost:4010/v1 \
  --skip-generate-from-notes \
  --auto-remediate \
  --max-attempts 3

stage "STAGE 6/6: MULTI-LANGUAGE EXAMPLES BASELINE"
say "Generating multilingual code tabs and validating required language coverage."
python3 -u scripts/generate_multilang_tabs.py --paths docs templates --scope api --write
python3 -u scripts/validate_multilang_examples.py --docs-dir docs --scope api --required-languages curl,javascript,python

stage "DEMO COMPLETE"
say "The mock server is still running for live client walkthrough."
say "Use: bash scripts/api_first_demo_stop.sh after the meeting."
