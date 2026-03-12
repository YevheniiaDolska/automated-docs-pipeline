#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export PYTHONUNBUFFERED=1

SANDBOX_BACKEND="${API_FIRST_DEMO_SANDBOX_BACKEND:-docker}"
MOCK_BASE_URL="${API_FIRST_DEMO_MOCK_BASE_URL:-}"
AUTO_PREPARE_EXTERNAL_MOCK="${API_FIRST_DEMO_AUTO_PREPARE_EXTERNAL_MOCK:-true}"

if [[ "${SANDBOX_BACKEND}" == "external" && -z "${MOCK_BASE_URL}" ]]; then
  MOCK_BASE_URL="$(python3 - <<'PY'
import yaml
from pathlib import Path

mkdocs = Path("mkdocs.yml")
if not mkdocs.exists():
    print("")
    raise SystemExit(0)
cfg = yaml.safe_load(mkdocs.read_text(encoding="utf-8")) or {}
extra = cfg.get("extra", {}) if isinstance(cfg, dict) else {}
plg = extra.get("plg", {}) if isinstance(extra, dict) else {}
api_pg = plg.get("api_playground", {}) if isinstance(plg, dict) else {}
endpoints = api_pg.get("endpoints", {}) if isinstance(api_pg, dict) else {}
url = endpoints.get("sandbox_base_url", "")
if not url and isinstance(extra, dict):
    legacy = extra.get("api_playground", {})
    if isinstance(legacy, dict):
        url = legacy.get("sandbox_base_url", "")
print(str(url).strip())
PY
)"
fi

if [[ -z "${MOCK_BASE_URL}" && "${SANDBOX_BACKEND}" != "external" ]]; then
  MOCK_BASE_URL="http://localhost:4010/v1"
fi

if [[ "${SANDBOX_BACKEND}" == "external" && -n "${MOCK_BASE_URL}" ]]; then
  export API_SANDBOX_EXTERNAL_BASE_URL="${MOCK_BASE_URL}"
fi

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
say "I will run a nine-stage API-first flow."
say "You will see planning notes, OpenAPI generation, contract/lint checks, stub generation, user-path verification, multilingual examples, glossary sync, retrieval evals, and JSON-LD knowledge graph generation."

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
if [[ "${SANDBOX_BACKEND}" == "external" ]]; then
  if [[ "${AUTO_PREPARE_EXTERNAL_MOCK}" == "true" && -z "${MOCK_BASE_URL}" ]]; then
    say "External mock URL is not preset. It will be auto-prepared in Stage 2-5 via Postman API."
  else
    say "Using external public sandbox endpoint: ${MOCK_BASE_URL}"
    bash scripts/api_sandbox_project.sh status taskstream ./api/openapi.yaml 4010 external
  fi
else
  say "Starting a product-specific mock server for TaskStream on port 4010 (backend=${SANDBOX_BACKEND})."
  bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010 "${SANDBOX_BACKEND}"
  say "Mock server is running. I will now execute the production flow."
fi

stage "STAGE 2-5/6: RUN UNIVERSAL API-FIRST FLOW"
api_flow_cmd=(
  python3 -u scripts/run_api_first_flow.py
  --project-slug taskstream
  --notes demos/api-first/taskstream-planning-notes.md
  --spec api/openapi.yaml
  --spec-tree api/taskstream
  --sandbox-backend "${SANDBOX_BACKEND}"
  --docs-provider mkdocs
  --inject-demo-nav
  --verify-user-path
  --mock-base-url "${MOCK_BASE_URL:-https://sandbox-api.example.com/v1}"
  --skip-generate-from-notes
  --auto-remediate
  --sync-playground-endpoint
  --max-attempts 3
)
if [[ "${SANDBOX_BACKEND}" == "external" && "${AUTO_PREPARE_EXTERNAL_MOCK}" == "true" ]]; then
  api_flow_cmd+=(
    --auto-prepare-external-mock
    --external-mock-provider postman
    --external-mock-base-path /v1
  )
fi
"${api_flow_cmd[@]}"

stage "STAGE 6/9: MULTI-LANGUAGE EXAMPLES BASELINE"
say "Generating multilingual code tabs and validating required language coverage."
python3 -u scripts/generate_multilang_tabs.py --paths docs templates --scope api --write
python3 -u scripts/validate_multilang_examples.py --docs-dir docs --scope api --required-languages curl,javascript,python

stage "STAGE 7/9: GLOSSARY SYNC"
say "Syncing glossary markers into glossary.yml for terminology governance."
python3 -u scripts/sync_project_glossary.py \
  --paths docs \
  --glossary glossary.yml \
  --report reports/glossary_sync_report.json \
  --write

stage "STAGE 8/9: RETRIEVAL QUALITY EVALS"
say "Running retrieval precision/recall/hallucination evals on the knowledge index."
python3 -u scripts/generate_knowledge_retrieval_index.py --modules-dir knowledge_modules --output docs/assets/knowledge-retrieval-index.json
python3 -u scripts/run_retrieval_evals.py \
  --index docs/assets/knowledge-retrieval-index.json \
  --auto-generate-dataset \
  --dataset-out reports/retrieval_eval_dataset.generated.yml \
  --report reports/retrieval_evals_report.json \
  --top-k 3 \
  --min-precision 0.5 \
  --min-recall 0.5 \
  --max-hallucination-rate 0.5

stage "STAGE 9/9: KNOWLEDGE GRAPH JSON-LD"
say "Generating lightweight ontology/graph layer for RAG and discovery."
python3 -u scripts/generate_knowledge_graph_jsonld.py \
  --modules-dir knowledge_modules \
  --output docs/assets/knowledge-graph.jsonld \
  --report reports/knowledge_graph_report.json \
  --min-graph-nodes 5

stage "DEMO COMPLETE"
if [[ "${SANDBOX_BACKEND}" == "external" ]]; then
  say "External sandbox endpoint remains available for all users: ${MOCK_BASE_URL}"
  say "No local sandbox process to stop."
else
  say "The mock server is still running for live client walkthrough."
  say "Use: bash scripts/api_first_demo_stop.sh after the meeting."
fi
