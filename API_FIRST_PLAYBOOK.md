# API-first playbook

This playbook explains how to manage documentation for API-first products. API-first means the API contract (OpenAPI specification) is the source of truth, and all documentation, SDKs, and client libraries must stay synchronized with it.

## What API-first means

In an API-first workflow:

1. The OpenAPI specification file defines what the API does.
1. SDK and client library code is generated or written to match the spec.
1. Reference documentation describes the same endpoints, schemas, and behaviors.
1. If any of these three (spec, SDK, docs) get out of sync, that is called "drift."

This playbook prevents drift by automating checks that catch it before code merges.

## Why drift is a problem

Without automated drift detection, teams frequently ship:

1. **Updated API, outdated docs**: New endpoints exist but docs still describe the old ones.
1. **Updated SDK, missing migration notes**: Breaking changes in the SDK with no upgrade guide.
1. **Broken code examples**: Examples in docs reference old field names or removed endpoints.

Each of these causes support tickets, developer frustration, and lost trust.

## What the pipeline provides for API-first teams

### Enforcement workflows

These GitHub Actions workflows run automatically on pull requests:

| Workflow | File | What it checks |
| --- | --- | --- |
| PR DoD contract | `.github/workflows/pr-dod-contract.yml` | If interface files changed, docs must also change |
| API/SDK drift gate | `.github/workflows/api-sdk-drift-gate.yml` | If OpenAPI or SDK changed, reference docs must update |
| Code examples smoke | `.github/workflows/code-examples-smoke.yml` | Fenced code blocks tagged `smoke` must execute without errors |
| OpenAPI source sync | `.github/workflows/openapi-source-sync.yml` | Resolves API spec from api-first or code-first strategy |
| API scaffold generation | `.github/workflows/api-first-scaffold.yml` | Generates server stubs and client SDKs from OpenAPI spec |

### Enforcement scripts

These scripts run locally and in CI:

| Script | What it does |
| --- | --- |
| `scripts/check_docs_contract.py` | Checks if interface file changes have matching docs changes |
| `scripts/check_api_sdk_drift.py` | Checks if API/SDK changes have matching reference doc updates |
| `scripts/check_code_examples_smoke.py` | Executes tagged code blocks in 8 languages |

### Policy pack

The `api-first.yml` policy pack sets quality thresholds for API-heavy products:

```yaml
# policy_packs/api-first.yml
min_quality_score: 82      # Strict quality
max_stale_percentage: 12   # Low stale tolerance
max_high_priority_gaps: 6  # Few gaps allowed
max_quality_score_drop: 4  # Tight quality regression limit
```

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

## Core commands

### Check the interface-to-docs contract

This command checks whether code changes that affect public interfaces also include documentation updates:

```bash
python3 scripts/check_docs_contract.py \
  --base origin/main \
  --head HEAD \
  --policy-pack policy_packs/api-first.yml
```

**What happens:**

1. The script compares files changed between `origin/main` and `HEAD`.
1. If any changed file matches `interface_patterns` in the policy pack (for example, `src/controllers/**`, `src/routes/**`), the script checks whether any file matching `docs_patterns` also changed.
1. If interface files changed but no docs files changed, the command fails.

**How to fix a failure:** Add documentation updates to the same pull request.

### Check API/SDK drift

This command checks whether API specification or SDK changes have matching documentation updates:

```bash
python3 scripts/check_api_sdk_drift.py \
  --base origin/main \
  --head HEAD \
  --policy-pack policy_packs/api-first.yml \
  --json-output reports/api_sdk_drift_report.json \
  --md-output reports/api_sdk_drift_report.md
```

**What happens:**

1. The script looks for changes in files matching `drift_patterns` (for example, `openapi*.yaml`, `sdk/**`).
1. If those files changed but reference docs did not update, the command fails.
1. The report files explain exactly which documentation is missing.

**How to fix a failure:** Update the corresponding files in `docs/reference/`.

### Check code examples

This command executes fenced code blocks in documentation to verify they work:

```bash
python3 scripts/check_code_examples_smoke.py --paths docs templates
```

**What happens:**

1. The script finds all fenced code blocks tagged with `smoke`.
1. It executes each block in the appropriate language runtime.
1. If any block fails (syntax error, runtime error), the command fails.

**Supported languages:** Python, Bash, JavaScript, TypeScript, Go, curl, JSON, YAML.

**How to fix a failure:** Open the file and line number shown in the output, fix the broken code example.

## Step-by-step workflow for an API change

When you change the API, follow this exact sequence:

1. **Update the OpenAPI specification file** with the new or changed endpoint.
1. **Update SDK or client code** if the change affects them.
1. **Update reference docs** in `docs/reference/` to describe the change.
1. **Add migration notes** if the change is breaking (removed fields, changed behavior).
1. **Run the DoD contract check** to verify docs are included.
1. **Run the drift check** to verify reference docs match the spec.
1. **Run the smoke examples check** to verify code examples still work.
1. **Open the pull request** only after all three checks pass locally.

```bash
# Run all three checks in sequence
python3 scripts/check_docs_contract.py --base origin/main --head HEAD --policy-pack policy_packs/api-first.yml
python3 scripts/check_api_sdk_drift.py --base origin/main --head HEAD --policy-pack policy_packs/api-first.yml --json-output reports/api_sdk_drift_report.json --md-output reports/api_sdk_drift_report.md
python3 scripts/check_code_examples_smoke.py --paths docs templates
```

## What to include in docs for API changes

At minimum, update these sections in the reference documentation:

1. **Endpoint path and HTTP method** (for example, `POST /v2/orders`).
1. **Request schema** (required fields, optional fields, data types).
1. **Response schema** (success response, error response structures).
1. **Error codes** (what errors can occur and what they mean).
1. **Authentication requirements** (which auth method, required scopes).
1. **Example request and response** (complete, runnable examples).

Use the `templates/api-reference.md` template for new endpoint documentation.

## Optional: generate code from OpenAPI

If your team uses OpenAPI Generator to create client SDKs:

```bash
docker run --rm -v "${PWD}:/local" openapitools/openapi-generator-cli:v7.7.0 generate \
  -i /local/api/openapi.yaml \
  -g typescript-axios \
  -o /local/generated/client
```

This generates a TypeScript client from the OpenAPI spec. Use the generated code as a starting point, then add business logic.

The pipeline also provides a built-in scaffold workflow:

1. Go to GitHub Actions and run `.github/workflows/api-first-scaffold.yml` manually.
1. Provide `spec_path` (path to your OpenAPI file).
1. Provide `server_generator` (for example, `spring`, `express`).
1. Provide `client_generator` (for example, `typescript-axios`, `python`).
1. The workflow generates server stubs and client SDK artifacts.

## Optional: API playground

For interactive API documentation where users can try endpoints in the browser, see the API playground section in `PLG_PLAYBOOK.md`. The playground uses Swagger UI or Redoc and routes test requests to a sandbox environment.

Start a mock sandbox from your OpenAPI spec:

```bash
npm run api:sandbox:mock
```

Stop the mock sandbox:

```bash
npm run api:sandbox:stop
```

## Common failure cases and fixes

### Drift gate failed

**What it means:** API or SDK files changed, but reference documentation was not updated.

**How to fix:**

1. Check the drift report in `reports/api_sdk_drift_report.md` for details.
1. Update the corresponding files in `docs/reference/`.
1. Re-run the drift check.

### DoD contract failed

**What it means:** Public interface files changed (controllers, routes, models) without any documentation changes in the same pull request.

**How to fix:**

1. Add documentation files to the same pull request.
1. Re-run the contract check.

### Smoke examples failed

**What it means:** A code block tagged with `smoke` in the documentation failed to execute.

**How to fix:**

1. Read the script output to find the exact file and line number.
1. Open the file and fix the broken code example.
1. Re-run the smoke check.

## Definition of done for an API-first pull request

A pull request is ready to merge only when all of these are true:

1. DoD contract check passes.
1. Drift gate check passes.
1. Smoke examples check passes.
1. Reference docs describe the current API behavior (not the old behavior).
1. Breaking changes include a migration guide or release note.
1. All code examples are complete and runnable.

## Starting from zero

If you have never used these checks before, start with this one command:

```bash
npm run validate:minimal
```

This runs the basic quality checks. Once that passes consistently, add the API-first checks (contract, drift, smoke) to your workflow before every API-related pull request.

## Related guides

| Guide | What it covers |
| --- | --- |
| `POLICY_PACKS.md` | All policy packs including `api-first.yml` |
| `PLG_PLAYBOOK.md` | PLG documentation with API playground |
| `CUSTOMIZATION_PER_COMPANY.md` | Full per-company configuration |
| `PILOT_VS_FULL_IMPLEMENTATION.md` | Pilot week vs full implementation |
| `OPERATOR_RUNBOOK.md` | Step-by-step delivery execution |
