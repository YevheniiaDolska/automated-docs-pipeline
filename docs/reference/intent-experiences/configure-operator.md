---
title: "Intent experience: configure for operator"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

# Intent experience: configure for operator

This page is assembled for the `configure` intent and the `operator` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent configure --audience operator --channel docs
```

## Included modules

### ASYNCAPI API Reference (Part 3)

Auto-generated asyncapi reference from source contract.

<div id="asyncapi-playground" style="border:1px solid #d1d5db; padding:12px; border-radius:8px;">
  <p><strong>WebSocket Endpoint:</strong> <code id="asyncapi-ws-view"></code></p>
  <p><strong>HTTP Publish Endpoint:</strong> <code id="asyncapi-http-view"></code></p>
  <!-- vale Google.Quotes = NO -->
  <textarea id="asyncapi-message" rows="8" style="width:100%; font-family:monospace;">{
  "event": "health",
  "value": "ok"
}</textarea><br/>
  <!-- vale Google.Quotes = YES -->
  <button id="asyncapi-send-ws">Send via WebSocket</button>
  <button id="asyncapi-send-http">Send via HTTP</button>
  <pre id="asyncapi-output" style="margin-top:12px; max-height:320px; overflow:auto;"></pre>
</div>
<script>
(function(){ const wsEndpoint = ""; const httpEndpoint = "";
const wsView = document.getElementById('asyncapi-ws-view');
const httpView = document.getElementById('asyncapi-http-view');
const sendWs = document.getElementById('asyncapi-send-ws');
const sendHttp = document.getElementById('asyncapi-send-http');
const msg = document.getElementById('asyncapi-message');
const out = document.getElementById('asyncapi-output');
if (!wsView || !httpView || !sendWs || !sendHttp || !msg || !out) return;
wsView.textContent = wsEndpoint || 'not configured';
httpView.textContent = httpEndpoint || 'not configured';
sendWs.onclick = function(){
  if (!wsEndpoint) { out.textContent = 'WebSocket endpoint is not configured (runtime.api_protocol_settings.asyncapi.asyncapi_ws_endpoint)'; return; }
  try {
    const socket = new WebSocket(wsEndpoint);
    socket.onopen = function(){ socket.send(msg.value); out.textContent = 'sent over websocket'; socket.close(); };
    socket.onerror = function(e){ out.textContent = String(e); };
    socket.onmessage = function(e){ out.textContent = String(e.data); };
  } catch (error) { out.textContent = String(error); }
};
sendHttp.onclick = async function(){
  if (!httpEndpoint) { out.textContent = 'HTTP publish endpoint is not configured (runtime.api_protocol_settings.asyncapi.asyncapi_http_publish_endpoint)'; return; }
  out.textContent = 'Loading...';
  try {
    const body = JSON.parse(msg.value || '{}');
    const response = await fetch(httpEndpoint, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(body) });
    const text = await response.text();
    out.textContent = text;
  } catch (error) { out.textContent = String(error); }
};
})();
</script>

### Quality evidence and gate results (Part 6)

Complete quality evidence from the VeriDoc pipeline for VeriOps docs, covering KPI metrics, protocol gates, 24 automated checks, and RAG readiness.

### Style checks (automated)

<!-- vale AmericanEnglish.Spelling = NO -->
<!-- vale proselint.Spelling = NO -->

| Rule | Enforced by | Description |
| --- | --- | --- |
| American English | Vale + AmericanEnglish | Use "color" instead of British "colour" and "optimize" instead of "optimise" |

<!-- vale AmericanEnglish.Spelling = YES -->
<!-- vale proselint.Spelling = YES -->
| Active voice | Vale + write-good | "Configure the webhook" not "The webhook should be configured" |
| No weasel words | Vale + write-good | No "simple," "easy," "just," "many," "various" |
| No contractions | Vale + Google style | "do not" not "don't," "cannot" not "can't" |
| Second person | Vale + Google style | "you" not "the user" or "one" |
| Present tense | Vale + Google style | "sends" not "will send" for current features |

### GRAPHQL API Reference (Part 2)

Auto-generated graphql reference from source contract.

## Interactive GraphQL Playground

<div id="graphql-playground" style="border:1px solid #d1d5db; padding:12px; border-radius:8px;">
  <p><strong>Endpoint:</strong> <code id="graphql-endpoint-view"></code></p>
  <textarea id="graphql-query" rows="12" style="width:100%; font-family:monospace;">query HealthCheck {
  __typename
}</textarea>
  <br/>
  <button id="graphql-run">Run Query</button>
  <pre id="graphql-output" style="margin-top:12px; max-height:320px; overflow:auto;"></pre>
</div>
<script>
(function(){ const endpoint = "";
const view = document.getElementById('graphql-endpoint-view');
const run = document.getElementById('graphql-run');
const query = document.getElementById('graphql-query');
const out = document.getElementById('graphql-output');
if (!view || !run || !query || !out) return;
view.textContent = endpoint || 'not configured';
run.onclick = async function(){
  if (!endpoint) { out.textContent = 'Endpoint is not configured in runtime.api_protocol_settings.graphql.graphql_endpoint'; return; }
  out.textContent = 'Loading...';
  try {
    const response = await fetch(endpoint, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({ query: query.value }) });
    const text = await response.text();
    out.textContent = text;
  } catch (error) { out.textContent = String(error); }
};
})();
</script>

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
