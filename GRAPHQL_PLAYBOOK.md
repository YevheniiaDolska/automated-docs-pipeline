---
title: "GraphQL docs-ops playbook"
description: "Operational runbook for GraphQL schema validation, regression checks, docs generation, and test asset management."
content_type: reference
product: both
tags:
  - GraphQL
  - Playbook
  - Docs-Ops
---

# GraphQL docs-ops playbook

- Source of truth: `schema.graphql` / introspection export.
- Contract lint: `python3 scripts/validate_graphql_contract.py <schema>`
- Regression: `python3 scripts/check_protocol_regression.py --protocol graphql --input <schema> --snapshot <path>`
- Docs generation: `python3 scripts/generate_protocol_docs.py --protocol graphql --source <schema> --output docs/reference/graphql-api.md`
- Test assets: `python3 scripts/generate_protocol_test_assets.py --protocols graphql --source <schema>`
- Upload (optional): `python3 scripts/upload_api_test_assets.py --cases-json reports/api-test-assets/api_test_cases.json`

## Next steps

- [Documentation index](../index.md)
