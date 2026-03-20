---
title: "WebSocket docs-ops playbook"
description: "Operational runbook for WebSocket contract validation, regression checks, docs generation, and test asset management."
content_type: reference
product: both
tags:
  - WebSocket
  - Playbook
  - Docs-Ops
---

# WebSocket docs-ops playbook

- Source of truth: channel/event contract (`websocket.yaml|json`).
- Contract lint: `python3 scripts/validate_websocket_contract.py api/websocket.yaml`
- Regression: `python3 scripts/check_protocol_regression.py --protocol websocket --input api/websocket.yaml --snapshot api/.websocket-regression.json`
- Docs generation: `python3 scripts/generate_protocol_docs.py --protocol websocket --source api/websocket.yaml --output docs/reference/websocket-api.md`
- Test assets: `python3 scripts/generate_protocol_test_assets.py --protocols websocket --source api/websocket.yaml`
- Upload (optional): `python3 scripts/upload_api_test_assets.py --cases-json reports/api-test-assets/api_test_cases.json`

## Next steps

- [Documentation index](../index.md)
