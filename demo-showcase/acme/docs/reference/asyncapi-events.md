---
title: "AsyncAPI event docs"
description: "AsyncAPI 2.6.0 event documentation for Acme with channel contracts, delivery semantics, payload schemas, and interactive event tester."
content_type: reference
product: both
tags:
  - Reference
  - API
last_reviewed: "2026-03-19"
---

# AsyncAPI event docs

The Acme event system provides asynchronous, event-driven communication for project lifecycle changes. AsyncAPI 2.6.0 contracts define channel schemas, delivery guarantees, and payload formats for three event channels.

!!! success "Powered by VeriDoc"
    This page is generated and maintained by the VeriDoc documentation pipeline.
    Channel definitions come from the AsyncAPI 2.6.0 contract at `contracts/asyncapi.yaml`.

## Broker and transport

| Setting | Value |
| --- | --- |
| AsyncAPI version | 2.6.0 |
| Protocol | AMQP 0.9.1 (RabbitMQ) |
| Broker | `amqp://events.acme.example:5672` |
| WebSocket bridge | `wss://events.acme.example/ws` |
| Authentication | Bearer token in connection header or SASL PLAIN |
| Delivery guarantee | At-least-once |
| Message retention | 7 days |
| Max payload size | 256 KB |
| Default consumer group | `acme-consumers` |
| Heartbeat interval | 60 seconds |

## Channel catalog

The Acme event system publishes events on three channels. All channels use JSON-encoded payloads with a standard envelope format.

| Channel | Direction | Payload type | Trigger | Description |
| --- | --- | --- | --- | --- |
| `project.updated` | Publish (server to client) | `ProjectUpdatedEvent` | Project status or name changes | Fires on every `PUT /v1/projects/{id}` that modifies the resource |
| `project.created` | Publish (server to client) | `ProjectCreatedEvent` | New project created | Fires on every `POST /v1/projects` |
| `task.completed` | Publish (server to client) | `TaskCompletedEvent` | Task status changes to `done` | Fires when a task reaches terminal status |

## Event envelope format

Every event uses a standard envelope that wraps the domain-specific payload:

```json
{
  "event_id": "evt_01abc789",
  "event_type": "project.updated",
  "occurred_at": "2026-03-19T14:30:00Z",
  "producer": "acme-core-service",
  "trace_id": "tr_abc123def456",
  "schema_version": "1.0.0",
  "data": {}
}
```

### Envelope fields

| Field | Type | Description |
| --- | --- | --- |
| `event_id` | string | Unique event identifier for idempotency (format: `evt_*`) |
| `event_type` | string | Channel name matching the AsyncAPI contract |
| `occurred_at` | string (ISO 8601) | Timestamp when the event occurred |
| `producer` | string | Service that emitted the event |
| `trace_id` | string | Distributed tracing ID for correlation |
| `schema_version` | string | Payload schema version (semver) |
| `data` | object | Domain-specific payload (see below) |

## Channel: project.updated

Fires when a project status or name changes.

**Payload schema:**

```json
{
  "event_id": "evt_01abc789",
  "event_type": "project.updated",
  "occurred_at": "2026-03-19T14:30:00Z",
  "producer": "acme-core-service",
  "trace_id": "tr_abc123def456",
  "schema_version": "1.0.0",
  "data": {
    "project_id": "prj_abc123",
    "status": "active",
    "previous_status": "draft",
    "updated_by": "usr_456",
    "updated_fields": ["status"]
  }
}
```

**Payload fields (`data`):**

| Field | Type | Description |
| --- | --- | --- |
| `project_id` | string | Project ID (format: `prj_*`) |
| `status` | string | New status: `draft`, `active`, `archived` |
| `previous_status` | string | Status before the change |
| `updated_by` | string | User ID who made the change |
| `updated_fields` | array of strings | List of fields that changed |

## Channel: project.created

Fires when a new project is created.

**Payload schema:**

```json
{
  "event_id": "evt_02ABCD456",
  "event_type": "project.created",
  "occurred_at": "2026-03-19T15:00:00Z",
  "producer": "acme-core-service",
  "trace_id": "tr_def456ghi789",
  "schema_version": "1.0.0",
  "data": {
    "project_id": "prj_def456",
    "name": "Mobile App Launch",
    "status": "active",
    "created_by": "usr_789"
  }
}
```

## Channel: task.completed

Fires when a task status changes to `done`.

**Payload schema:**

```json
{
  "event_id": "evt_03cde789",
  "event_type": "task.completed",
  "occurred_at": "2026-03-19T16:00:00Z",
  "producer": "acme-task-service",
  "trace_id": "tr_ghi789jkl012",
  "schema_version": "1.0.0",
  "data": {
    "task_id": "tsk_abc123",
    "project_id": "prj_abc123",
    "title": "Design homepage mockup",
    "completed_by": "usr_456",
    "duration_seconds": 7200
  }
}
```

## Delivery semantics

| Property | Value | Notes |
| --- | --- | --- |
| Guarantee | At-least-once | Events may be delivered more than once |
| Ordering key | `data.project_id` | Events for the same project arrive in order |
| Deduplication | Use `event_id` | Store processed event IDs for idempotency checks |
| Retry policy | 3 retries with exponential backoff | Initial delay 5 seconds, max delay 60 seconds |
| Dead-letter queue | `{channel}.dlq` | Failed events route here after 3 retries |
| Consumer acknowledgment | Manual ACK required | Unacknowledged messages redeliver after 300 seconds |
| Message TTL | 7 days | Messages expire from the queue after 7 days |

## Consumer code examples

### JavaScript (WebSocket bridge)

```javascript
// Subscribe to project update events via WebSocket bridge
// Requires: valid bearer token and active WebSocket connection
const ws = new WebSocket('wss://events.acme.example/ws', [], {
  headers: { 'Authorization': 'Bearer YOUR_API_KEY' }
});

const processedEvents = new Set();

ws.addEventListener('open', () => {
  ws.send(JSON.stringify({
    action: 'subscribe',
    channels: ['project.updated', 'project.created']
  }));
  console.log('Subscribed to project event channels');
});

ws.addEventListener('message', (event) => {
  const payload = JSON.parse(event.data);

  // Idempotency check: skip duplicate events
  if (processedEvents.has(payload.event_id)) {
    console.log('Skipping duplicate event:', payload.event_id);
    return;
  }
  processedEvents.add(payload.event_id);

  console.log('Event received:', payload.event_type, payload.data.project_id);
  // Process the event here
});
```

<!-- requires: api-key -->

### Python (AMQP direct)

```python
import json
import pika

# Connect to the AMQP broker
# Requires: pika library (pip install pika) and valid credentials
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='events.acme.example',
        port=5672,
        credentials=pika.PlainCredentials('YOUR_USERNAME', 'YOUR_PASSWORD')
    )
)
channel = connection.channel()
channel.queue_declare(queue='my-consumer', durable=True)
channel.queue_bind(queue='my-consumer', exchange='acme.events', routing_key='project.updated')

processed_ids = set()

def on_message(ch, method, properties, body):
    event = json.loads(body)
    if event['event_id'] in processed_ids:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    processed_ids.add(event['event_id'])
    print(f"Project {event['data']['project_id']} status: {event['data']['status']}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='my-consumer', on_message_callback=on_message)
channel.start_consuming()
```

<!-- requires: pika, amqp-credentials -->

## Interactive event tester

Enter a test event payload and send it to the sandbox WebSocket bridge.

!!! info "Sandbox mode"
    Events route to a public WebSocket echo sandbox.
    The endpoint field below auto-fills with the sandbox URL.
    No API key is required for sandbox requests.

<div style="border:1px solid #dbe2ea;border-radius:10px;padding:16px;background:#f8f9fa">
<label><strong>WebSocket endpoint:</strong></label>
<input id="async-ep" value="wss://events.acme.example/ws" style="width:100%;padding:6px;margin:4px 0 8px;border:1px solid #ccc;border-radius:4px;font-family:monospace;">
<label><strong>Event payload (JSON):</strong></label>
<!-- vale Google.Quotes = NO -->
<textarea id="async-payload" rows="8" style="width:100%;font-family:monospace;padding:8px;border:1px solid #ccc;border-radius:4px;">{
  "event_id": "evt_test_01",
  "event_type": "project.updated",
  "occurred_at": "2026-03-19T14:30:00Z",
  "producer": "test-client",
  "data": {
    "project_id": "prj_abc123",
    "status": "active",
    "previous_status": "draft"
  }
}</textarea>
<!-- vale Google.Quotes = YES -->
<button id="async-send" style="margin:8px 0;padding:8px 24px;background:#1a73e8;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px;">Send event</button>
<pre id="async-out" style="max-height:280px;overflow:auto;border:1px solid #dbe2ea;padding:12px;border-radius:8px;background:#fff;margin-top:8px;"></pre>
</div>

<script>
(() => {
  var sandbox = (window.ACME_SANDBOX && window.ACME_SANDBOX.asyncapi_ws_url) || '';
  var fallback = (window.ACME_SANDBOX && window.ACME_SANDBOX.asyncapi_ws_fallback_urls) || [];
  var epInput = document.getElementById('async-ep');
  if (sandbox && epInput) { epInput.value = sandbox; }
  var btn = document.getElementById('async-send');
  if (!btn) return;

  function candidateEndpoints(primary, extras) {
    var seen = {};
    var out = [];
    [primary].concat(Array.isArray(extras) ? extras : []).forEach(function (url) {
      var v = String(url || '').trim();
      if (!v || seen[v]) return;
      seen[v] = true;
      out.push(v);
    });
    return out;
  }

  btn.onclick = function () {
    var out = document.getElementById('async-out');
    var primary = document.getElementById('async-ep').value;
    var payload = document.getElementById('async-payload').value;
    var candidates = candidateEndpoints(primary, fallback);
    var idx = 0;
    out.textContent = 'Connecting to ' + (candidates[0] || 'N/A') + '...';

    function tryNext(lastError) {
      if (idx >= candidates.length) {
        out.textContent = 'Connection failed for all sandbox endpoints.'
          - '\nTried: ' + candidates.join(', ')
          - (lastError ? '\nLast error: ' + lastError : '');
        return;
      }
      var endpoint = candidates[idx++];
      out.textContent = 'Connecting to ' + endpoint + '...';
      try {
        var settled = false;
        var ws = new WebSocket(endpoint);
        var timeout = setTimeout(function () {
          if (settled) return;
          settled = true;
          try { ws.close(); } catch (e) {}
          tryNext('timeout');
        }, 6000);
        ws.onopen = function () {
          if (settled) return;
          ws.send(payload);
          out.textContent = 'Connected to ' + endpoint + '. Event sent. Waiting for acknowledgement...';
        };
        ws.onmessage = function (e) {
          if (settled) return;
          settled = true;
          clearTimeout(timeout);
          out.textContent = 'Endpoint: ' + endpoint + '\nResponse: ' + e.data;
          ws.close();
        };
        ws.onerror = function () {
          if (settled) return;
          settled = true;
          clearTimeout(timeout);
          tryNext('handshake failed');
        };
        ws.onclose = function () {
          if (settled) return;
          settled = true;
          clearTimeout(timeout);
          tryNext('closed before response');
        };
      } catch (e) {
        tryNext(String(e));
      }
    }

    tryNext('');
  };
})();
</script>

## Error handling

| Error | Cause | Resolution |
| --- | --- | --- |
| `CONNECTION_REFUSED` | Broker unreachable | Verify `events.acme.example:5672` is accessible from your network |
| `AUTH_FAILED` | Invalid credentials | Check bearer token or SASL credentials |
| `CHANNEL_NOT_FOUND` | Invalid channel name | Use exact channel names from the catalog above |
| `PAYLOAD_TOO_LARGE` | Message exceeds 256 KB | Reduce payload size or split into multiple events |
| `CONSUMER_TIMEOUT` | No ACK within 300 seconds | Acknowledge messages faster or increase prefetch count |

## Next steps

- [WebSocket event playground](websocket-events.md) for bidirectional real-time messaging
- [REST API reference](rest-api.md) for synchronous CRUD operations
- [Tutorial: launch your first integration](../guides/tutorial.md) to subscribe to events end-to-end
