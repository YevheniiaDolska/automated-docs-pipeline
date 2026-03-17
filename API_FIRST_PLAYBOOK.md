---
title: "API-first and code-first playbook"
description: "Practical guide for API-first and code-first workflows with sandbox modes, contract checks, and documentation gates."
content_type: reference
product: both
last_reviewed: "2026-03-17"
tags:
  - Reference
  - API
  - Operations
---

# API-first and code-first playbook

This playbook explains how to manage documentation for products that expose APIs. It covers two workflows: API-first, where you write the OpenAPI specification before writing code, and code-first, where you extract the OpenAPI specification from existing code. Both workflows converge on the same quality gates, drift detection, and reference documentation pipeline.

## Two workflows, one quality bar

| Aspect | API-first | Code-first |
| --- | --- | --- |
| Source of truth | Hand-written OpenAPI spec in `api/openapi.yaml` | Running application code |
| How the spec arrives | Author writes it, then generates stubs | `npm run gaps:code` reads code, then generates spec |
| Mock server | `scripts/api_sandbox_project.sh` (`docker`, `prism`, or `external`) | Real endpoints tested directly |
| Scaffold generation | OpenAPI Generator via local flow (`run_api_first_flow.py`) | Not applicable (code exists) |
| Spectral lint | Runs on the hand-written spec | Runs on the generated spec |
| Reference docs | Generated from the spec | Generated from the spec |

Both paths produce an OpenAPI specification file. Once that file exists, every downstream check (Spectral lint, drift detection, DoD contract, consolidated report) works identically.

## API-first workflow

Use this workflow when you design the API contract before writing server code. The specification file drives code generation, mock servers, and documentation.

### Step 1: Write the OpenAPI specification

Create or edit `api/openapi.yaml`. Follow the OpenAPI quality rules enforced by `.spectral.yml` (see the Spectral rules section below).

### Step 2: Run the API-first flow end-to-end

Run the standard pipeline entry point:

```bash
python3 scripts/run_api_first_flow.py \
  --project-slug taskstream \
  --notes demos/api-first/taskstream-planning-notes.md \
  --spec api/openapi.yaml \
  --spec-tree api/taskstream \
  --docs-provider mkdocs \
  --verify-user-path \
  --mock-base-url "https://<your-real-public-mock-url>/v1" \
  --generate-test-assets \
  --upload-test-assets \
  --sync-playground-endpoint \
  --auto-remediate \
  --max-attempts 3
```

This generates OpenAPI artifacts, runs contract and lint checks, generates stubs, verifies user path, syncs docs sandbox URL, generates API test assets, and can upload those assets to TestRail/Zephyr.

### Step 3: Start sandbox mode

Docker mode:

```bash
bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010 docker
```

No-Docker local mode:

```bash
bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010 prism
```

Public hosted mode:

```bash
API_SANDBOX_EXTERNAL_BASE_URL="https://<your-real-public-mock-url>/v1" \
bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010 external
```

Supported external providers are not hardcoded. Typical options are Postman Mock Servers, Stoplight-hosted Prism, Mockoon Cloud, or self-hosted Prism.

### Step 3A: Fully automatic Postman setup (recommended)

Provide these environment variables once:

1. `POSTMAN_API_KEY`
1. `POSTMAN_WORKSPACE_ID`
1. optional `POSTMAN_COLLECTION_UID` (if missing, pipeline imports collection from generated OpenAPI)
1. Optional `POSTMAN_MOCK_SERVER_ID` (reuse existing mock)
1. Optional TestRail upload vars:
   `TESTRAIL_UPLOAD_ENABLED`, `TESTRAIL_BASE_URL`, `TESTRAIL_EMAIL`, `TESTRAIL_API_KEY`, `TESTRAIL_SECTION_ID`, optional `TESTRAIL_SUITE_ID`
1. Optional Zephyr upload vars:
   `ZEPHYR_UPLOAD_ENABLED`, `ZEPHYR_SCALE_API_TOKEN`, `ZEPHYR_SCALE_PROJECT_KEY`, optional `ZEPHYR_SCALE_BASE_URL`, optional `ZEPHYR_SCALE_FOLDER_ID`

Then run API-first flow with external mock auto-prepare:

```bash
python3 scripts/run_api_first_flow.py \
  --project-slug taskstream \
  --notes demos/api-first/taskstream-planning-notes.md \
  --spec api/openapi.yaml \
  --spec-tree api/taskstream \
  --sandbox-backend external \
  --auto-prepare-external-mock \
  --external-mock-provider postman \
  --external-mock-base-path /v1 \
  --verify-user-path \
  --generate-test-assets \
  --upload-test-assets \
  --sync-playground-endpoint
```

The pipeline creates or reuses Postman mock automatically and injects resolved URL into playground config.

### Step 4: Test against the selected sandbox

Send requests to your configured `mock_base_url` and fix the spec until responses match design intent.

### Step 5: Lint the specification with Spectral

```bash
npx @stoplight/spectral-cli lint api/openapi.yaml
```

Fix all errors before proceeding. See the Spectral rules section for the full rule set.

### Step 6: Write reference documentation

Use `templates/api-reference.md` as the base template. Place the new file in `docs/reference/` and update `mkdocs.yml` navigation.

## API test assets flow (OpenAPI -> TestRail/Zephyr)

Use this flow when QA teams need import-ready artifacts generated from OpenAPI and optional direct upload into test management systems.

### 1) Generate test assets from OpenAPI

Run either the API-first full flow with flags:

```bash
python3 scripts/run_api_first_flow.py \
  --project-slug taskstream \
  --notes demos/api-first/taskstream-planning-notes.md \
  --spec api/openapi.yaml \
  --spec-tree api/taskstream \
  --generate-test-assets
```

Or run the direct command:

```bash
npm run api:test:assets
```

Default outputs:

- `reports/api-test-assets/api_test_cases.json`
- `reports/api-test-assets/test_matrix.md`
- `reports/api-test-assets/testrail_test_cases.csv`
- `reports/api-test-assets/zephyr_test_cases.json`
- `reports/api-test-assets/property_scenarios.md`
- `reports/api-test-assets/fuzz_scenarios.md`

### 2) Upload generated assets (optional)

Enable credentials via environment variables:

1. TestRail:
   `TESTRAIL_UPLOAD_ENABLED`, `TESTRAIL_BASE_URL`, `TESTRAIL_EMAIL`, `TESTRAIL_API_KEY`, `TESTRAIL_SECTION_ID`, optional `TESTRAIL_SUITE_ID`
1. Zephyr Scale:
   `ZEPHYR_UPLOAD_ENABLED`, `ZEPHYR_SCALE_API_TOKEN`, `ZEPHYR_SCALE_PROJECT_KEY`, optional `ZEPHYR_SCALE_BASE_URL`, optional `ZEPHYR_SCALE_FOLDER_ID`

Then run either:

```bash
python3 scripts/run_api_first_flow.py \
  --project-slug taskstream \
  --notes demos/api-first/taskstream-planning-notes.md \
  --spec api/openapi.yaml \
  --spec-tree api/taskstream \
  --generate-test-assets \
  --upload-test-assets
```

Or direct upload command:

```bash
npm run api:test:upload
```

Upload report:

- `reports/api-test-assets/upload_report.json`

### 3) Recommended verification

1. Confirm generated files exist in `reports/api-test-assets/`.
1. Check `upload_report.json` for per-system success/failure details.
1. Verify imported cases in target TestRail/Zephyr section/folder.

## Code-first workflow

Use this workflow when the API already exists in code and you need to extract the specification from it.

### Step 1: Analyze code changes

Run the code gap analyzer to identify documentation-relevant changes in recent commits:

```bash
npm run gaps:code
```

This executes `python3 -m scripts.gap_detection.cli code`, which scans git history for changes to controllers, routes, handlers, models, and SDK files. It reports which changes need documentation and suggests document types.

For a specific release tag:

```bash
python3 -m scripts.gap_detection.cli code --tag v1.2.0
```

For a custom time window:

```bash
python3 -m scripts.gap_detection.cli code --since 30
```

### Step 2: Generate the OpenAPI specification from code

If your project has an export script, the `openapi-source-sync.yml` workflow handles this automatically:

1. Go to the Actions tab and select "OpenAPI Source Sync."
1. Select `code-first` as the strategy.
1. Provide the expected output path (default: `api/openapi.yaml`).

The workflow looks for one of these export methods:

1. A `package.json` script named `openapi:export`.
1. An executable script at `scripts/export_openapi.sh`.

If neither exists, the workflow fails with instructions on what to add.

### Step 3: Test real endpoints

Unlike the API-first workflow where you test against a Prism mock, the code-first workflow tests against the actual running application. Start your server and run integration tests against it.

### Step 4: Lint the generated specification

```bash
npx @stoplight/spectral-cli lint api/openapi.yaml
```

Fix all Spectral errors. If the generated spec has issues, fix the source code annotations and re-export.

### Step 5: Write reference documentation

Same as API-first: use `templates/api-reference.md`, place in `docs/reference/`, update `mkdocs.yml`.

## Drift detection

Drift occurs when the API specification, SDK code, or documentation get out of sync. The pipeline detects drift automatically and blocks pull requests until it is resolved.

### How drift detection works

The `check_api_sdk_drift.py` script compares files changed in a pull request against three pattern groups defined in `policy_packs/api-first.yml`:

| Pattern group | What it matches | Examples |
| --- | --- | --- |
| `openapi_patterns` | OpenAPI specification files | `openapi*.yaml`, `swagger*.json` |
| `sdk_patterns` | SDK and client library code | `sdk/**`, `clients/**` |
| `reference_doc_patterns` | Reference documentation | `docs/reference/**`, `templates/api-reference.md` |

**Decision logic:**

1. If no OpenAPI or SDK files changed, the check passes.
1. If OpenAPI or SDK files changed AND reference docs also changed, the check passes.
1. If OpenAPI or SDK files changed WITHOUT reference doc updates, the check fails with status `drift`.

### Running drift detection locally

```bash
npm run drift-check
```

Or with full arguments:

```bash
python3 scripts/check_api_sdk_drift.py \
  --base origin/main \
  --head HEAD \
  --policy-pack policy_packs/api-first.yml \
  --json-output reports/api_sdk_drift_report.json \
  --md-output reports/api_sdk_drift_report.md
```

The script produces two report files:

- `reports/api_sdk_drift_report.json` -- structured data for the consolidated report.
- `reports/api_sdk_drift_report.md` -- human-readable summary.

### Drift detection in CI

The `api-sdk-drift-gate.yml` workflow runs automatically on every pull request that touches API, OpenAPI, SDK, or generated files. When drift is detected:

1. The workflow creates a GitHub issue labeled `documentation`, `doc-gap`, and `auto-created`.
1. The issue title includes the pull request number.
1. The issue body contains the full drift report.
1. The workflow fails, blocking the pull request from merging.

**Trigger paths:**

- `api/**`
- `**/openapi*.yaml`, `**/openapi*.yml`, `**/openapi*.json`
- `**/swagger*.yaml`, `**/swagger*.yml`, `**/swagger*.json`
- `sdk/**`, `clients/**`, `generated/**`

### Fixing a drift failure

1. Read the drift report in `reports/api_sdk_drift_report.md` or the auto-created issue.
1. Update the corresponding files in `docs/reference/`.
1. Re-run `npm run drift-check` to verify.
1. Push the documentation changes in the same pull request.

## Definition of Done contract

The `check_docs_contract.py` script tracks when public interface files change without paired documentation changes in the same pull request. Default mode is report-only.

### How the DoD contract works

The script compares changed files against two pattern groups from `policy_packs/api-first.yml`:

| Pattern group | What it matches |
| --- | --- |
| `interface_patterns` | `api/**`, OpenAPI specs, `sdk/**`, `clients/**` |
| `doc_patterns` | `docs/reference/**`, `docs/how-to/**`, API templates |

If interface files changed but no doc files changed, the script reports docs-contract drift. In strict mode, it can also fail the check.

### Running the DoD contract locally

```bash
npm run docs-contract
```

Or with full arguments:

```bash
python3 scripts/check_docs_contract.py \
  --base origin/main \
  --head HEAD \
  --enforcement report-only \
  --policy-pack policy_packs/api-first.yml \
  --json-output reports/pr_docs_contract.json
```

### DoD contract in CI

The `pr-dod-contract.yml` workflow runs on every pull request that touches `api/`, `sdk/`, `clients/`, `src/`, `docs/`, `templates/`, or policy packs. It runs two steps:

1. `validate_pr_dod.py` -- validates the pull request template structure.
1. `check_docs_contract.py` -- reports interface-to-docs drift (`report-only` by default).

By default this is an informational signal. Optional strict mode can be enabled per team.

## Spectral rules

The `.spectral.yml` configuration extends the built-in `spectral:oas` ruleset and adds 18 rules organized into four categories.

### Documentation quality rules

| Rule | Severity | What it checks |
| --- | --- | --- |
| `operation-description` | warn | Every operation has a description |
| `operation-operationId` | error | Every operation has an `operationId` |
| `operation-tags` | warn | Every operation has at least one tag |
| `info-contact` | warn | The `info` object includes contact details |
| `info-description` | error | The `info` object has a description |
| `info-license` | off | License info (disabled) |

### Security rules

| Rule | Severity | What it checks |
| --- | --- | --- |
| `no-eval-in-markdown` | error | No `eval()` in markdown descriptions |
| `no-script-tags-in-markdown` | error | No `<script>` tags in markdown descriptions |

### Best practices rules

| Rule | Severity | What it checks |
| --- | --- | --- |
| `path-params` | error | Path parameters are defined and used |
| `typed-enum` | warn | Enum values have explicit types |
| `operation-success-response` | error | Every operation defines a success response |

### Naming convention rules

| Rule | Severity | What it checks |
| --- | --- | --- |
| `path-keys-no-trailing-slash` | error | Paths do not end with `/` |
| `path-not-include-query` | error | Paths do not contain query strings |

### Custom rules

| Rule | Severity | What it checks |
| --- | --- | --- |
| `parameter-description` | error | Every parameter has a description |
| `schema-properties-example` | warn | Schema properties include example values |

### OpenAPI quality requirements

Every OpenAPI specification in this pipeline must satisfy these requirements:

1. **Every operation has an `operationId`** -- Spectral enforces this at error severity. Use camelCase: `listOrders`, `createUser`, `getOrderById`.
1. **Every operation has a description** -- Spectral warns if missing. Write one to three sentences explaining what the endpoint does.
1. **Every parameter has a description** -- Custom Spectral rule at error severity. Describe the parameter purpose, valid values, and defaults.
1. **Schema properties include examples** -- Custom Spectral rule at warn severity. Provide realistic example values, not placeholders.
1. **Every operation defines a success response** -- Spectral enforces this at error severity. Include at least one 2xx response with a schema.
1. **Error responses are documented** -- Include 400, 401, 403, 404, and 500 responses where applicable.
1. **The info object is complete** -- Must include `description` (error) and `contact` (warn).
1. **Paths follow conventions** -- No trailing slashes, no query strings in paths.

## Policy pack thresholds

The `policy_packs/api-first.yml` file defines quality thresholds that the pipeline enforces through KPI SLA checks:

```yaml
kpi_sla:
  min_quality_score: 82
  max_stale_pct: 12.0
  max_high_priority_gaps: 6
  max_quality_score_drop: 4
```

| Threshold | Value | What it means |
| --- | --- | --- |
| `min_quality_score` | 82 | Documentation quality score must stay at or above 82 |
| `max_stale_pct` | 12.0 | No more than 12% of documents can be stale (90+ days without update) |
| `max_high_priority_gaps` | 6 | No more than 6 high-priority documentation gaps allowed |
| `max_quality_score_drop` | 4 | Quality score cannot drop more than 4 points between reports |

Run the SLA check:

```bash
npm run kpi-sla
```

The policy pack also defines file pattern groups for the docs contract and drift detection (see those sections above).

## Integration with the consolidated report

The consolidated report (`reports/consolidated_report.json`) merges four data sources into one prioritized action list:

1. **Gap analysis** (`doc_gaps_report.json`) -- missing documentation identified by code analysis, community signals, and search analytics.
1. **API/SDK drift** (`api_sdk_drift_report.json`) -- specification or SDK changes without matching doc updates.
1. **KPI wall** (`kpi-wall.json`) -- quality scores, stale documents, metadata completeness.
1. **KPI SLA** (`kpi-sla-report.json`) -- threshold breaches.

### Drift items are Tier 1 priority

The consolidator assigns `priority: "high"` to all drift-detected items. Drift action items include:

- **`api_drift` category** -- OpenAPI spec changed without documentation update. Lists the changed spec files.
- **`sdk_drift` category** -- SDK or client code changed without documentation update. Lists the changed SDK files.

The consolidator also cross-references drift data with gap analysis items. If a gap's `related_files` overlap with drift-changed files, the gap item receives a `drift_related: true` annotation and `drift_overlapping_files` context. This promotes those gaps to higher effective priority when an LLM agent processes the consolidated report.

### Running the full consolidation

```bash
npm run consolidate
```

This runs gap analysis, KPI wall, KPI SLA checks, and then merges all four reports into `reports/consolidated_report.json`.

To consolidate from existing reports without re-running analysis:

```bash
npm run consolidate:reports-only
```

## Enforcement workflows summary

| Workflow | File | Trigger | What it does |
| --- | --- | --- | --- |
| API/SDK drift gate | `api-sdk-drift-gate.yml` | PR touching API/SDK files | Blocks PR if docs are missing, creates issue |
| PR DoD contract | `pr-dod-contract.yml` | PR touching interface or doc files | Reports interface/docs drift (report-only default) |
| Code examples smoke | `code-examples-smoke.yml` | PR or push touching docs/templates | Executes tagged code blocks to verify they work |
| OpenAPI source sync | `openapi-source-sync.yml` | Manual dispatch | Resolves spec from api-first or code-first strategy |
| API-first full flow | `scripts/run_api_first_flow.py` | Local run / weekly automation | Generates contract + stubs + verification + sandbox endpoint sync + test assets + finalize gate (lint/fix loop) |

## Enforcement scripts summary

| Script | npm command | What it does |
| --- | --- | --- |
| `check_api_sdk_drift.py` | `npm run drift-check` | Detects API/SDK drift against reference docs |
| `check_docs_contract.py` | `npm run docs-contract` | Blocks PRs when interface changes lack doc updates |
| `check_code_examples_smoke.py` | `npm run lint:examples-smoke` | Executes fenced code blocks tagged `smoke` |

## First-time local setup

From the repository root:

```bash
npm install
python3 -m pip install -r requirements.txt
```

If `python3` is not available on Windows, use `py -3` instead:

```bash
py -3 -m pip install -r requirements.txt
```

Verify the installation works:

```bash
npm run validate:minimal
```

## Step-by-step workflow for an API change

### API-first path

1. Edit `api/openapi.yaml` with the new or changed endpoint.
1. Lint the spec: `npx @stoplight/spectral-cli lint api/openapi.yaml`.
1. Start sandbox: `bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010 prism`.
1. For public docs sandbox use external mode: `API_SANDBOX_EXTERNAL_BASE_URL=\"https://<your-real-public-mock-url>/v1\" bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010 external`.
1. Test requests against configured `mock_base_url`.
1. Run API-first flow to regenerate and verify: `python3 scripts/run_api_first_flow.py ... --verify-user-path --mock-base-url https://<your-real-public-mock-url>/v1 --generate-test-assets --upload-test-assets --sync-playground-endpoint --ask-commit-confirmation`.
1. Update reference docs in `docs/reference/`.
1. Run `npm run docs-contract` and `npm run drift-check`.
1. Run `npm run lint:examples-smoke`.
1. Open the pull request after all checks pass.

### Code-first path

1. Implement the API change in code.
1. Run `npm run gaps:code` to identify what needs documentation.
1. Export the updated spec (via `openapi:export` script or `scripts/export_openapi.sh`).
1. Lint the spec: `npx @stoplight/spectral-cli lint api/openapi.yaml`.
1. Test real endpoints.
1. Update reference docs in `docs/reference/`.
1. Run `npm run docs-contract` and `npm run drift-check`.
1. Run `npm run lint:examples-smoke`.
1. Open the pull request after all checks pass.

## What to include in docs for API changes

At minimum, update these sections in the reference documentation:

1. **Endpoint path and HTTP method** (for example, `POST /v2/orders`).
1. **Request schema** (required fields, optional fields, data types).
1. **Response schema** (success response, error response structures).
1. **Error codes** (what errors can occur and what they mean).
1. **Authentication requirements** (which auth method, required scopes).
1. **Example request and response** (complete, runnable examples).

Use the `templates/api-reference.md` template for new endpoint documentation.

## Common failure cases and fixes

### Drift gate failed

**What it means:** API or SDK files changed, but reference documentation was not updated.

**How to fix:**

1. Check the drift report in `reports/api_sdk_drift_report.md` for details.
1. Update the corresponding files in `docs/reference/`.
1. Re-run `npm run drift-check`.

### DoD contract drift reported

**What it means:** Public interface files changed (controllers, routes, models, API specs) without paired documentation changes in the same pull request.

**How to fix:**

1. Add or update documentation files in the same pull request.
1. Re-run `npm run docs-contract` to refresh the report.

### Smoke examples failed

**What it means:** A code block tagged with `smoke` in the documentation failed to execute.

**How to fix:**

1. Read the script output to find the exact file and line number.
1. Open the file and fix the broken code example.
1. Re-run `npm run lint:examples-smoke`.

### Spectral lint failed

**What it means:** The OpenAPI specification violates one or more quality rules.

**How to fix:**

1. Run `npx @stoplight/spectral-cli lint api/openapi.yaml` to see all violations.
1. Fix each violation in the spec file.
1. Errors must be fixed. Warnings should be fixed.
1. Re-run the lint command until the spec passes.

### KPI SLA breach

**What it means:** Documentation quality metrics dropped below thresholds in `policy_packs/api-first.yml`.

**How to fix:**

1. Run `npm run kpi-sla` to see which thresholds are breached.
1. Address the specific metric: improve quality score, update stale docs, or close high-priority gaps.
1. Run `npm run consolidate` to regenerate all reports.

## Definition of done for an API-related pull request

A pull request is ready to merge only when all of these are true:

1. DoD contract drift report is reviewed (or strict mode passes, if enabled).
1. Drift gate check passes.
1. Smoke examples check passes.
1. Spectral lint passes on all OpenAPI specification files.
1. Reference docs describe the current API behavior (not the old behavior).
1. Breaking changes include a migration guide or release note.
1. All code examples are complete and runnable.

## Starting from zero

If you have never used these checks before, start with this one command:

```bash
npm run validate:minimal
```

This runs the basic quality checks. Once that passes consistently, add the API checks to your workflow:

```bash
npm run drift-check
npm run docs-contract
npm run lint:examples-smoke
npx @stoplight/spectral-cli lint api/openapi.yaml
```

Run all four before every API-related pull request.

## Related guides

| Guide | What it covers |
| --- | --- |
| `POLICY_PACKS.md` | All policy packs including `api-first.yml` |
| `PLG_PLAYBOOK.md` | PLG documentation with API playground |
| `CUSTOMIZATION_PER_COMPANY.md` | Full per-company configuration |
| `PILOT_VS_FULL_IMPLEMENTATION.md` | Pilot week vs full implementation |
| `OPERATOR_RUNBOOK.md` | Step-by-step delivery execution |

## Next steps

- [Documentation index](../index.md)
