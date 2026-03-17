---
title: TaskStream API playground
description: Interactive TaskStream OpenAPI playground with Swagger UI or Redoc and
  try-it-out requests against mock or prod-like sandbox endpoints.
content_type: reference
product: both
tags:
- Reference
- Cloud
- Self-hosted
last_reviewed: '2026-03-12'
original_author: Developer
---


# TaskStream API playground

This page provides an interactive OpenAPI playground where users can send requests to the configured sandbox endpoint before production rollout.

## Start a sandbox endpoint

Mock mode:

```bash
bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010
```

No-Docker local mode:

```bash
bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010 prism
```

External hosted mode (recommended for public docs):

```bash
API_SANDBOX_EXTERNAL_BASE_URL="https://sandbox-api.example.com/v1" \
bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010 external
```

Prod-like mode:

```bash
bash scripts/api_prodlike_project.sh up taskstream 4011
```

## Playground embed

<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css">
<div id="api-playground-root"></div>
<script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
<script>
document.addEventListener("DOMContentLoaded", function () {
  var el = document.getElementById("api-playground-root");
  if (!el || el.dataset.swaggerLoaded) return;
  el.dataset.swaggerLoaded = "1";
  SwaggerUIBundle({
    url: "{{ config.site_url }}assets/api/openapi.bundled.json",
    dom_id: "#api-playground-root",
    deepLinking: true,
    docExpansion: "list",
    defaultModelsExpandDepth: 1,
    supportedSubmitMethods: ["get","put","post","delete","options","head","patch","trace"],
    requestInterceptor: function (req) {
      try {
        var u = new URL(req.url, location.origin);
        var t = new URL("{{ config.extra.plg.api_playground.endpoints.sandbox_base_url }}", location.origin);
        u.protocol = t.protocol;
        u.hostname = t.hostname;
        u.port = t.port;
        req.url = u.toString();
      } catch (e) {}
      return req;
    }
  });
});
if (document.readyState !== "loading") { document.dispatchEvent(new Event("DOMContentLoaded")); }
</script>

For multi-version API docs, publish one spec per version and add separate playground blocks or tabs:

- `/assets/api/v1/openapi.yaml`
- `/assets/api/v2/openapi.yaml`

## Multi-language request examples

=== "cURL"

    ```bash
    curl -sS "{{ config.extra.plg.api_playground.endpoints.sandbox_base_url }}/healthz"
    ```

=== "JavaScript"

    ```javascript
    const res = await fetch("{{ config.extra.plg.api_playground.endpoints.sandbox_base_url }}/healthz");
    console.log(await res.json());
    ```

=== "Python"

    ```python
    import requests

    res = requests.get("{{ config.extra.plg.api_playground.endpoints.sandbox_base_url }}/healthz", timeout=10)
    print(res.json())
    ```

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
