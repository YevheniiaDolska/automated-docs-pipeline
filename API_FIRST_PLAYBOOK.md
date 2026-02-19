# API-first playbook (beginner-friendly)

This guide is for a person who has never managed API-first documentation workflow before.

## What API-first means

API-first means:

1. API contract (OpenAPI) is the source of truth.
1. SDK and docs must match the API contract.
1. If API changes, reference docs must change in the same pull request.

## Why this matters

Without API-first controls, teams often ship:

1. Updated API but outdated docs.
1. Updated SDK but missing migration notes.
1. Broken examples in docs.

This playbook prevents that drift automatically.

## What is already in this repository

Main enforcement workflows:

1. `.github/workflows/pr-dod-contract.yml`
1. `.github/workflows/api-sdk-drift-gate.yml`
1. `.github/workflows/code-examples-smoke.yml`

Main scripts:

1. `scripts/check_docs_contract.py`
1. `scripts/check_api_sdk_drift.py`
1. `scripts/check_code_examples_smoke.py`

Policy pack:

1. `policy_packs/api-first.yml`

## First local setup

From repository root:

```bash
npm install
python3 -m pip install -r requirements.txt
```

If `python3` is unavailable on Windows, use:

```bash
py -3 -m pip install -r requirements.txt
```

## Core commands you need

### Check interface-to-docs DoD contract

```bash
python3 scripts/check_docs_contract.py \
  --base origin/main \
  --head HEAD \
  --policy-pack policy_packs/api-first.yml
```

Meaning:

1. If API/interface files changed and docs did not change, command fails.
1. You must add docs updates in the same PR.

### Check API/SDK drift

```bash
python3 scripts/check_api_sdk_drift.py \
  --base origin/main \
  --head HEAD \
  --policy-pack policy_packs/api-first.yml \
  --json-output reports/api_sdk_drift_report.json \
  --md-output reports/api_sdk_drift_report.md
```

Meaning:

1. If OpenAPI or SDK changed without reference docs updates, command fails.
1. Report file explains exactly what is missing.

### Check runnable docs examples

```bash
python3 scripts/check_code_examples_smoke.py --paths docs templates
```

Meaning:

1. Runs fenced code blocks tagged with `smoke`.
1. Fails if examples are syntactically invalid or broken.

## Beginner workflow for one API change

Use this exact sequence:

1. Update OpenAPI file.
1. Update SDK/client (if needed).
1. Update reference docs in `docs/reference/`.
1. Update migration notes if breaking change exists.
1. Run DoD contract check.
1. Run drift check.
1. Run smoke examples check.
1. Open PR.

## What to update in docs for API changes

At minimum:

1. Endpoint path and method.
1. Request schema.
1. Response schema.
1. Error codes.
1. Authentication notes.
1. Example request and response.

## Optional code generation

If your team uses OpenAPI Generator:

```bash
docker run --rm -v "${PWD}:/local" openapitools/openapi-generator-cli:v7.7.0 generate \
  -i /local/api/openapi.yaml \
  -g typescript-axios \
  -o /local/generated/client
```

Use generated code as a starting point, then add business logic manually.

## Common failure cases and fixes

### Drift gate failed

Reason:

1. API/SDK changed, but reference docs were not updated.

Fix:

1. Update files in `docs/reference/`.
1. Re-run drift check.

### DoD contract failed

Reason:

1. Public interface changed without docs changes.

Fix:

1. Add docs files in same PR.
1. Re-run contract check.

### Smoke examples failed

Reason:

1. One of `smoke` code blocks is broken.

Fix:

1. Open failing file and line from script output.
1. Fix snippet and rerun check.

## Definition of done for API-first PR

PR is done only when:

1. DoD contract passes.
1. Drift gate passes.
1. Smoke examples check passes.
1. Reference docs reflect current API behavior.
1. Breaking changes include migration notes.

## If you are starting from zero

Start with this one command first:

```bash
npm run validate:minimal
```

Then run the API-first checks above before every API-related PR.
