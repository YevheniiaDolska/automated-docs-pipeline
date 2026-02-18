# API-First Playbook

## Purpose

Use this workflow when a company follows API-first delivery.
The pipeline can generate server stubs and SDK clients directly from OpenAPI specs using ready-made tools.

## Tooling

- OpenAPI Generator (`openapitools/openapi-generator-cli`)
- Optional alternatives: NSwag, Swagger Codegen, Speakeasy, Stainless

## GitHub Actions Workflow

Run `.github/workflows/api-first-scaffold.yml` manually and provide:

1. `spec_path` (for example `api/openapi.yaml`)
1. `server_generator` (for example `typescript-express-server`)
1. `client_generator` (for example `typescript-axios`)

Output artifacts:

- `generated/server`
- `generated/client`

## Local Command Equivalent

```bash
docker run --rm -v "${PWD}:/local" openapitools/openapi-generator-cli:v7.7.0 generate \
  -i /local/api/openapi.yaml \
  -g typescript-express-server \
  -o /local/generated/server

docker run --rm -v "${PWD}:/local" openapitools/openapi-generator-cli:v7.7.0 generate \
  -i /local/api/openapi.yaml \
  -g typescript-axios \
  -o /local/generated/client
```

## Recommended Delivery Model

1. Generate stubs from the spec.
1. Implement business logic in service-layer modules.
1. Keep generated code isolated from handcrafted domain logic.
1. Regenerate stubs on spec changes.
1. Use drift gates to enforce docs/reference updates with API changes.

## Quality Guardrails

1. Run `npm run drift-check` after API/spec changes.
1. Update `docs/reference/` and `templates/api-reference.md` when signatures change.
1. Include migration notes in `release-docs-pack.md` for breaking changes.
