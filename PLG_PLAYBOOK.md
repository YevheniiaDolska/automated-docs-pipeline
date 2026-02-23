# PLG documentation playbook

Use this playbook to create product-led-growth documentation that drives
activation, not only technical comprehension.

## Core PLG documentation patterns

1. Persona entry pages (for example, creators, marketers, operations).
1. Value-first use-case pages with setup time and expected savings.
1. Workflow stack pages that combine multiple templates into one outcome.
1. Before and after framing for decision confidence.
1. Fast checklists that lead to first successful run quickly.

## Templates for PLG docs

1. `templates/plg-persona-guide.md`
1. `templates/plg-value-page.md`
1. `templates/use-case.md`
1. `templates/quickstart.md`

## API sandbox as part of PLG

Interactive API docs can reduce onboarding friction.

1. Use Swagger UI or Redoc.
1. Configure policy: `sandbox-only`, `real-api`, or `mixed`.
1. Route requests using `extra.plg.api_playground.endpoints`.

## Unified PLG config

Use this block in `mkdocs.yml`:

```yaml
extra:
  plg:
    mode: mixed
    approach: hybrid
    api_playground:
      enabled: true
      provider: swagger-ui
      try_it_mode: sandbox-only
      try_it_enabled: false
      source:
        strategy: api-first
        api_first_spec_url: /api/openapi.yaml
        code_first_spec_url: /api/openapi-generated.yaml
      endpoints:
        sandbox_base_url: https://sandbox-api.example.com
        production_base_url: https://api.example.com
```

## API-first and code-first

1. API-first: use committed OpenAPI spec.
1. Code-first: generate spec (`openapi:export` script or `scripts/export_openapi.sh`).
1. Resolve source via `.github/workflows/openapi-source-sync.yml`.

## Human role

Automation and AI handle repetitive drafting and checks.
Humans validate facts, policy fit, and business relevance.
