---
title: "Intent experience: troubleshoot for support"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

<!-- markdownlint-disable MD001 MD007 MD024 MD025 MD031 -->

# Intent experience: troubleshoot for support

This page is assembled for the `troubleshoot` intent and the `support` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent troubleshoot --audience support --channel docs
```

## Included modules

### Troubleshooting Guide

Solutions for common problems including webhook failures, credential errors, execution timeouts, and memory issues.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

#### Troubleshooting Guide: Troubleshooting

Problem → cause → solution. Start here when something breaks.

### Fix: Webhook trigger not firing

Troubleshoot Webhook nodes that do not receive requests. Common causes include inactive workflows, wrong URL type, and network configuration.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

#### Fix: Webhook trigger not firing: Fix: Webhook trigger not firing

The Webhook node does not respond to incoming HTTP requests. The sender receives a timeout, connection refused, or 404 error.

#### Fix: Webhook trigger not firing: Cause 1: Using Test URL with an inactive editor

**Symptom:** Requests to the Test URL return a timeout or 404 after you close the editor tab.

**Why:** The Test URL (`/webhook-test/<id>`) is only active while the workflow editor is open and the workflow is in Listening mode. Closing the browser tab deactivates it.

**Fix:** Toggle the workflow to **Active** and use the **Production URL** (`/webhook/<id>`) instead. The Production URL remains active as long as the workflow is enabled.

#### Fix: Webhook trigger not firing: Cause 2: Workflow not activated

**Symptom:** Requests to the Production URL return 404 Not Found.

**Why:** The Production URL only works when the workflow toggle is set to **Active** (green). An inactive workflow does not register its webhook endpoints.

**Fix:** Open the workflow in the editor. Toggle the **Active** switch in the top-right corner. Verify the Production URL returns a response.

### Fix: Webhook trigger not firing (Part 2)

Troubleshoot Webhook nodes that do not receive requests. Common causes include inactive workflows, wrong URL type, and network configuration.

#### Fix: Webhook trigger not firing (Part 2): Cause 3: Firewall or reverse proxy blocking requests

**Symptom:** Requests from external services timeout. Local `curl` requests work fine.

**Why:** The service listens on port 5678 by default. If your server firewall or reverse proxy (Nginx, Caddy, Traefik) does not route traffic to this port, external requests never reach it.

**Fix:**

=== "Docker with Nginx"

 Verify your Nginx config routes traffic to the container:

```nginx

 location /webhook/ {
 proxy_pass http://product:5678;
 proxy_set_header Host $host;
 proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
 }

```

=== "Direct install"

 Check that port 5678 is open:

```bash

 sudo ufw allow 5678
 # or
 sudo firewall-cmd --add-port=5678/tcp --permanent

```

#### Fix: Webhook trigger not firing (Part 2): Cause 4: Incorrect WEBHOOK_URL environment variable

**Symptom:** The Webhook node shows a URL that does not match your domain. External services cannot reach it.

**Why:** The service uses the `WEBHOOK_URL` environment variable to generate webhook URLs. If this is set to `http://localhost:5678` (the default), external services cannot resolve `localhost`.

**Fix:** Set `WEBHOOK_URL` to your public-facing URL:

```bash

export WEBHOOK_URL=https://product.yourdomain.com

```

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

### Define idempotent webhook retry handling

Provides retry and idempotency patterns to avoid duplicate processing across documentation, assistant guidance, and runbook automation.

Use idempotency keys to make webhook retries safe. Persist a processed-event key for at least 24 hours, and skip duplicate events with HTTP 200 to stop upstream retries. Use exponential backoff for outbound retries: one second, two seconds, four seconds, eight seconds, and 16 seconds, capped at five attempts.

```javascript

const retryScheduleSeconds = [1, 2, 4, 8, 16];

function shouldProcess(eventId, cache) {
  if (cache.has(eventId)) {
    return false;
  }
  cache.add(eventId);
  return true;
}

```

Alert when retry rate exceeds 5% for 15 minutes. This threshold usually indicates downstream instability.

## Next steps

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`
