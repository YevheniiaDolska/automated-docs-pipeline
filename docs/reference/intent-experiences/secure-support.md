---
title: 'Intent experience: secure for support'
description: Assembled guidance for one intent and audience using reusable knowledge
  modules with verified metadata and channel-ready sections.
content_type: reference
product: both
tags:
- Reference
- AI
last_reviewed: '2026-03-26'
original_author: Developer
---


<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

# Intent experience: secure for support

This page is assembled for the `secure` intent and the `support` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent secure --audience support --channel docs
```

## Included modules

### Troubleshooting: common VeriOps pipeline issues (Part 4)

Fix common VeriOps documentation pipeline issues in under 5 minutes, covering contract failures, quality gates, build errors, and WebSocket problems.

### Fix quality score in 5 minutes

1. Check the gap report for high-priority items:

    ```bash
    python3 -c "
    import json
    r = json.load(open('reports/acme-demo/doc_gaps_report.json'))
    high = [g for g in r.get('gaps', []) if g.get('priority') == 'high']
    print(f'{len(high)} high-priority gaps:')
    for g in high:
        print(f'  [{g[\"priority\"]}] {g[\"title\"]}')"
    ```

1. Address each high-priority gap by creating or updating the relevant document. Common gaps include:

    | Gap category | Typical fix |
    | --- | --- |
    | `authentication` | Add authentication guide with token management |
    | `webhook` | Document webhook setup and payload schemas |
    | `database_schema` | Add data model reference with field descriptions |
    | `error_handling` | Create error code reference with resolution steps |

1. Re-run the pipeline and verify the score:

    ```bash
    python3 -c "
    import json
    print(json.load(open('reports/acme-demo/kpi-wall.json'))['quality_score'])"
    ```

## MkDocs build fails with theme error

**You see:** `mkdocs build` exits with `Theme 'material' not found` or `Module 'mkdocs_macros' not found`.

**Root cause:** The required Python packages are not installed in the current environment.

### Troubleshooting: common VeriOps pipeline issues (Part 5)

Fix common VeriOps documentation pipeline issues in under 5 minutes, covering contract failures, quality gates, build errors, and WebSocket problems.

### Fix MkDocs theme in 1 minute

```bash
pip install mkdocs-material mkdocs-macros-plugin pymdown-extensions
```

Verify the build succeeds:

```bash
cd demo-showcase/acme && mkdocs build --strict
```

Expected output: `INFO - Documentation built in X.XX seconds`

## WebSocket tester shows connection error

**You see:** The interactive WebSocket tester on the [WebSocket event playground](../reference/websocket-events.md) displays "Connection error."

**Root cause:** The browser blocks insecure WebSocket connections (`ws://`) from HTTPS pages, or the endpoint is unreachable.

### Fix WebSocket connection in 1 minute

- Verify the endpoint uses `wss://` (not `ws://`). The correct endpoint is `wss://api.acme.example/realtime`.
- Confirm the endpoint is accessible from your network. Try from the command line:

    ```bash
    curl -s -o /dev/null -w "%{http_code}" https://api.acme.example/realtime
    ```

- Check browser developer tools (Console tab) for specific error messages.
- If you use a corporate proxy, configure WebSocket passthrough or use the [AsyncAPI event docs](../reference/asyncapi-events.md) with direct AMQP instead.

### Configure HMAC authentication for inbound webhooks

Covers secure webhook authentication setup for docs, assistant responses, in-product hints, and automation workflows with one reusable module.

Use HMAC validation to reject spoofed webhook requests before your workflow executes. Set the shared secret in {{ env_vars.webhook_url }} settings, then verify the `X-Signature` header with SHA-256. Reject requests older than 300 seconds, and return HTTP 401 for invalid signatures.

```bash
curl -X POST "http://localhost:{{ default_webhook_port }}/webhook/order-events" \\
  -H "Content-Type: application/json" \\
  -H "X-Signature: sha256=YOUR_CALCULATED_SIGNATURE" \\
  -d '{"order_id":"ord_9482","event":"order_paid","amount":129.99}'
```

Keep replay protection enabled, rotate the secret every 90 days, and monitor 401 spikes for abuse detection.

## Next steps

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`
