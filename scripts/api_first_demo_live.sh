#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export PYTHONUNBUFFERED=1

# Load local docsops secrets automatically for demo runs.
# This file is gitignored and intended for local operator credentials.
if [[ -f ".env.docsops.local" ]]; then
  set -a
  # shellcheck disable=SC1091
  . ".env.docsops.local"
  set +a
fi

SANDBOX_BACKEND="${API_FIRST_DEMO_SANDBOX_BACKEND:-docker}"
MOCK_BASE_URL="${API_FIRST_DEMO_MOCK_BASE_URL:-}"
AUTO_PREPARE_EXTERNAL_MOCK="${API_FIRST_DEMO_AUTO_PREPARE_EXTERNAL_MOCK:-true}"
AUTO_DEPLOY="${API_FIRST_DEMO_AUTO_DEPLOY:-true}"
DEPLOY_WORKFLOW="${API_FIRST_DEMO_DEPLOY_WORKFLOW:-deploy.yml}"
DEPLOY_TIMEOUT_SECONDS="${API_FIRST_DEMO_DEPLOY_TIMEOUT_SECONDS:-1800}"

if [[ "${SANDBOX_BACKEND}" == "external" && "${AUTO_PREPARE_EXTERNAL_MOCK}" != "true" && -z "${MOCK_BASE_URL}" ]]; then
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

if [[ "${SANDBOX_BACKEND}" == "external" && "${AUTO_PREPARE_EXTERNAL_MOCK}" != "true" && -z "${MOCK_BASE_URL}" ]]; then
  echo "[error] External sandbox mode requires either API_FIRST_DEMO_MOCK_BASE_URL or API_FIRST_DEMO_AUTO_PREPARE_EXTERNAL_MOCK=true."
  exit 1
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

require_cmd() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    echo "[error] Required command is missing: $name"
    exit 1
  fi
}

build_playground_url() {
  python3 - <<'PY'
import yaml
from pathlib import Path

cfg = yaml.safe_load(Path("mkdocs.yml").read_text(encoding="utf-8")) or {}
site_url = str(cfg.get("site_url", "")).strip().rstrip("/")
if site_url:
    print(f"{site_url}/reference/taskstream-api-playground/")
else:
    print("/reference/taskstream-api-playground/")
PY
}

wait_for_deploy_success() {
  local workflow="$1"
  local head_sha="$2"
  local timeout_seconds="$3"
  local started elapsed run_id status conclusion run_sha
  started="$(date +%s)"
  while true; do
    run_line="$(gh run list --workflow "$workflow" --branch main --limit 20 --json databaseId,status,conclusion,headSha --jq '.[] | "\(.databaseId)|\(.status)|\(.conclusion // "none")|\(.headSha)"' | grep "$head_sha" | head -n1 || true)"
    if [[ -n "$run_line" ]]; then
      run_id="$(echo "$run_line" | cut -d'|' -f1)"
      status="$(echo "$run_line" | cut -d'|' -f2)"
      conclusion="$(echo "$run_line" | cut -d'|' -f3)"
      run_sha="$(echo "$run_line" | cut -d'|' -f4)"
      echo "[demo] ${workflow} -> run=${run_id} status=${status} conclusion=${conclusion} sha=${run_sha}"
      if [[ "$status" == "completed" && "$conclusion" == "success" ]]; then
        return 0
      fi
      if [[ "$status" == "completed" && "$conclusion" != "success" ]]; then
        echo "[error] ${workflow} failed for sha ${head_sha}"
        gh run view "$run_id" --log-failed || true
        return 1
      fi
    else
      echo "[demo] waiting for ${workflow} run for sha ${head_sha}..."
    fi
    elapsed="$(( $(date +%s) - started ))"
    if (( elapsed > timeout_seconds )); then
      echo "[error] timed out waiting for ${workflow} success (${timeout_seconds}s)"
      return 1
    fi
    sleep 20
  done
}

stage "API-FIRST LIVE DEMO: TASKSTREAM"
say "I will run an end-to-end API-first flow with generation, validation, deployment, and published sandbox verification."
say "You will see planning notes, OpenAPI generation, contract/lint checks, stub generation, user-path verification, and final MkDocs deployment with a working API sandbox."
say "Knowledge, glossary, retrieval evals, and JSON-LD graph run as a separate platform layer, not as API page content."

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
say "What happens now: the notes are converted into a machine-readable OpenAPI contract and split spec tree."
python3 -u scripts/generate_openapi_from_planning_notes.py \
  --notes demos/api-first/taskstream-planning-notes.md \
  --spec api/openapi.yaml \
  --spec-tree api/taskstream
say "Stage result: OpenAPI source files were generated at api/openapi.yaml and api/taskstream/."

stage "STAGE 1/5: START PROJECT MOCK SANDBOX"
say "What happens now: the pipeline prepares a sandbox endpoint used by API Try-it-out checks."
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
say "Stage result: sandbox mode is selected and the next stage will run contract and behavior checks."

stage "STAGE 2-5/6: RUN UNIVERSAL API-FIRST FLOW"
say "What happens now: run_api_first_flow executes contract validation, lint stack, stub generation, stub coverage check, and user-path verification."
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
  --mock-base-url "${MOCK_BASE_URL:-}"
  --skip-generate-from-notes
  --auto-remediate
  --sync-playground-endpoint
  --max-attempts 3
)
if [[ "${SANDBOX_BACKEND}" == "external" && "${AUTO_PREPARE_EXTERNAL_MOCK}" == "true" && -z "${MOCK_BASE_URL}" ]]; then
  api_flow_cmd+=(
    --auto-prepare-external-mock
    --external-mock-provider postman
    --external-mock-base-path /v1
  )
fi
"${api_flow_cmd[@]}"
if [[ "${SANDBOX_BACKEND}" == "external" && "${AUTO_PREPARE_EXTERNAL_MOCK}" == "true" ]]; then
  resolved_mock_url="$(python3 - <<'PY'
import json
from pathlib import Path
p = Path("reports/external_mock_resolution.json")
if p.exists():
    data = json.loads(p.read_text(encoding="utf-8"))
    print(str(data.get("mock_base_url", "")).strip())
else:
    print("")
PY
)"
  if [[ -n "${resolved_mock_url}" ]]; then
    MOCK_BASE_URL="${resolved_mock_url}"
    say "Stage result: Postman external mock resolved at ${MOCK_BASE_URL}."
  else
    say "Stage result: API-first validation flow passed."
  fi
else
  say "Stage result: API-first validation flow passed."
fi

stage "STAGE 6/10: GENERATE API TEST ASSETS"
say "Generating structured API test documentation from OpenAPI for QA tools."
say "What happens now: test cases, suites, preconditions, steps, expected results, and endpoint traceability are exported."
python3 -u scripts/generate_api_test_assets.py \
  --spec api/openapi.yaml \
  --output-dir reports/api-test-assets \
  --testrail-csv reports/api-test-assets/testrail_test_cases.csv \
  --zephyr-json reports/api-test-assets/zephyr_test_cases.json
say "Stage result: TestRail CSV and Zephyr JSON assets are ready in reports/api-test-assets."

stage "STAGE 7/10: MULTI-LANGUAGE EXAMPLES BASELINE"
say "Generating multilingual examples baseline for API usability."
say "What happens now: API examples are normalized into language tabs and validated for required language coverage."
python3 -u scripts/generate_multilang_tabs.py --paths docs templates --scope api --write
python3 -u scripts/validate_multilang_examples.py --docs-dir docs --scope api --required-languages curl,javascript,python
say "Stage result: API examples are available and validated for cURL, JavaScript, and Python."

stage "STAGE 8/10: GLOSSARY SYNC"
say "Running terminology governance sync as a platform-level quality layer."
say "What happens now: glossary markers from docs are synchronized into glossary.yml."
python3 -u scripts/sync_project_glossary.py \
  --paths docs \
  --glossary glossary.yml \
  --report reports/glossary_sync_report.json \
  --write
say "Stage result: terminology dictionary is synchronized."

stage "STAGE 9/10: RETRIEVAL QUALITY EVALS"
say "Running retrieval evals as separate knowledge-system quality telemetry."
say "What happens now: retrieval index is rebuilt and tested for precision, recall, and hallucination rate."
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
retrieval_summary="$(python3 - <<'PY'
import json
from pathlib import Path
p = Path("reports/retrieval_evals_report.json")
if not p.exists():
    print("retrieval eval report not found")
else:
    d = json.loads(p.read_text(encoding="utf-8"))
    print(f"precision={d.get('precision')} recall={d.get('recall')} hallucination_rate={d.get('hallucination_rate')}")
PY
)"
say "Stage result: ${retrieval_summary}."

stage "STAGE 10/10: KNOWLEDGE GRAPH JSON-LD"
say "Generating JSON-LD graph as a separate knowledge artifact, not injected into API document content."
say "What happens now: module relationships are exported into a lightweight JSON-LD graph file."
python3 -u scripts/generate_knowledge_graph_jsonld.py \
  --modules-dir knowledge_modules \
  --output docs/assets/knowledge-graph.jsonld \
  --report reports/knowledge_graph_report.json \
  --min-graph-nodes 5
graph_summary="$(python3 - <<'PY'
import json
from pathlib import Path
p = Path("reports/knowledge_graph_report.json")
if not p.exists():
    print("graph report not found")
else:
    d = json.loads(p.read_text(encoding="utf-8"))
    print(f"graph_nodes={d.get('graph_nodes')} edges={d.get('edge_count')} status={d.get('status')}")
PY
)"
say "Stage result: ${graph_summary}."

PLAYGROUND_URL="$(build_playground_url)"

if [[ "${AUTO_DEPLOY}" == "true" ]]; then
  stage "STAGE 11/13: COMMIT AND PUSH DEMO OUTPUT"
  say "What happens now: generated API-first artifacts are committed and pushed to main to trigger MkDocs deploy."
  require_cmd git
  require_cmd gh
  current_branch="$(git rev-parse --abbrev-ref HEAD)"
  if [[ "${current_branch}" != "main" ]]; then
    echo "[error] API-first live deploy stage requires main branch. Current branch: ${current_branch}"
    exit 1
  fi

  git add -A \
    api/openapi.yaml \
    api/taskstream \
    generated/api-stubs \
    docs/assets/api \
    docs/reference/taskstream-api-playground.md \
    mkdocs.yml \
    reports/external_mock_resolution.json \
    reports/glossary_sync_report.json \
    reports/retrieval_eval_dataset.generated.yml \
    reports/retrieval_evals_report.json \
    reports/knowledge_graph_report.json \
    docs/assets/knowledge-retrieval-index.json \
    docs/assets/knowledge-graph.jsonld || true

  if ! git diff --cached --quiet; then
    git commit -m "docs(api-first): refresh taskstream playground and published sandbox"
    git push origin main
    say "Stage result: changes committed and pushed."
  else
    say "No file changes to commit; continuing with deployed-site verification."
  fi

  stage "STAGE 12/13: WAIT FOR MKDOCS DEPLOY SUCCESS"
  say "What happens now: waiting for GitHub Actions deploy workflow to finish successfully."
  head_sha="$(git rev-parse HEAD)"
  wait_for_deploy_success "${DEPLOY_WORKFLOW}" "${head_sha}" "${DEPLOY_TIMEOUT_SECONDS}"
  say "Stage result: deploy workflow succeeded."

  stage "STAGE 13/13: VERIFY PUBLISHED SANDBOX PAGE"
  say "What happens now: checking the published MkDocs page and confirming sandbox wiring on the live site."
  if [[ "${PLAYGROUND_URL}" != /* ]]; then
    say "Checking published page: ${PLAYGROUND_URL}"
    page_html="$(curl -fsSL "${PLAYGROUND_URL}")"
    if ! grep -q "/assets/api/openapi.yaml" <<<"${page_html}"; then
      echo "[error] Published page does not include expected OpenAPI spec path."
      exit 1
    fi
    if [[ -n "${MOCK_BASE_URL}" ]] && ! grep -q "${MOCK_BASE_URL}" <<<"${page_html}"; then
      echo "[error] Published page does not include expected sandbox mock URL: ${MOCK_BASE_URL}"
      exit 1
    fi
    say "Published MkDocs page contains OpenAPI spec and sandbox endpoint."
  else
    echo "[error] site_url is not configured in mkdocs.yml, cannot verify published page."
    exit 1
  fi
else
  say "AUTO_DEPLOY is disabled; skipping commit/push/deploy verification stages."
fi

stage "DEMO COMPLETE"
say "Final summary: API-first document is generated, verified, deployed, and linked to a live sandbox endpoint."
if [[ "${SANDBOX_BACKEND}" == "external" ]]; then
  say "External sandbox endpoint remains available for all users."
  if [[ -n "${MOCK_BASE_URL}" ]]; then
    say "Sandbox base URL: ${MOCK_BASE_URL}"
  fi
  say "No local sandbox process to stop."
else
  say "The mock server is still running for live client walkthrough."
  say "Use: bash scripts/api_first_demo_stop.sh after the meeting."
fi
say "Sandbox page: ${PLAYGROUND_URL}"
