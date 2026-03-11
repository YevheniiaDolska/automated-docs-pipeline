---
title: "Set up a real-time webhook processing pipeline"
description: "Configure end-to-end webhook ingestion with HMAC verification, async queue processing, and delivery guarantees in under 15 minutes."
content_type: how-to
product: both
tags:
  - Webhook
  - How-To
  - Cloud
  - Self-hosted
last_reviewed: "2026-03-11"
---

{{ product_name }} webhook processing pipeline enables real-time event ingestion with cryptographic signature verification, async queue processing, and automatic retry logic. This guide walks you through setting up a production-ready webhook receiver with HMAC-SHA256 authentication, BullMQ event queuing, and delivery guarantees—supporting up to {{ rate_limit_requests_per_minute }} events per minute.

## Before you start

Make sure you have:

- {{ product_name }} version {{ current_version }} or later
- Node.js 18+ and Python 3.10+
- Access to a Redis instance for queue management
- An API key with webhook management permissions

Run this version check to confirm your environment:

```bash
curl -s http://localhost:{{ default_port }}/api/{{ api_version }}/health | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Version: {data.get(\"version\", \"unknown\")}')
print(f'Status:  {data.get(\"status\", \"unknown\")}')
"
```

## Configure HMAC-SHA256 signature verification

Webhook signatures prevent unauthorized payloads from reaching your processing pipeline. {{ product_name }} signs every outgoing webhook with HMAC-SHA256 using a shared secret stored in the {{ env_vars.encryption_key }} environment variable.

=== "Cloud"

    {{ product_name }} Cloud at {{ cloud_url }} manages signing keys automatically. Navigate to **Settings > Webhooks > Signing secrets** and copy your key. Cloud rotates keys every 90 days and supports two active keys during rotation.

=== "Self-hosted"

    Generate a signing secret and set it as an environment variable:

    ```bash
    export {{ env_vars.encryption_key }}=$(openssl rand -hex 32)
    export {{ env_vars.webhook_url }}="http://localhost:{{ default_port }}/api/{{ api_version }}/webhooks"
    ```

    Store the secret in your configuration at {{ default_data_folder }}/config for persistence across restarts.

### Verify signatures with Python

Use this complete Python implementation to verify incoming webhook signatures with replay protection:

```python
import hmac
import hashlib
import json
import time

def verify_webhook_signature(payload_body, signature_header, secret):
    """Verify HMAC-SHA256 webhook signature with replay protection."""
    if not signature_header:
        return False

    parts = {}
    for pair in signature_header.split(","):
        key, _, value = pair.strip().partition("=")
        parts[key] = value

    timestamp = parts.get("t")
    signature = parts.get("v1")

    if not timestamp or not signature:
        return False

    # Reject events older than 5 minutes (replay protection)
    if abs(time.time() - int(timestamp)) > 300:
        return False

    # Compute expected signature
    signed_payload = f"{timestamp}.{payload_body}"
    expected = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # Timing-safe comparison prevents timing attacks
    return hmac.compare_digest(expected, signature)


# Test verification
test_payload = '{"event": "order.completed", "order_id": "ord_1234", "amount": 2999}'
test_secret = "whsec_test_secret_key_abc123"
test_timestamp = str(int(time.time()))
signed = f"{test_timestamp}.{test_payload}"
test_sig = hmac.new(
    test_secret.encode("utf-8"),
    signed.encode("utf-8"),
    hashlib.sha256
).hexdigest()
header = f"t={test_timestamp},v1={test_sig}"

result = verify_webhook_signature(test_payload, header, test_secret)
print("Signature valid:", result)  # Must print True
```

### Verify signatures with JavaScript

Use this equivalent Node.js implementation for server-side verification:

```javascript
const crypto = require('crypto');

function verifyWebhookSignature(payload, signatureHeader, secret) {
    if (!signatureHeader) return false;

    const parts = {};
    signatureHeader.split(',').forEach(pair => {
        const [key, value] = pair.trim().split('=');
        parts[key] = value;
    });

    const timestamp = parts['t'];
    const signature = parts['v1'];

    if (!timestamp || !signature) return false;

    // Reject events older than 5 minutes
    const age = Math.abs(Date.now() / 1000 - parseInt(timestamp, 10));
    if (age > 300) return false;

    // Compute expected signature
    const signedPayload = `${timestamp}.${payload}`;
    const expected = crypto
        .createHmac('sha256', secret)
        .update(signedPayload)
        .digest('hex');

    // Timing-safe comparison
    return crypto.timingSafeEqual(
        Buffer.from(expected, 'hex'),
        Buffer.from(signature, 'hex')
    );
}

// Test verification
const testPayload = '{"event": "order.completed", "order_id": "ord_1234", "amount": 2999}';
const testSecret = 'whsec_test_secret_key_abc123';
const ts = Math.floor(Date.now() / 1000).toString();
const sig = crypto.createHmac('sha256', testSecret)
    .update(`${ts}.${testPayload}`).digest('hex');
console.log('Signature valid:', verifyWebhookSignature(
    testPayload, `t=${ts},v1=${sig}`, testSecret
)); // Must print true
```

## Set up async event processing with BullMQ

Return HTTP 200 immediately after signature verification, then process events asynchronously through a Redis-backed queue. This approach prevents delivery timeouts and guarantees at-least-once processing.

```mermaid
sequenceDiagram
    participant C as Client
    participant G as API Gateway
    participant V as HMAC Validator
    participant Q as Event Queue
    participant P as Processor
    participant D as Database
    C->>G: POST /webhooks (signed payload)
    G->>V: Validate HMAC-SHA256
    V-->>G: Signature valid
    G->>Q: Enqueue event
    G-->>C: 200 OK (acknowledged)
    Q->>P: Process async
    P->>D: Store result
    P-->>Q: Job completed
```

## Tune webhook configuration parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `webhook_secret` | string | Required | HMAC signing secret (minimum 32 characters) |
| `max_payload_size` | integer | {{ max_payload_size_mb }} MB | Maximum accepted webhook body size |
| `retry_count` | integer | 3 | Number of delivery retry attempts |
| `retry_backoff` | string | `exponential` | Backoff strategy: `linear`, `exponential`, or `fixed` |
| `timeout_seconds` | integer | 30 | Maximum time to wait for consumer acknowledgment |
| `concurrency` | integer | 5 | Number of parallel queue workers per instance |
| `dead_letter_queue` | boolean | `true` | Route failed events to a dead-letter queue after max retries |

!!! info "Payload size limit"
    {{ product_name }} accepts webhook payloads up to {{ max_payload_size_mb }} MB. Payloads exceeding this limit return HTTP 413. For larger data transfers, include a download URL in the payload and fetch the full content asynchronously.

!!! warning "Signature verification required"
    Always verify webhook signatures before processing payloads. Skipping verification exposes your pipeline to forged events, replay attacks, and data injection. The {{ env_vars.encryption_key }} variable must contain the same secret on both sender and receiver.

!!! tip "Replay protection window"
    Include a timestamp in the signed payload and reject events older than five minutes. Adjust the tolerance window if your servers span multiple time zones. Use Network Time Protocol (NTP) synchronization to keep clock drift under one second.

## Handle delivery failures with exponential backoff

{{ product_name }} retries failed webhook deliveries using exponential backoff with jitter:

- **Attempt 1:** 1-second delay
- **Attempt 2:** 5-second delay
- **Attempt 3:** 30-second delay
- **Dead-letter queue:** Events that fail all three attempts route to a dead-letter queue for manual inspection

=== "Cloud"

    {{ product_name }} Cloud handles retry logic automatically. Monitor failed deliveries in the {{ cloud_url }} dashboard under **Webhooks > Delivery log**. Cloud retains failed events for 30 days.

=== "Self-hosted"

    Configure retry behavior in your {{ product_name }} instance:

    ```bash
    export WEBHOOK_RETRY_COUNT=3
    export WEBHOOK_RETRY_BACKOFF=exponential
    export WEBHOOK_DLQ_ENABLED=true
    ```

    Monitor the dead-letter queue with:

    ```bash
    curl http://localhost:{{ default_port }}/api/{{ api_version }}/webhooks/dlq/count
    ```

## Measure pipeline throughput and latency

Production benchmarks on a 4-core instance with 8 GB RAM running {{ product_name }} {{ current_version }}:

- **Ingestion throughput:** 1,200 webhooks per second at P50
- **HMAC verification latency:** 0.8 ms per payload (SHA-256)
- **Queue processing rate:** 850 events per second per worker
- **End-to-end latency:** 12 ms from receipt to database write (P95)
- **Retry processing:** 200 retries per second with exponential backoff
- **Storage retention:** 30 days for event logs, 90 days for audit trails

These numbers scale linearly with additional worker instances. Add workers by increasing the `concurrency` parameter or deploying additional {{ product_name }} nodes behind the load balancer.

## Troubleshoot webhook delivery failures

### Signature mismatch returns HTTP 401

**Problem:** Webhook delivery fails with `HMAC signature mismatch` error.

**Cause:** The payload body was modified in transit—a reverse proxy, load balancer, or middleware re-encoded the JSON body, changing whitespace or field order.

**Solution:** Verify the signature against the raw request body, not a parsed-and-re-serialized version. Configure your framework to preserve the raw body:

```python
# Flask: access raw body before JSON parsing
raw_body = request.get_data(as_text=True)
verify_webhook_signature(raw_body, request.headers.get("X-Signature"), secret)
```

### Replay attack detected returns HTTP 403

**Problem:** Valid webhooks are rejected with `timestamp outside tolerance window`.

**Cause:** Clock skew between the sending server and your receiver exceeds the five-minute tolerance window.

**Solution:** Synchronize both servers with NTP and verify clock accuracy:

```bash
# Check clock offset
ntpdate -q pool.ntp.org
# If offset exceeds 1 second, force sync
sudo ntpdate -s pool.ntp.org
```

If clock synchronization is not possible, increase the tolerance window to 10 minutes (600 seconds) in your verification function.

### Connection timeout returns HTTP 504

**Problem:** Webhook delivery times out because the receiver takes too long to respond.

**Cause:** Synchronous processing blocks the HTTP response. The sender times out after 30 seconds waiting for acknowledgment.

**Solution:** Return HTTP 200 immediately after signature verification, then process the event asynchronously through BullMQ. This decouples ingestion from processing:

```python
@app.route("/webhooks", methods=["POST"])
def receive_webhook():
    raw_body = request.get_data(as_text=True)
    if not verify_webhook_signature(raw_body, request.headers.get("X-Signature"), secret):
        return "Unauthorized", 401
    queue.enqueue("process_webhook", raw_body)  # Async processing
    return "OK", 200  # Respond immediately
```

## Explore the webhook pipeline architecture

The interactive diagram below shows all 13 components across five layers. Click any component to see detailed metrics, technologies, and connections.

<div class="interactive-diagram" markdown>
<iframe src="../../diagrams/demo-webhook-pipeline.html" title="Webhook processing pipeline architecture"></iframe>
</div>

For static environments, refer to the [Mermaid sequence diagram](#set-up-async-event-processing-with-bullmq) above.

For API endpoint details, see the [API reference](../reference/api-reference.md).

## Next steps

- [Documentation index](../index.md)
