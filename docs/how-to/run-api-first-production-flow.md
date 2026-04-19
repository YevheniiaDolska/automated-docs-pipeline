---
title: Run API-first production flow
description: Generate OpenAPI from planning notes, run full lint and self-verification,
  publish playground assets, and keep a sandbox ready for client testing.
content_type: how-to
product: both
tags:
- How-To
- Cloud
- Self-hosted
last_reviewed: '2026-03-17'
app_version: '3.1'
original_author: Developer
---


<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

# Run API-first production flow

This flow turns planning notes into a validated OpenAPI contract, generated stubs, and a testable sandbox with repeatable automation.

## Step 1: Prepare planning notes

Use this input artifact format:

```markdown
Project: **TaskStream**
API version: **v1**
Base URL: `https://api.taskstream.example.com/v1`
Status: Draft for OpenAPI writing
```

Store notes in `demos/api-first/taskstream-planning-notes.md`.

## Step 2: Run generation and verification

Run the universal flow command:

```bash
python3 scripts/run_api_first_flow.py \
  --project-slug taskstream \
  --notes demos/api-first/taskstream-planning-notes.md \
  --spec api/openapi.yaml \
  --spec-tree api/taskstream \
  --openapi-version 3.1.0 \
  --manual-overrides api/overrides/openapi.manual.yml \
  --regression-snapshot api/.openapi-regression.json \
  --docs-provider mkdocs \
  --verify-user-path \
  --mock-base-url https://<your-real-public-mock-url>/v1 \
  --generate-test-assets \
  --upload-test-assets \
  --auto-remediate \
  --max-attempts 3
```

The runner performs:

1. OpenAPI generation from notes.
1. Contract validation.
1. Spectral, Redocly, and Swagger CLI lint checks.
1. FastAPI stub generation.
1. Self-verification of operation coverage and user-path calls.
1. Finalize gate (`scripts/finalize_docs_gate.py`): iterative `lint -> fix -> lint` before completion.

For interactive confirmation before commit, add:

```bash
--ask-commit-confirmation
```

If you maintain multiple API versions, run one flow per version and publish to separate docs asset paths.
Example layout:

```text
api/v1/openapi.yaml -> docs/assets/api/v1/
api/v2/openapi.yaml -> docs/assets/api/v2/
```

Use overrides and regression snapshot as follows:

- `--manual-overrides`: keep advanced hand-crafted schema parts (`x-*`, `oneOf`, vendor extensions) across regeneration.
- `--regression-snapshot`: block unexpected contract drift.
- `--update-regression-snapshot`: refresh baseline snapshot only when intentional changes are approved.

## Test asset smart merge

When you pass `--generate-test-assets`, the pipeline generates contract test cases
from the OpenAPI spec into `reports/api-test-assets/api_test_cases.json`.
The generator uses a smart merge strategy that preserves manual and customized cases
across re-runs.

### How merge works

Each test case carries metadata fields:

| Field | Values | Purpose |
| --- | --- | --- |
| `origin` | `auto`, `manual` | Distinguishes generated cases from QA-written cases |
| `customized` | `true`, `false` | Marks auto cases that QA refined |
| `needs_review` | `true`, `false` | Flags customized cases affected by API changes |
| `review_reason` | text or `null` | Explains why the case requires review |
| `spec_hash` | 12-char hex | Fingerprint of the operation signature for change detection |

On every re-run the merge engine applies these rules:

1. **Manual cases** (`origin: manual`) survive every re-generation untouched.
1. **Customized auto cases** (`customized: true`) keep QA edits. If the API spec changed (different `spec_hash`), the case gets `needs_review: true` with a reason message.
1. **Pure auto cases** (`origin: auto`, `customized: false`) get overwritten with the latest generated version.
1. **Stale auto cases** for removed operations get dropped automatically.

### Add a manual business-logic case

Open `reports/api-test-assets/api_test_cases.json` and append a case to the `cases` array:

```json
{
  "id": "TC-manual-order-capacity-1",
  "title": "Order queue rejects when warehouse is at capacity",
  "suite": "Business Logic",
  "operation_id": "manual",
  "traceability": {"method": "POST", "path": "/orders", "operation_id": "manual"},
  "preconditions": ["Warehouse capacity is set to 500.", "Current queue has 500 items."],
  "steps": [
    "Send POST /orders with a new order payload.",
    "Verify the response returns 409 Conflict.",
    "Verify the error body includes a capacity_exceeded code."
  ],
  "expected_result": "Order is rejected with a capacity exceeded error.",
  "priority": "high",
  "type": "functional",
  "origin": "manual",
  "customized": false,
  "needs_review": false,
  "review_reason": null,
  "spec_hash": ""
}
```

Set `origin` to `manual` and leave `spec_hash` empty. The merge engine never overwrites or drops manual cases.

### Mark an auto case as customized

Find the auto-generated case you refined and set `customized` to `true`:

```json
{
  "id": "TC-get-tasks-by-task-id-positive",
  "customized": true,
  "steps": ["Your refined step 1.", "Your refined step 2."],
  "expected_result": "Your refined expected result."
}
```

On the next re-generation, the merge engine preserves your edits. If the underlying
API operation changes, the case gets `needs_review: true` so you know to verify
your custom steps still apply.

### Resolve needs_review flags

After re-generation, search the report for flagged cases:

```bash
python3 -c "
import json, sys
data = json.loads(open('reports/api-test-assets/api_test_cases.json').read())
flagged = [c for c in data['cases'] if c.get('needs_review')]
for c in flagged:
    print(f'{c[\"id\"]}: {c[\"review_reason\"]}')
if not flagged:
    print('No cases need review.')
"
```

For each flagged case, review the API changes, update steps if needed, then set
`needs_review` back to `false` and `review_reason` to `null`.

### Merge summary in the report

The generated report at `reports/api-test-assets/api_test_assets_report.json` includes
merge statistics:

```json
{
  "auto_cases": 143,
  "manual_cases": 1,
  "customized_cases": 1,
  "needs_review_cases": 0,
  "merge_stats": {
    "auto_kept": 139,
    "auto_updated": 3,
    "auto_new": 1,
    "auto_dropped": 0,
    "manual_preserved": 1,
    "customized_preserved": 1,
    "customized_flagged": 0
  }
}
```

## Step 3: Start sandbox for live testing

For contract-mock mode:

```bash
bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010
```

For no-Docker mode (local Prism mock):

```bash
bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010 prism
```

For public hosted sandbox mode (shared for all docs users):

```bash
API_SANDBOX_EXTERNAL_BASE_URL="https://<your-real-public-mock-url>/v1" \
bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010 external
```

Supported external services are provider-agnostic. You can use Postman Mock Servers, Stoplight-hosted Prism, Mockoon Cloud, or your own hosted Prism-compatible endpoint.

In external mode, run API-first verification against the same public URL:

```bash
python3 scripts/run_api_first_flow.py \
  --project-slug taskstream \
  --notes demos/api-first/taskstream-planning-notes.md \
  --spec api/openapi.yaml \
  --spec-tree api/taskstream \
  --verify-user-path \
  --mock-base-url "https://<your-real-public-mock-url>/v1" \
  --generate-test-assets \
  --upload-test-assets \
  --sync-playground-endpoint
```

`--sync-playground-endpoint` keeps `mkdocs.yml` playground `sandbox_base_url` aligned with your public mock URL.

For fully automatic Postman-managed external mock:

```bash
export POSTMAN_API_KEY="YOUR_POSTMAN_API_KEY"
export POSTMAN_WORKSPACE_ID="YOUR_WORKSPACE_ID"
# optional: export POSTMAN_COLLECTION_UID="YOUR_COLLECTION_UID"
# optional: export POSTMAN_MOCK_SERVER_ID="YOUR_EXISTING_MOCK_ID"
```

Then add these flags to the same flow command:

```text
--sandbox-backend external --auto-prepare-external-mock --external-mock-provider postman --external-mock-base-path /v1
```

If you want automatic upload to test-management tools, add environment variables:

```bash
export TESTRAIL_UPLOAD_ENABLED=true
export TESTRAIL_BASE_URL="https://<your-company>.testrail.io"
export TESTRAIL_EMAIL="qa-owner@company.com"
export TESTRAIL_API_KEY="YOUR_TESTRAIL_API_KEY"
export TESTRAIL_SECTION_ID="123"
# optional: export TESTRAIL_SUITE_ID="45"

export ZEPHYR_UPLOAD_ENABLED=true
export ZEPHYR_SCALE_API_TOKEN="YOUR_ZEPHYR_TOKEN"
export ZEPHYR_SCALE_PROJECT_KEY="PROJ"
# optional: export ZEPHYR_SCALE_BASE_URL="https://api.zephyrscale.smartbear.com/v2"
# optional: export ZEPHYR_SCALE_FOLDER_ID="1001"
```

For prod-like mode on VPS:

```bash
bash scripts/api_prodlike_project.sh up taskstream 4011
```

## Step 4: Keep sandbox always on

Use Docker restart policy and health checks through:

- `docker-compose.api-sandbox.prodlike.yml`
- `restart: unless-stopped`
- built-in healthcheck on `/v1/healthz`

## Step 5: Apply multilingual examples baseline

Run these commands to keep code snippets aligned with the new docs standard:

```bash
python3 scripts/generate_multilang_tabs.py --paths docs templates --scope api --write
python3 scripts/validate_multilang_examples.py --docs-dir docs --scope api --required-languages curl,javascript,python
python3 scripts/check_code_examples_smoke.py --paths docs templates --allow-empty
python3 scripts/check_openapi_regression.py --spec api/openapi.yaml --spec-tree api/taskstream --snapshot api/.openapi-regression.json
```

Use this API request tab set as the baseline format for executable examples:

=== "cURL"

    ```bash
    curl -sS https://<your-real-public-mock-url>/v1/healthz
    ```

=== "JavaScript"

    ```javascript
    const res = await fetch("https://<your-real-public-mock-url>/v1/healthz");
    console.log(await res.json());
    ```

=== "Python"

    ```python
    import requests

    res = requests.get("https://<your-real-public-mock-url>/v1/healthz", timeout=10)
    print(res.json())
    ```

## Step 6: Stop sandbox when needed

```bash
bash scripts/api_sandbox_project.sh down taskstream ./api/openapi.yaml 4010
bash scripts/api_prodlike_project.sh down taskstream 4011
```

## Next steps

- [TaskStream API playground](../reference/taskstream-api-playground.md)
- [TaskStream API planning notes](../reference/taskstream-planning-notes.md)
