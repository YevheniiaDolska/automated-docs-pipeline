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

## Step 3: Start sandbox for live testing

For contract-mock mode:

```bash
bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010
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

## Step 5: Stop sandbox when needed

```bash
bash scripts/api_sandbox_project.sh down taskstream ./api/openapi.yaml 4010
bash scripts/api_prodlike_project.sh down taskstream 4011
```

## Next steps

- [TaskStream API playground](../reference/taskstream-api-playground.md)
- [TaskStream API planning notes](../reference/taskstream-planning-notes.md)
