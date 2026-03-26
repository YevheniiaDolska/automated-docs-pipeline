---
title: API playground
description: Interactive API reference with Swagger UI or Redoc and configurable sandbox
  behavior for product-led growth.
content_type: reference
product: both
tags:
- Reference
- API
- Playground
status: active
last_reviewed: '2026-02-23'
original_author: Developer
---

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

## Overview

This page embeds an API sandbox into documentation.

Use it to support product-led growth by giving users interactive API exploration
inside docs.

## Provider options

1. `swagger-ui`: interactive explorer with optional `Try it out` requests.
1. `redoc`: high-readability API reference view.

## Configure this page

Use the unified PLG config in `mkdocs.yml` under `extra.plg.api_playground`.
This works for both API-first and code-first teams.

- `provider`: `swagger-ui` or `redoc`
- `source.strategy`: `api-first` or `code-first`
- `source.api_first_spec_url`: OpenAPI spec URL for API-first
- `source.code_first_spec_url`: generated spec URL for code-first
- `try_it_enabled`: `true` or `false`
- `try_it_mode`: `sandbox-only`, `real-api`, or `mixed`
- `endpoints.sandbox_base_url`: request target for sandbox mode
- `endpoints.production_base_url`: request target for real API mode

## Playground

<div id="swagger-ui-general"></div>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.18.2/swagger-ui.css">
<script src="https://unpkg.com/swagger-ui-dist@5.18.2/swagger-ui-bundle.js"></script>
<script>
(function() {
  var specUrl = "{{ config.site_url }}{{ config.extra.plg.api_playground.source.api_first_spec_url }}";
  var sandboxUrl = "{{ config.extra.plg.api_playground.endpoints.sandbox_base_url }}";
  function boot() {
    if (typeof SwaggerUIBundle === "undefined") { setTimeout(boot, 100); return; }
    SwaggerUIBundle({
      url: specUrl,
      dom_id: "#swagger-ui-general",
      deepLinking: true,
      docExpansion: "list",
      defaultModelsExpandDepth: 1,
      supportedSubmitMethods: [],
      requestInterceptor: function (req) {
        if (req.url === specUrl || req.url.indexOf("openapi") !== -1) return req;
        try {
          var u = new URL(req.url, location.origin);
          var t = new URL(sandboxUrl, location.origin);
          u.protocol = t.protocol; u.hostname = t.hostname; u.port = t.port;
          req.url = u.toString();
        } catch (e) {}
        return req;
      }
    });
  }
  boot();
})();
</script>

## Security guidance

1. `sandbox-only`: safest default for regulated or high-risk domains.
1. `real-api`: use only when product policy allows direct user requests.
1. `mixed`: let user choose sandbox vs real API explicitly.
1. Keep write operations protected by auth scopes and rate limits.

## Next steps

- [Documentation index](index.md)
