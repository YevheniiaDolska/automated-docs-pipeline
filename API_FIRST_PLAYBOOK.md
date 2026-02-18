# API-first playbook

Use this when a company ships API changes frequently.

## Goal

Keep API docs, SDK docs, and contracts synchronized with code changes.

## Required gates

1. PR DoD contract: `.github/workflows/pr-dod-contract.yml`
1. API/SDK drift gate: `.github/workflows/api-sdk-drift-gate.yml`
1. Smoke examples: `.github/workflows/code-examples-smoke.yml`

## Basic workflow

1. Update OpenAPI spec.
1. Update SDK/client code.
1. Update reference docs in same PR.
1. Run drift check.

## Local commands

```bash
python3 scripts/check_api_sdk_drift.py --base origin/main --head HEAD --policy-pack policy_packs/api-first.yml
python3 scripts/check_docs_contract.py --base origin/main --head HEAD --policy-pack policy_packs/api-first.yml
```

## Optional code generation

Example with OpenAPI Generator image:

```bash
docker run --rm -v "${PWD}:/local" openapitools/openapi-generator-cli:v7.7.0 generate -i /local/api/openapi.yaml -g typescript-axios -o /local/generated/client
```

## Delivery rule

If API signature changes and reference docs are not updated, PR must fail.
