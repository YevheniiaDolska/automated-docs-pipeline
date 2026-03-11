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

<div
  id="api-playground-root"
  data-provider="{{ config.extra.plg.api_playground.provider }}"
  data-source-strategy="{{ config.extra.plg.api_playground.source.strategy }}"
  data-api-first-spec-url="{{ config.extra.plg.api_playground.source.api_first_spec_url }}"
  data-code-first-spec-url="{{ config.extra.plg.api_playground.source.code_first_spec_url }}"
  data-try-it-enabled="{{ config.extra.plg.api_playground.try_it_enabled }}"
  data-try-it-mode="{{ config.extra.plg.api_playground.try_it_mode }}"
  data-sandbox-base-url="{{ config.extra.plg.api_playground.endpoints.sandbox_base_url }}"
  data-production-base-url="{{ config.extra.plg.api_playground.endpoints.production_base_url }}"
></div>

<script>
  window.DOCS_PLG_CONFIG = {
    mode: '{{ config.extra.plg.mode }}',
    approach: '{{ config.extra.plg.approach }}',
    api_playground: {
      provider: '{{ config.extra.plg.api_playground.provider }}',
      try_it_mode: '{{ config.extra.plg.api_playground.try_it_mode }}',
      try_it_enabled: {{ config.extra.plg.api_playground.try_it_enabled }},
      source: {
        strategy: '{{ config.extra.plg.api_playground.source.strategy }}',
        api_first_spec_url: '{{ config.extra.plg.api_playground.source.api_first_spec_url }}',
        code_first_spec_url: '{{ config.extra.plg.api_playground.source.code_first_spec_url }}'
      },
      endpoints: {
        sandbox_base_url: '{{ config.extra.plg.api_playground.endpoints.sandbox_base_url }}',
        production_base_url: '{{ config.extra.plg.api_playground.endpoints.production_base_url }}'
      }
    }
  };
</script>

## Security guidance

1. `sandbox-only`: safest default for regulated or high-risk domains.
1. `real-api`: use only when product policy allows direct user requests.
1. `mixed`: let user choose sandbox vs real API explicitly.
1. Keep write operations protected by auth scopes and rate limits.

## Next steps

- [Documentation index](index.md)
