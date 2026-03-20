---
title: "AsyncAPI docs-ops playbook"
description: "Operational runbook for AsyncAPI contract validation, regression checks, docs generation, and test asset management."
content_type: reference
product: both
tags:
  - AsyncAPI
  - Playbook
  - Docs-Ops
---

# AsyncAPI docs-ops playbook

- Source of truth: `asyncapi.yaml` / `asyncapi.json`.
- Contract lint: `python3 scripts/validate_asyncapi_contract.py api/asyncapi.yaml`
- Regression: `python3 scripts/check_protocol_regression.py --protocol asyncapi --input api/asyncapi.yaml --snapshot api/.asyncapi-regression.json`
- Docs generation: `python3 scripts/generate_protocol_docs.py --protocol asyncapi --source api/asyncapi.yaml --output docs/reference/asyncapi.md`
- Test assets: `python3 scripts/generate_protocol_test_assets.py --protocols asyncapi --source api/asyncapi.yaml`
- Upload (optional): `python3 scripts/upload_api_test_assets.py --cases-json reports/api-test-assets/api_test_cases.json`

## Next steps

- [Documentation index](../index.md)
