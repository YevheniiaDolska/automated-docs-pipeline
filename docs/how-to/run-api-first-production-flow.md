---
title: "Run API-first production flow"
description: "Generate OpenAPI from planning notes, run full lint and self-verification, publish playground assets, and keep a sandbox ready for client testing."
content_type: how-to
product: both
tags:
  - How-To
  - Cloud
  - Self-hosted
last_reviewed: "2026-03-09"
---

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
  --mock-base-url http://localhost:4010/v1 \
  --auto-remediate \
  --max-attempts 3
```

The runner performs:

1. OpenAPI generation from notes.
1. Contract validation.
1. Spectral, Redocly, and Swagger CLI lint checks.
1. FastAPI stub generation.
1. Self-verification of operation coverage and user-path calls.

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
API_SANDBOX_EXTERNAL_BASE_URL="https://sandbox-api.example.com/v1" \
bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010 external
```

In external mode, run API-first verification against the same public URL:

```bash
python3 scripts/run_api_first_flow.py \
  --project-slug taskstream \
  --notes demos/api-first/taskstream-planning-notes.md \
  --spec api/openapi.yaml \
  --spec-tree api/taskstream \
  --verify-user-path \
  --mock-base-url "https://sandbox-api.example.com/v1"
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
    curl -sS http://localhost:4010/v1/healthz
    ```

=== "JavaScript"

    ```javascript
    const res = await fetch("http://localhost:4010/v1/healthz");
    console.log(await res.json());
    ```

=== "Python"

    ```python
    import requests

    res = requests.get("http://localhost:4010/v1/healthz", timeout=10)
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
