---
title: "Intent experience: configure for support"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

<!-- markdownlint-disable MD001 MD007 MD024 MD025 MD031 -->

# Intent experience: configure for support

This page is assembled for the `configure` intent and the `support` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent configure --audience support --channel docs
```

## Included modules

### Fix: Webhook trigger not firing (Part 3)

Troubleshoot Webhook nodes that do not receive requests. Common causes include inactive workflows, wrong URL type, and network configuration.

#### Fix: Webhook trigger not firing (Part 3): Still not working?

1. Check the logs for errors: `docker logs` or the process output.
1. Test with a minimal `curl` command from the same network as the service.
1. Verify the HTTP method matches (the Webhook node only responds to the configured method).

#### Fix: Webhook trigger not firing (Part 3): Related

- [Webhook node reference](../reference/nodes/webhook.md)
- [Configure Webhook authentication](../how-to/configure-webhook-trigger.md)

#### Fix: Webhook trigger not firing (Part 3): Next steps

- [Documentation index](index.md)

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
