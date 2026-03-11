---
title: "TaskStream API playground"
description: "Interactive TaskStream OpenAPI playground with Swagger UI or Redoc and try-it-out requests against mock or prod-like sandbox endpoints."
content_type: reference
product: both
tags:
  - Reference
  - Cloud
  - Self-hosted
last_reviewed: "2026-03-09"
---

# TaskStream API playground

This page provides an interactive OpenAPI playground where users can send requests to the sandbox endpoint before production rollout.

## Start a sandbox endpoint

Mock mode:

```bash
bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010
```

Prod-like mode:

```bash
bash scripts/api_prodlike_project.sh up taskstream 4011
```

## Playground embed

<div
  id="api-playground-root"
  data-provider="swagger-ui"
  data-source-strategy="api-first"
  data-api-first-spec-url="/assets/api/openapi.yaml"
  data-try-it-enabled="true"
  data-try-it-mode="sandbox-only"
  data-sandbox-base-url="{{ docs_url }}/sandbox/taskstream/v1"
  data-production-base-url="{{ cloud_url }}/v1"
></div>

## What this validates

1. Request and response schema compatibility.
1. Pagination, filtering, and sorting behavior.
1. Error envelope and request-id propagation.
1. Endpoint availability before backend merge.

## Related pages

- [Run API-first production flow](../how-to/run-api-first-production-flow.md)
- [TaskStream API planning notes](taskstream-planning-notes.md)

## Next steps

- [Documentation index](index.md)
