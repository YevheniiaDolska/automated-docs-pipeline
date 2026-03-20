---
title: "gRPC docs-ops playbook"
description: "Operational runbook for gRPC proto contract validation, regression checks, docs generation, and test asset management."
content_type: reference
product: both
tags:
  - gRPC
  - Playbook
  - Docs-Ops
---

# gRPC docs-ops playbook

- Source of truth: `.proto` / descriptor set.
- Contract lint: `python3 scripts/validate_proto_contract.py --proto api/proto`
- Regression: `python3 scripts/check_protocol_regression.py --protocol grpc --input api/proto --snapshot api/.grpc-regression.json`
- Docs generation: `python3 scripts/generate_protocol_docs.py --protocol grpc --source api/proto --output docs/reference/grpc-api.md`
- Test assets: `python3 scripts/generate_protocol_test_assets.py --protocols grpc --source api/proto`
- Upload (optional): `python3 scripts/upload_api_test_assets.py --cases-json reports/api-test-assets/api_test_cases.json`

## Next steps

- [Documentation index](../index.md)
