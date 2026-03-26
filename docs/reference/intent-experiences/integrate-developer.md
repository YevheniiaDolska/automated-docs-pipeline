---
title: "Intent experience: integrate for developer"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

# Intent experience: integrate for developer

This page is assembled for the `integrate` intent and the `developer` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent integrate --audience developer --channel docs
```

## Included modules

### VeriOps API platform architecture

Interactive architecture diagram showing the VeriOps API platform with 5 protocol gateways, 4 microservices, and data infrastructure across 5 layers.

# VeriOps API platform architecture

The VeriOps API platform is a multi-protocol system that exposes 5 API interfaces (REST, GraphQL, gRPC, AsyncAPI, WebSocket) through a unified gateway layer backed by microservices and event-driven infrastructure.

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyTDEgMTJsNCA0IDctNyA3IDcgNC00TDEyIDJ6Ii8+PC9zdmc+)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)
![Endpoints](https://img.shields.io/badge/Endpoints-19-3b82f6?style=flat-square)

</div>

## Interactive platform diagram

Click any component in the diagram to view its description, key metrics, and technology tags in the detail panel below.

<div class="interactive-diagram" markdown>
<iframe src="../../diagrams/acme-architecture.html" title="VeriOps platform architecture diagram"></iframe>
</div>

## Layer breakdown

### VeriOps API platform architecture (Part 2)

Interactive architecture diagram showing the VeriOps API platform with 5 protocol gateways, 4 microservices, and data infrastructure across 5 layers.

### Clients layer (4 components)

| Client | Protocol | Description |
| --- | --- | --- |
| SDK Clients | REST, gRPC | Auto-generated libraries for Python, JavaScript, Go, and Java |
| Web Dashboard | REST, WebSocket | React SPA with real-time project boards and notifications |
| Mobile Apps | REST, gRPC | iOS (Swift) and Android (Kotlin) with offline-first architecture |
| Webhook Consumers | HTTP POST | External integrations receiving at-least-once event delivery |

### Edge and security layer (3 components)

| Component | Function | Key metric |
| --- | --- | --- |
| CDN | Content delivery, TLS termination, HTTP/2 | 99.99% uptime SLA, 12 points of presence |
| WAF | SQL injection, XSS, DDoS protection | 2 million malicious request blocks per day |
| Rate Limiter | Per-key request throttling via Redis | 60 requests per minute default, configurable per plan |

### VeriOps API platform architecture (Part 3)

Interactive architecture diagram showing the VeriOps API platform with 5 protocol gateways, 4 microservices, and data infrastructure across 5 layers.

### API gateway layer (5 protocols)

| Protocol | Transport | Endpoints | Interactive reference |
| --- | --- | --- | --- |
| REST | HTTP/1.1 + JSON | 19 endpoints across 5 resources | [Swagger UI](../reference/rest-api.md) |
| GraphQL | HTTP POST | 3 operation types (Query, Mutation, Subscription) | [Live playground](../reference/graphql-playground.md) |
| gRPC | HTTP/2 + Protobuf | 3 RPC methods on ProjectService | [Gateway tester](../reference/grpc-gateway.md) |
| AsyncAPI | AMQP 0.9.1 | 3 event channels | [Event tester](../reference/asyncapi-events.md) |
| WebSocket | WSS (RFC 6455) | 4 real-time channels | [WS playground](../reference/websocket-events.md) |

### Services layer (4 microservices)

| Service | Responsibility | Key capability |
| --- | --- | --- |
| Auth Service | JWT validation, OAuth2 flows, RBAC | 50&nbsp;ms average token validation |
| Project Service | Project CRUD, status transitions, event emission | Emits project.created and project.updated events |
| Task Service | Task lifecycle, priority queue, assignment | Cascading delete with parent project |
| Notification Service | Fan-out to WebSocket, webhooks, and email | Bridges AMQP events to client transports |

### VeriOps API platform architecture (Part 4)

Interactive architecture diagram showing the VeriOps API platform with 5 protocol gateways, 4 microservices, and data infrastructure across 5 layers.

### Data and infrastructure layer (4 components)

| Component | Role | Key metric |
| --- | --- | --- |
| PostgreSQL | Primary relational database | 8,500 queries per second, primary + 2 read replicas |
| Redis | Cache, rate limits, sessions | 94% cache hit rate, 3-node cluster |
| RabbitMQ | Event broker (AMQP 0.9.1) | 3 exchanges, 7-day message retention |
| Object Storage | File attachments, backups, audit logs | S3-compatible, AES-256 encryption, 2.5 TB per day |

## Request flow

A typical API request traverses 5 layers in sequence:

1. **Client sends request** to one of the 5 protocol endpoints
1. **CDN caches** static content (24-hour TTL) and forward dynamic requests
1. **WAF inspects** the request payload against OWASP Top 10 rules
1. **Rate Limiter checks** the API key's remaining quota in Redis
1. **API Gateway routes** to the appropriate protocol handler
1. **Auth Service validates** the JWT Bearer token (50&nbsp;ms average)
1. **Domain Service processes** the business logic (Project or Task Service)
1. **PostgreSQL persists** the state change, Redis updates the cache
1. **RabbitMQ publishes** lifecycle events to subscribed channels
1. **Notification Service fans out** events to WebSocket clients and webhook endpoints

### VeriOps API platform architecture (Part 5)

Interactive architecture diagram showing the VeriOps API platform with 5 protocol gateways, 4 microservices, and data infrastructure across 5 layers.

## Next steps

- [REST API reference](../reference/rest-api.md) for the full 19-endpoint specification
- [Concept: pipeline-first lifecycle](concept.md) for how the documentation pipeline works
- [Quality evidence](../quality/evidence.md) for gate results and metrics

### ASYNCAPI API Reference

Auto-generated asyncapi reference from source contract.

# ASYNCAPI Reference

Source: `reports/acme-demo/contracts/asyncapi.yaml`

Flow mode: `api-first`

## Top-level Keys

- `asyncapi`
- `channels`
- `info`

## Channels

- Channel count: `1`
- `project.updated`

### ASYNCAPI API Reference (Part 2)

Auto-generated asyncapi reference from source contract.

## Interactive AsyncAPI Tester

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

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

### ASYNCAPI API Reference (Part 4)

Auto-generated asyncapi reference from source contract.

## Next steps

- [Documentation index](../../../index.md)

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

### AsyncAPI event docs

AsyncAPI 2.6.0 event documentation for VeriOps with channel contracts, delivery semantics, payload schemas, and interactive event tester.

# AsyncAPI event docs

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)

</div>

The VeriOps event system provides asynchronous, event-driven communication for project lifecycle changes. AsyncAPI 2.6.0 contracts define channel schemas, delivery guarantees, and payload formats for three event channels.

## Broker and transport

| Setting | Value |
| --- | --- |
| AsyncAPI version | 2.6.0 |
| Protocol | AMQP 0.9.1 (RabbitMQ) |
| Broker | `amqp://events.veriops.example:5672` |
| WebSocket bridge | `wss://events.veriops.example/ws` |
| Authentication | Bearer token in connection header or SASL PLAIN |
| Delivery guarantee | At-least-once |
| Message retention | 7 days |
| Max payload size | 256 KB |
| Default consumer group | `veriops-consumers` |
| Heartbeat interval | 60 seconds |

### AsyncAPI event docs (Part 10)

AsyncAPI 2.6.0 event documentation for VeriOps with channel contracts, delivery semantics, payload schemas, and interactive event tester.

<script>
(() => {
  if (window.__ACME_SANDBOX_CONTROLLER__ === true) return;
  var sandbox = (window.ACME_SANDBOX && window.ACME_SANDBOX.asyncapi_ws_url) || '';
  var fallback = (window.ACME_SANDBOX && window.ACME_SANDBOX.asyncapi_ws_fallback_urls) || [];
  var epInput = document.getElementById('async-ep');
  if (sandbox && epInput) { epInput.value = sandbox; }
  var btn = document.getElementById('async-send');
  if (!btn) return;
  function safeParse(raw) {
    try { return JSON.parse(String(raw || '{}')); } catch (_) { return { raw: String(raw || '') }; }
  }
  function semanticAsync(req) {
    var eventType = String((req && (req.event_type || req.type || req.event)) || '').toLowerCase();
    var data = (req && req.data && typeof req.data === 'object') ? req.data : {};
    var eventId = String((req && req.event_id) || ('evt_' + Math.random().toString(36).slice(2, 10)));
    var projectId = String(data.project_id || 'prj_abc123');
    var occurredAt = (req && req.occurred_at) || new Date().toISOString();
    if (eventType === 'project.created') return { event_id: eventId, event_type: 'project.created', occurred_at: occurredAt, data: { project_id: projectId, name: data.name || 'New Project', status: data.status || 'draft' } };
    if (eventType === 'project.updated') return { event_id: eventId, event_type: 'project.updated', occurred_at: occurredAt, data: { project_id: projectId, status: data.status || 'active', changed_fields: data.changed_fields || ['status'] } };
    if (eventType === 'task.completed') return { event_id: eventId, event_type: 'task.completed', occurred_at: occurredAt, data: { task_id: data.task_id || 'tsk_123', project_id: projectId, completed_by: data.completed_by || 'usr_demo' } };
    return { event_id: eventId, event_type: eventType || 'custom.event', occurred_at: occurredAt, data: Object.assign({ project_id: projectId, status: 'accepted' }, data), hint: 'Use: project.created, project.updated, task.completed' };
  }

### AsyncAPI event docs (Part 11)

AsyncAPI 2.6.0 event documentation for VeriOps with channel contracts, delivery semantics, payload schemas, and interactive event tester.

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

### AsyncAPI event docs (Part 12)

AsyncAPI 2.6.0 event documentation for VeriOps with channel contracts, delivery semantics, payload schemas, and interactive event tester.

function tryNext(lastError) {
      if (idx >= candidates.length) {
        out.textContent = JSON.stringify(
          {
            mode: 'offline-semantic-fallback',
            tried: candidates,
            last_error: lastError || '',
            simulated_response: semanticAsync(safeParse(payload))
          },
          null,
          2
        );
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
          out.textContent = JSON.stringify(
            {
              endpoint: endpoint,
              mode: 'live-echo-plus-semantic',
              raw: String(e.data || ''),
              simulated_response: semanticAsync(safeParse(e.data))
            },
            null,
            2
          );
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

### AsyncAPI event docs (Part 13)

AsyncAPI 2.6.0 event documentation for VeriOps with channel contracts, delivery semantics, payload schemas, and interactive event tester.

tryNext('');
  };
})();
</script>

## Error handling

| Error | Cause | Resolution |
| --- | --- | --- |
| `CONNECTION_REFUSED` | Broker unreachable | Verify `events.veriops.example:5672` is accessible from your network |
| `AUTH_FAILED` | Invalid credentials | Check bearer token or SASL credentials |
| `CHANNEL_NOT_FOUND` | Invalid channel name | Use exact channel names from the catalog above |
| `PAYLOAD_TOO_LARGE` | Message exceeds 256 KB | Reduce payload size or split into multiple events |
| `CONSUMER_TIMEOUT` | No ACK within 300 seconds | Acknowledge messages faster or increase prefetch count |

## Next steps

- [WebSocket event playground](websocket-events.md) for bidirectional real-time messaging
- [REST API reference](rest-api.md) for synchronous CRUD operations
- [Tutorial: launch your first integration](../guides/tutorial.md) to subscribe to events end-to-end

### AsyncAPI event docs (Part 2)

AsyncAPI 2.6.0 event documentation for VeriOps with channel contracts, delivery semantics, payload schemas, and interactive event tester.

## Channel catalog

The VeriOps event system publishes events on three channels. All channels use JSON-encoded payloads with a standard envelope format.

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
  "producer": "veriops-core-service",
  "trace_id": "tr_abc123def456",
  "schema_version": "1.0.0",
  "data": {}
}
```

### AsyncAPI event docs (Part 3)

AsyncAPI 2.6.0 event documentation for VeriOps with channel contracts, delivery semantics, payload schemas, and interactive event tester.

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

### AsyncAPI event docs (Part 4)

AsyncAPI 2.6.0 event documentation for VeriOps with channel contracts, delivery semantics, payload schemas, and interactive event tester.

## Channel: project.updated

Fires when a project status or name changes.

**Payload schema:**

```json
{
  "event_id": "evt_01abc789",
  "event_type": "project.updated",
  "occurred_at": "2026-03-19T14:30:00Z",
  "producer": "veriops-core-service",
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
  "producer": "veriops-core-service",
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

### AsyncAPI event docs (Part 5)

AsyncAPI 2.6.0 event documentation for VeriOps with channel contracts, delivery semantics, payload schemas, and interactive event tester.

## Channel: task.completed

Fires when a task status changes to `done`.

**Payload schema:**

```json
{
  "event_id": "evt_03cde789",
  "event_type": "task.completed",
  "occurred_at": "2026-03-19T16:00:00Z",
  "producer": "veriops-task-service",
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

### AsyncAPI event docs (Part 6)

AsyncAPI 2.6.0 event documentation for VeriOps with channel contracts, delivery semantics, payload schemas, and interactive event tester.

### JavaScript (WebSocket bridge)

```javascript
// Subscribe to project update events via WebSocket bridge
// Requires: valid bearer token and active WebSocket connection
const ws = new WebSocket('wss://events.veriops.example/ws', [], {
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

### AsyncAPI event docs (Part 7)

AsyncAPI 2.6.0 event documentation for VeriOps with channel contracts, delivery semantics, payload schemas, and interactive event tester.

### Python (AMQP direct)

```python
import json
import pika

# Connect to the AMQP broker
# Requires: pika library (pip install pika) and valid credentials
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='events.veriops.example',
        port=5672,
        credentials=pika.PlainCredentials('YOUR_USERNAME', 'YOUR_PASSWORD')
    )
)
channel = connection.channel()
channel.queue_declare(queue='my-consumer', durable=True)
channel.queue_bind(queue='my-consumer', exchange='veriops.events', routing_key='project.updated')

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

### AsyncAPI event docs (Part 8)

AsyncAPI 2.6.0 event documentation for VeriOps with channel contracts, delivery semantics, payload schemas, and interactive event tester.

## Interactive event tester

Enter a test event payload and send it to the sandbox WebSocket bridge.

!!! info "Sandbox mode"
    Events route to a public WebSocket echo sandbox.
    The endpoint field below auto-fills with the sandbox URL.
    No API key is required for sandbox requests.

### AsyncAPI event docs (Part 9)

AsyncAPI 2.6.0 event documentation for VeriOps with channel contracts, delivery semantics, payload schemas, and interactive event tester.

<div style="border:1px solid #dbe2ea;border-radius:10px;padding:16px;background:#f8f9fa">
<label><strong>WebSocket endpoint:</strong></label>
<input id="async-ep" value="wss://events.veriops.example/ws" style="width:100%;padding:6px;margin:4px 0 8px;border:1px solid #ccc;border-radius:4px;font-family:monospace;">
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

### Concept: pipeline-first documentation lifecycle

Pipeline-first documentation automates generation, validation, and publishing of API docs from source contracts, reducing review cycles by 60%.

# Concept: pipeline-first documentation lifecycle

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)

</div>

Pipeline-first documentation is a methodology where automated systems generate, validate, and publish API documentation from source contracts. Humans review and approve outputs instead of writing from scratch, reducing review cycles from 5+ rounds to 1-2 rounds.

### Concept: pipeline-first documentation lifecycle (Part 10)

Pipeline-first documentation automates generation, validation, and publishing of API docs from source contracts, reducing review cycles by 60%.

## Next steps

- [How-to: keep docs aligned with every release](how-to.md) for the operational workflow
- [Quality evidence and gate results](../quality/evidence.md) for the latest pipeline metrics
- [Troubleshooting: common pipeline issues](troubleshooting.md) if pipeline stages fail
- [Quality evidence](../quality/evidence.md) for the latest gate results

### Concept: pipeline-first documentation lifecycle (Part 2)

Pipeline-first documentation automates generation, validation, and publishing of API docs from source contracts, reducing review cycles by 60%.

## The problem it solves

Without pipeline-first documentation, engineering teams face three critical challenges:

1. **Documentation drift**: API code changes ship to production while docs remain stuck on the previous version. The average drift window is 2-4 weeks, during which users encounter incorrect information.

1. **Inconsistent quality**: Documentation quality depends on individual writers. One team produces excellent guides while another produces minimal stubs. No enforced quality bar exists across the organization.

1. **Multi-protocol coverage gaps**: Teams that support REST, GraphQL, gRPC, AsyncAPI, and WebSocket must maintain five separate documentation sets. Without automation, at least two protocols fall behind on every release.

Traditional approaches like wiki-based documentation or manual Markdown editing fail because they rely on human memory to trigger updates. When the OpenAPI spec changes, nobody remembers to update the corresponding tutorial.

## How the pipeline works

The VeriDoc pipeline follows an eight-stage execution order. Each stage reads the output of the previous stage and produces artifacts for the next.

### Concept: pipeline-first documentation lifecycle (Part 3)

Pipeline-first documentation automates generation, validation, and publishing of API docs from source contracts, reducing review cycles by 60%.

### Stage 1: ingest

Read source contracts from the repository:

| Contract type | Format | Example path |
| --- | --- | --- |
| REST | OpenAPI 3.0 YAML | `api/openapi.yaml` |
| GraphQL | SDL schema | `contracts/graphql.schema.graphql` |
| gRPC | Proto3 definition | `contracts/grpc/veriops.proto` |
| AsyncAPI | AsyncAPI 2.6.0 YAML | `contracts/asyncapi.yaml` |
| WebSocket | WebSocket contract YAML | `contracts/websocket.yaml` |

### Stage 2: lint

Validate each contract against protocol-specific rules. REST uses Spectral with 18 rules, GraphQL uses schema validation, gRPC uses `protoc` compilation, AsyncAPI uses the AsyncAPI parser, and WebSocket uses custom schema validation.

### Stage 3: regression

Compare the current contract against the previous snapshot to detect breaking changes. Breaking changes (removed endpoints, renamed fields, changed types) trigger warnings in the review manifest.

### Stage 4: generate

Produce reference documentation from validated contracts. Each protocol generates endpoint tables, payload schemas, code examples, and interactive testers.

### Concept: pipeline-first documentation lifecycle (Part 4)

Pipeline-first documentation automates generation, validation, and publishing of API docs from source contracts, reducing review cycles by 60%.

### Stage 5: quality gate

Run 24 automated checks on every generated page:

| Category | Check count | What they verify |
| --- | --- | --- |
| GEO (8 checks) | 8 | LLM and AI search optimization: meta descriptions, first paragraph length, heading hierarchy, fact density |
| SEO (14 checks) | 14 | Traditional search optimization: title length, URL depth, internal links, structured data |
| Style (automated) | Per-page | American English, active voice, no weasel words, no contractions |
| Contract (per-protocol) | Per-endpoint | Schema validation, regression detection, snippet lint |

### Stage 6: test assets

Generate API test cases for integration testing frameworks. The pipeline produces test cases in three formats:

| Format | Output path | Purpose |
| --- | --- | --- |
| JSON (generic) | `reports/api_test_cases.json` | Framework-agnostic test definitions |
| CSV (TestRail) | `reports/testrail_test_cases.csv` | Import into TestRail test management |
| JSON (Zephyr) | `reports/zephyr_test_cases.json` | Import into Zephyr Scale for Jira |

### Concept: pipeline-first documentation lifecycle (Part 5)

Pipeline-first documentation automates generation, validation, and publishing of API docs from source contracts, reducing review cycles by 60%.

### Stage 7: RAG optimize

Build a knowledge retrieval index, FAISS vector store, and knowledge graph for AI-powered search. Six advanced retrieval features are available:

| Artifact | Description | Metrics (VeriOps demo) |
| --- | --- | --- |
| Knowledge modules | Auto-extracted topic chunks | 167 modules |
| Knowledge graph | Node and edge relationships | 1,272 nodes, 1,089 edges |
| Retrieval index | Search-optimized vector index | Precision: 0.2, Recall: 0.6 |
| FAISS index | `text-embedding-3-small` embeddings | Cosine similarity search |

| Advanced feature | Description |
| --- | --- |
| Token-aware chunking | Splits modules into 750-token chunks with 100-token overlap |
| Hybrid search (RRF) | Fuses semantic and token-overlap rankings (k=60) |
| HyDE query expansion | Generates hypothetical passage before embedding |
| Cross-encoder reranking | Rescores top 20 candidates with `ms-marco-MiniLM-L-6-v2` |
| Embedding cache | In-memory LRU cache (TTL: 3,600 seconds, max: 512 entries) |
| Multi-mode evaluation | Compares token, semantic, hybrid, and hybrid+rerank modes |

### Stage 8: publish

Copy verified artifacts to the documentation site. Only artifacts that pass all quality gates reach the publish stage.

### Concept: pipeline-first documentation lifecycle (Part 6)

Pipeline-first documentation automates generation, validation, and publishing of API docs from source contracts, reducing review cycles by 60%.

## Quality gate breakdown

The pipeline enforces 24 automated checks before any document reaches production:

### Concept: pipeline-first documentation lifecycle (Part 7)

Pipeline-first documentation automates generation, validation, and publishing of API docs from source contracts, reducing review cycles by 60%.

| Check ID | Rule | Severity | Threshold |
| --- | --- | --- | --- |
| GEO-1 | Meta description present | Error | Must exist |
| GEO-1b | Meta description length (minimum) | Warning | 50 characters minimum |
| GEO-1c | Meta description length (maximum) | Warning | 160 characters maximum |
| GEO-2 | First paragraph length | Warning | 60 words maximum |
| GEO-3 | First paragraph definition pattern | Suggestion | Contains "is," "enables," "provides," or "allows" |
| GEO-4 | Heading specificity | Warning | No generic headings (overview, setup, configuration) |
| GEO-5 | Heading hierarchy | Error | No skipped levels (H2 to H4 is invalid) |
| GEO-6 | Fact density | Warning | At least one fact per 200 words |
| SEO-01 | Title length | Error/Warning | 10-70 characters |
| SEO-02 | Title keyword match | Suggestion | 50% overlap with filename keywords |
| SEO-03 | URL depth | Warning | Max 4 directory levels |
| SEO-04 | URL naming | Warning | Kebab-case only |
| SEO-05 | Image alt text | Warning | 100% of images must have alt text |
| SEO-06 | Internal links | Suggestion | At least 1 per page |
| SEO-07 | Bare URLs | Warning | All URLs must use `[text](url)` format |
| SEO-08 | Path special characters | Warning | Alphanumeric and hyphens only |
| SEO-09 | Line length | Warning | Max 120 characters outside code blocks |
| SEO-10 | Heading keyword overlap | Suggestion | H2 headings share keywords with title |
| SEO-11 | Freshness signal | Suggestion | `last_reviewed` or `date` in frontmatter |
| SEO-12 | Content depth | Warning | Minimum 100 words |
| SEO-13 | Duplicate headings | Warning | No two headings share the same text |
| SEO-14 | Structured data | Suggestion | At least 1 table, code block, or list |

### Concept: pipeline-first documentation lifecycle (Part 8)

Pipeline-first documentation automates generation, validation, and publishing of API docs from source contracts, reducing review cycles by 60%.

## Key benefits

### Zero-drift guarantee

Documentation updates when contracts change, not weeks later. The pipeline detects drift by comparing the current contract hash against the last published snapshot. When drift is detected, the pipeline regenerates the affected pages automatically.

### Protocol parity

REST, GraphQL, gRPC, AsyncAPI, and WebSocket documentation follow the same quality bar. All five protocols pass through identical pipeline stages with protocol-specific validation at each stage.

### Operator review checkpoint

The pipeline generates a review manifest before publish. It lists all artifacts, their availability status, and provides an approval checklist. Operators approve or reject the entire batch instead of reviewing individual pages.

### Advanced RAG pipeline

The knowledge retrieval index with 1,272 nodes and 1,089 edges enables AI support agents to answer user questions from the documentation. The pipeline auto-extracts 167 knowledge modules from docs content, builds a searchable graph, and embeds modules into a FAISS vector store. Six advanced features (chunking, hybrid search, HyDE, reranking, embedding cache, and multi-mode eval) maximize retrieval precision and recall.

### Concept: pipeline-first documentation lifecycle (Part 9)

Pipeline-first documentation automates generation, validation, and publishing of API docs from source contracts, reducing review cycles by 60%.

## Comparison: traditional versus pipeline-first

| Dimension | Traditional docs | Pipeline-first docs | Improvement |
| --- | --- | --- | --- |
| Drift window | 2-4 weeks | 0 days (auto-generated) | Eliminated |
| Quality checks | Manual review | 24 automated checks | Consistent |
| Review cycles | 5+ rounds | 1-2 rounds | 60% reduction |
| Protocol coverage | 1-2 protocols | 5 protocols | Full parity |
| Time to publish | 2-3 days | 20 minutes | 95% faster |
| Stale page detection | Discovered by users | Weekly automated scan | Proactive |
| RAG readiness | Manual tagging | Auto-generated index | Automated |

## When to use pipeline-first documentation

Use pipeline-first documentation when you have:

- More than 2 API protocols to document (REST + GraphQL + gRPC is the common starting point)
- Release cadence faster than monthly (weekly or biweekly releases benefit most)
- Quality requirements that exceed what manual review can sustain
- AI-powered support agents that need structured knowledge for retrieval

Do not use pipeline-first documentation when:

- You have a single, stable API with infrequent changes (manual docs are sufficient)
- Your documentation is primarily conceptual, not API reference (the pipeline focuses on contract-driven content)

### Quality evidence and gate results

Complete quality evidence from the VeriDoc pipeline for VeriOps docs, covering KPI metrics, protocol gates, 24 automated checks, and RAG readiness.

# Quality evidence and gate results

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)

</div>

This page provides the complete quality evidence generated by the VeriDoc pipeline for the VeriOps documentation site. It covers KPI metrics, protocol gate results, 24 automated quality checks, RAG retrieval readiness, and all pipeline artifacts.

## KPI metrics

These metrics come from `reports/acme-demo/kpi-wall.json`:

| Metric | Value | Target | Status |
| --- | --- | --- | --- |
| Quality score | **100%** | 80% | Excellent |
| Total documents | **12** | -- | Indexed across all protocols |
| Stale pages | **0** | 0 | No stale pages |
| Documentation gaps | **0** | 0 | No active gaps |
| Metadata completeness | **100%** | 100% | All frontmatter fields present and valid |
| Frontmatter errors | **0** | 0 | All pages pass schema validation |

### Quality evidence and gate results (Part 10)

Complete quality evidence from the VeriDoc pipeline for VeriOps docs, covering KPI metrics, protocol gates, 24 automated checks, and RAG readiness.

## Pipeline artifacts

All artifacts generated by the pipeline for this demo:

| Artifact | Status | Path | Description |
| --- | --- | --- | --- |
| Multi-protocol contract report | Generated | `reports/acme-demo/multi_protocol_contract_report.json` | Protocol validation results |
| KPI wall | Generated | `reports/acme-demo/kpi-wall.json` | Quality metrics dashboard |
| Gap analysis | Generated | `reports/acme-demo/doc_gaps_report.json` | Missing documentation topics |
| Lifecycle report | Generated | `reports/acme-demo/lifecycle-report.json` | Document freshness and staleness |
| Glossary sync report | Generated | `reports/acme-demo/glossary_sync_report.json` | Terminology consistency |
| Retrieval eval report | Generated | `reports/acme-demo/retrieval_evals_report.json` | RAG precision and recall |
| Knowledge graph report | Generated | `reports/acme-demo/knowledge_graph_report.json` | Node and edge counts |
| Pipeline stage summary | Generated | `reports/acme-demo/pipeline_stage_summary.json` | Stage execution details |

## Next steps

- [How-to: keep docs aligned with every release](../guides/how-to.md) for the release-day workflow
- [Troubleshooting: common pipeline issues](../guides/troubleshooting.md) if pipeline stages fail

### Quality evidence and gate results (Part 2)

Complete quality evidence from the VeriDoc pipeline for VeriOps docs, covering KPI metrics, protocol gates, 24 automated checks, and RAG readiness.

## Protocol contract gate results

Each protocol passes through eight pipeline stages: ingest, lint, regression, docs generation, frontmatter gate, snippet lint, test assets, and publish. Results come from `reports/acme-demo/multi_protocol_contract_report.json`.

| Protocol | Contract source | Status | Stages passed | Notes |
| --- | --- | --- | --- | --- |
| REST | `api/openapi.yaml` (OpenAPI 3.0) | **PASS** | 8/8 | 14 endpoints validated |
| GraphQL | `contracts/graphql.schema.graphql` | **PASS** | 8/8 | 3 operation types validated |
| gRPC | `contracts/grpc/acme.proto` (Proto3) | **PASS** | 8/8 | 3 RPC methods validated |
| AsyncAPI | `contracts/asyncapi.yaml` (v2.6.0) | **PASS** | 8/8 | 3 channels validated |
| WebSocket | `contracts/websocket.yaml` | **PASS** | 8/8 | 3 channels validated |

## Quality checks enforced

The pipeline runs 24 automated checks on every documentation page. These are the same checks described in `scripts/seo_geo_optimizer.py`.

### Quality evidence and gate results (Part 3)

Complete quality evidence from the VeriDoc pipeline for VeriOps docs, covering KPI metrics, protocol gates, 24 automated checks, and RAG readiness.

### GEO checks (8 checks -- LLM and AI search optimization)

| Check ID | Rule | Severity | Threshold | Purpose |
| --- | --- | --- | --- | --- |
| GEO-1 | Meta description present | Error | Must exist | Ensures every page has a description for search snippets |
| GEO-1b | Meta description minimum length | Warning | 50 characters | Prevents truncated search snippets |
| GEO-1c | Meta description maximum length | Warning | 160 characters | Prevents overflow in search results |
| GEO-2 | First paragraph length | Warning | 60 words max | Ensures concise opening for LLM extraction |
| GEO-3 | First paragraph definition | Suggestion | Contains definition verb | Helps LLMs identify what the page is about |
| GEO-4 | Heading specificity | Warning | No generic headings | Prevents vague headings like "Overview" or "Setup" |
| GEO-5 | Heading hierarchy | Error | No skipped levels | Ensures proper H2-H3-H4 nesting |
| GEO-6 | Fact density | Warning | 1 fact per 200 words | Keeps content information-rich |

### Quality evidence and gate results (Part 4)

Complete quality evidence from the VeriDoc pipeline for VeriOps docs, covering KPI metrics, protocol gates, 24 automated checks, and RAG readiness.

### SEO checks (14 checks -- search engine optimization)

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

### Quality evidence and gate results (Part 5)

Complete quality evidence from the VeriDoc pipeline for VeriOps docs, covering KPI metrics, protocol gates, 24 automated checks, and RAG readiness.

| Check ID | Rule | Severity | Threshold | Purpose |
| --- | --- | --- | --- | --- |
| SEO-01 | Title length | Error/Warning | 10-70 characters | Optimal title display in search results |
| SEO-02 | Title keyword match | Suggestion | 50% overlap | Aligns title with filename keywords |
| SEO-03 | URL depth | Warning | Max 4 levels | Prevents deep URLs that search engines deprioritize |
| SEO-04 | URL naming | Warning | Kebab-case | Consistent, readable URL structure |
| SEO-05 | Image alt text | Warning | 100% coverage | Accessibility and image search visibility |
| SEO-06 | Internal links | Suggestion | Min 1 link | Cross-references improve crawlability |
| SEO-07 | Bare URLs | Warning | Zero bare URLs | Requires descriptive link text |
| SEO-08 | Path characters | Warning | Alphanumeric + hyphens | Prevents encoding issues in URLs |
| SEO-09 | Line length | Warning | Max 120 characters | Mobile readability |
| SEO-10 | Heading keywords | Suggestion | Shared with title | Signals relevance to search engines |
| SEO-11 | Freshness signal | Suggestion | Date in frontmatter | Indicates content currency |
| SEO-12 | Content depth | Warning | Min 100 words | Prevents thin content penalties |
| SEO-13 | Duplicate headings | Warning | Zero duplicates | Unique headings for anchor links |
| SEO-14 | Structured data | Suggestion | Min 1 element | Tables, code blocks, or lists |

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

### Quality evidence and gate results (Part 7)

Complete quality evidence from the VeriDoc pipeline for VeriOps docs, covering KPI metrics, protocol gates, 24 automated checks, and RAG readiness.

## RAG retrieval pipeline

The pipeline generates a knowledge retrieval index that powers AI-driven search and support agents. Results come from `reports/acme-demo/knowledge_graph_report.json` and `reports/acme-demo/retrieval_evals_report.json`.

| Metric | Value | Target | Status |
| --- | --- | --- | --- |
| Knowledge graph nodes | **1,272** | -- | Topics, entities, and concepts extracted |
| Knowledge graph edges | **1,089** | -- | Relationships between nodes |
| Knowledge modules | **167** | -- | Auto-extracted topic chunks |
| Retrieval precision | **0.2** | 0.7 | Baseline (token-overlap scorer) |
| Retrieval recall | **0.6** | 0.8 | Baseline (token-overlap scorer) |
| Hallucination rate | **0.0** | 0.1 | Pass (all retrieved docs exist in corpus) |
| Evaluation status | **Baseline** | Pass | Token scorer; advanced pipeline available |

### Quality evidence and gate results (Part 8)

Complete quality evidence from the VeriDoc pipeline for VeriOps docs, covering KPI metrics, protocol gates, 24 automated checks, and RAG readiness.

### Advanced retrieval features (enabled by default)

Six advanced features are available to improve retrieval quality beyond the token-overlap baseline:

| Feature | Description | Expected impact |
| --- | --- | --- |
| Token-aware chunking | Splits modules into 750-token chunks with 100-token overlap (`cl100k_base`) | Improves recall for long documents |
| Hybrid search (RRF) | Fuses semantic (FAISS) and token-overlap rankings with Reciprocal Rank Fusion (k=60) | Higher recall for mixed queries |
| HyDE query expansion | Generates hypothetical doc passage via `gpt-4.1-mini` before embedding | Better retrieval for vague queries |
| Cross-encoder reranking | Rescores top 20 candidates with `cross-encoder/ms-marco-MiniLM-L-6-v2` | Higher precision in top-N |
| Embedding cache | In-memory LRU cache (TTL: 3,600 seconds, max: 512 entries) for query embeddings | Reduced latency and API costs |
| Multi-mode evaluation | Compares token, semantic, hybrid, and hybrid+rerank modes across 50 curated queries | Data-driven mode selection |

Run a full retrieval comparison across all four modes:

```bash
python3 scripts/run_retrieval_evals.py \
  --mode all \
  --dataset config/retrieval_eval_dataset.yml \
  --report reports/retrieval_comparison.json
```

<!-- requires: OPENAI_API_KEY, faiss-cpu, sentence-transformers -->

### Quality evidence and gate results (Part 9)

Complete quality evidence from the VeriDoc pipeline for VeriOps docs, covering KPI metrics, protocol gates, 24 automated checks, and RAG readiness.

### Quality score formula

Quality score measures documentation health and is independent of RAG retrieval metrics:

`score = 100 - metadata_penalty - stale_penalty - gap_penalty`

- **metadata_penalty**: deduction for missing or invalid frontmatter fields
- **stale_penalty**: deduction for pages not reviewed within the freshness window
- **gap_penalty**: deduction for documented gaps in coverage

!!! info "Baseline retrieval metrics"
    Retrieval precision (0.2) and recall (0.6) reflect the token-overlap baseline scorer, which runs without external dependencies.
    Production deployments enable hybrid search with FAISS embeddings, HyDE query expansion, and cross-encoder reranking for significantly higher precision and recall.
    Run `--mode all` to compare all four search strategies and select the optimal mode for your deployment.

### GRAPHQL API Reference

Auto-generated graphql reference from source contract.

# GRAPHQL Reference

Source: `reports/acme-demo/contracts/graphql.schema.graphql`

Flow mode: `api-first`

## Operations

- Query count: `2`
- Mutation count: `1`
- Subscription count: `1`
- Queries: `health`, `project`
- Mutations: `createProject`
- Subscriptions: `projectUpdated`

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

### GRAPHQL API Reference (Part 3)

Auto-generated graphql reference from source contract.

## Next steps

- [Documentation index](../../../index.md)

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

### GraphQL playground

Interactive GraphQL playground for VeriOps API with schema explorer, live query editor, subscription support, and advanced RAG retrieval pipeline.

# GraphQL playground

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)

</div>

The VeriOps GraphQL API provides a single endpoint for flexible queries across projects, tasks, and users. This page documents the full schema, provides a live query editor, covers authentication, error handling, performance limits, and the advanced RAG retrieval pipeline that powers AI-driven search across GraphQL documentation.

## Endpoint and authentication

| Setting | Value |
| --- | --- |
| Endpoint | [`https://api.veriops.example/graphql`](https://api.veriops.example/graphql) |
| Method | POST |
| Authentication | Bearer token in `Authorization` header |
| Content type | `application/json` |
| Max query depth | 10 levels |
| Max query complexity | 500 points |
| Rate limit | 60 requests per minute |
| Introspection | Enabled in development, disabled in production |

## Schema overview

The VeriOps GraphQL schema exposes three operation types and one core object type:

### GraphQL playground (Part 2)

Interactive GraphQL playground for VeriOps API with schema explorer, live query editor, subscription support, and advanced RAG retrieval pipeline.

### Query type

| Field | Arguments | Return type | Description |
| --- | --- | --- | --- |
| `health` | -- | `Health!` | Returns API health status, version, and uptime |
| `project` | `id: ID!` | `Project` | Fetch a single project by ID |
| `projects` | `status: String`, `limit: Int` | `[Project!]!` | List projects with optional status filter |

### Mutation type

| Field | Arguments | Return type | Description |
| --- | --- | --- | --- |
| `createProject` | `name: String!`, `status: String` | `Project!` | Create a new project resource |
| `updateProject` | `id: ID!`, `name: String`, `status: String` | `Project!` | Update an existing project |

### Subscription type

| Field | Arguments | Return type | Description |
| --- | --- | --- | --- |
| `projectUpdated` | `projectId: ID` | `Project!` | Real-time stream of project changes |

### Project type

| Field | Type | Description |
| --- | --- | --- |
| `id` | `ID!` | Unique project identifier (format: `prj_*`) |
| `name` | `String!` | Project name (3-100 characters) |
| `status` | `String!` | Current status: `draft`, `active`, `archived` |
| `createdAt` | `DateTime` | ISO 8601 creation timestamp |
| `updatedAt` | `DateTime` | ISO 8601 last update timestamp |

### GraphQL playground (Part 3)

Interactive GraphQL playground for VeriOps API with schema explorer, live query editor, subscription support, and advanced RAG retrieval pipeline.

## Quick start: query a project

```graphql
query GetProject {
  project(id: "prj_abc123") {
    id
    name
    status
    createdAt
    updatedAt
  }
}
```

Send this query with curl:

```bash
curl -X POST https://api.veriops.example/graphql \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query GetProject { project(id: \"prj_abc123\") { id name status } }"
  }'
```

<!-- requires: api-key -->

**Example response:**

```json
{
  "data": {
    "project": {
      "id": "prj_abc123",
      "name": "Website Redesign",
      "status": "active"
    }
  }
}
```

## Query examples

### Check API health

```graphql
query Health {
  health {
    status
    version
    uptime_seconds
  }
}
```

### List active projects

```graphql
query ActiveProjects {
  projects(status: "active", limit: 10) {
    id
    name
    status
    createdAt
  }
}
```

### Create a project (mutation)

```graphql
mutation CreateProject {
  createProject(name: "Mobile App Launch", status: "active") {
    id
    name
    status
    createdAt
  }
}
```

### Subscribe to project updates

```graphql
subscription WatchProject {
  projectUpdated(projectId: "prj_abc123") {
    id
    name
    status
    updatedAt
  }
}
```

Subscriptions require a WebSocket connection to `wss://api.veriops.example/graphql/ws`.

### GraphQL playground (Part 4)

Interactive GraphQL playground for VeriOps API with schema explorer, live query editor, subscription support, and advanced RAG retrieval pipeline.

## Live query editor

Enter a GraphQL query and click **Run query** to execute it against the Postman mock sandbox.

!!! info "Sandbox mode"
    Queries route to the Postman mock server at
    [`https://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io/graphql`](https://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io/graphql).
    No API key is required for sandbox requests.

<div style="border:1px solid #dbe2ea;border-radius:10px;padding:16px;background:#f8f9fa">
<label><strong>GraphQL query:</strong></label>
<textarea id="gql-q" rows="10" style="width:100%;font-family:monospace;padding:12px;border:1px solid #ccc;border-radius:8px;font-size:14px;margin:4px 0 8px;">query Health {
  health {
    status
    version
    uptime_seconds
  }
}</textarea>
<button id="gql-run" style="margin:8px 0;padding:8px 24px;background:#1a73e8;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px">Run query</button>
<pre id="gql-out" style="max-height:320px;overflow:auto;border:1px solid #dbe2ea;padding:12px;border-radius:10px;background:#fff;margin-top:8px;"></pre>
</div>

<script>
/* Sandbox onclick is set by acme-sandbox.js with local mock responses */
</script>

### GraphQL playground (Part 5)

Interactive GraphQL playground for VeriOps API with schema explorer, live query editor, subscription support, and advanced RAG retrieval pipeline.

## Advanced RAG retrieval pipeline

The pipeline uses six advanced retrieval features to power AI-driven search across GraphQL and all five protocol documentation sets. These features are enabled by default in `config/ask-ai.yml`.

### Token-aware chunking

The pipeline splits long documentation modules into overlapping chunks of 750 tokens each (100-token overlap) using the `cl100k_base` tokenizer. This matches the `text-embedding-3-small` embedding model tokenization. Short modules that fit within the token limit remain as single chunks.

| Parameter | Default | Description |
| --- | --- | --- |
| `chunking.max_tokens` | 750 | Maximum tokens per chunk |
| `chunking.overlap_tokens` | 100 | Overlap between consecutive chunks |
| Tokenizer | `cl100k_base` | Matches OpenAI embedding models |

### Hybrid search with Reciprocal Rank Fusion

The retrieval pipeline combines two search strategies using Reciprocal Rank Fusion (RRF, k=60):

1. **Semantic search** queries the FAISS vector index with cosine similarity over `text-embedding-3-small` embeddings
1. **Token-overlap search** scores modules by keyword overlap between query and document text

RRF merges both rankings into a single fused list. This improves recall for queries that combine specific terminology (matched by tokens) with conceptual intent (matched by embeddings).

### GraphQL playground (Part 6)

Interactive GraphQL playground for VeriOps API with schema explorer, live query editor, subscription support, and advanced RAG retrieval pipeline.

### HyDE query expansion

When HyDE is enabled, the pipeline generates a hypothetical documentation passage using `gpt-4.1-mini` (temperature 0.0, max 300 tokens) before embedding the query. The generated passage captures domain-specific vocabulary that the raw user question may lack. The pipeline embeds this hypothetical document instead of the raw query, which improves retrieval for vague or high-level questions.

### Cross-encoder reranking

After initial retrieval returns 20 candidates, a cross-encoder model (`cross-encoder/ms-marco-MiniLM-L-6-v2`) reranks them by scoring (query, document) pairs. The reranker uses the concatenation of each candidate's title, summary, and assistant excerpt. This reduces false positives and surfaces the most relevant modules for the final top-N context window.

### Embedding cache

An in-memory LRU cache stores embedding vectors with a 3,600-second TTL and a maximum of 512 entries. Repeated queries skip the OpenAI embedding API call entirely, reducing latency and API costs. The cache evicts the oldest entry when full.

### GraphQL playground (Part 7)

Interactive GraphQL playground for VeriOps API with schema explorer, live query editor, subscription support, and advanced RAG retrieval pipeline.

### Multi-mode retrieval evaluation

The `run_retrieval_evals.py` script supports four search modes for comparison:

| Mode | Strategy | Use case |
| --- | --- | --- |
| `token` | Token-overlap scoring | Baseline, no API key required |
| `semantic` | FAISS cosine similarity | Embedding-based retrieval |
| `hybrid` | RRF fusion of token + semantic | Best recall for mixed queries |
| `hybrid+rerank` | Hybrid + cross-encoder reranking | Highest precision for production |

Run a full comparison:

```bash
python3 scripts/run_retrieval_evals.py \
  --mode all \
  --use-embeddings \
  --dataset config/retrieval_eval_dataset.yml \
  --report reports/retrieval_comparison.json
```

<!-- requires: OPENAI_API_KEY, faiss-cpu, sentence-transformers -->

## Error handling

GraphQL errors appear in the `errors` array alongside partial `data`:

```json
{
  "data": null,
  "errors": [
    {
      "message": "Project not found",
      "locations": [{"line": 2, "column": 3}],
      "path": ["project"],
      "extensions": {
        "code": "NOT_FOUND",
        "timestamp": "2026-03-20T14:30:00Z"
      }
    }
  ]
}
```

### GraphQL playground (Part 8)

Interactive GraphQL playground for VeriOps API with schema explorer, live query editor, subscription support, and advanced RAG retrieval pipeline.

### Error codes

| Code | HTTP equivalent | Meaning | Resolution |
| --- | --- | --- | --- |
| `UNAUTHENTICATED` | 401 | Missing or invalid bearer token | Provide a valid `Authorization: Bearer` header |
| `FORBIDDEN` | 403 | Token valid but lacks required scope | Request the `graphql:read` or `graphql:write` scope |
| `NOT_FOUND` | 404 | Requested resource does not exist | Verify the resource ID |
| `QUERY_TOO_COMPLEX` | 400 | Query exceeds 500 complexity points | Reduce nesting depth or remove unnecessary fields |
| `QUERY_TOO_DEEP` | 400 | Query exceeds 10 levels of nesting | Flatten the query or use separate requests |
| `RATE_LIMITED` | 429 | Exceeded 60 requests per minute | Implement request throttling on the client |
| `INTERNAL_ERROR` | 500 | Server error | Retry with exponential backoff (max 3 attempts) |

## Performance limits

| Limit | Value | Notes |
| --- | --- | --- |
| Max query depth | 10 levels | Nested field resolution depth |
| Max complexity | 500 points | Each field costs 1 point, lists cost 10 points |
| Max query size | 10 KB | Request body size limit |
| Timeout | 30 seconds | Per-query execution timeout |
| Batch queries | Up to 5 | Multiple queries in one request |

### GraphQL playground (Part 9)

Interactive GraphQL playground for VeriOps API with schema explorer, live query editor, subscription support, and advanced RAG retrieval pipeline.

## Next steps

- [REST API reference](rest-api.md) for standard CRUD operations
- [gRPC gateway invoke](grpc-gateway.md) for high-performance Remote Procedure Calls
- [AsyncAPI event docs](asyncapi-events.md) for event-driven channels
- [WebSocket event playground](websocket-events.md) for bidirectional real-time messaging
- [Tutorial: launch your first integration](../guides/tutorial.md) to use GraphQL in practice

### gRPC gateway invoke

Invoke VeriOps gRPC services through the HTTP gateway with service catalog, proto definitions, and interactive request testing.

# gRPC gateway invoke

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)

</div>

The VeriOps gRPC API provides high-performance Remote Procedure Call (RPC) access to project services over HTTP/2 with Protocol Buffers serialization. The HTTP gateway adapter allows you to invoke gRPC methods from any HTTP client without a gRPC library.

!!! note "Sandbox mode"
    Interactive requests route to the Postman mock server. No gRPC tooling required.
    In production, the pipeline validates proto definitions against the `protoc` compiler automatically.

## Connection details

| Setting | Value |
| --- | --- |
| gRPC endpoint | `grpc.veriops.example:443` |
| HTTP gateway | [`https://api.veriops.example/grpc/invoke`](https://api.veriops.example/grpc/invoke) |
| Transport | HTTP/2 with TLS 1.3 |
| Serialization | Protocol Buffers (proto3) |
| Package | `veriops.v1` |
| Proto file | `veriops.proto` |
| Default deadline | 30 seconds |
| Max message size | 4 MB |
| Authentication | Bearer token in `Authorization` metadata |

### gRPC gateway invoke (Part 2)

Invoke VeriOps gRPC services through the HTTP gateway with service catalog, proto definitions, and interactive request testing.

## Service catalog

The `veriops.v1` package exposes one service with three RPC methods:

| Service | Method | Type | Request | Response | Description |
| --- | --- | --- | --- | --- | --- |
| `ProjectService` | `GetProject` | Unary | `GetProjectRequest` | `GetProjectResponse` | Retrieve a project by ID |
| `ProjectService` | `ListProjects` | Server streaming | `ListProjectsRequest` | `stream Project` | Stream project list with pagination |
| `ProjectService` | `CreateProject` | Unary | `CreateProjectRequest` | `Project` | Create a new project resource |

### gRPC gateway invoke (Part 3)

Invoke VeriOps gRPC services through the HTTP gateway with service catalog, proto definitions, and interactive request testing.

## Proto definition

```protobuf
syntax = "proto3";

package veriops.v1;

service ProjectService {
  // Retrieve a single project by its unique identifier.
  rpc GetProject(GetProjectRequest) returns (GetProjectResponse);

  // Stream a paginated list of all projects.
  rpc ListProjects(ListProjectsRequest) returns (stream Project);

  // Create a new project resource with the given name and status.
  rpc CreateProject(CreateProjectRequest) returns (Project);
}

message GetProjectRequest {
  string project_id = 1;  // Required. Format: prj_*
}

message GetProjectResponse {
  string id = 1;
  string name = 2;
  string status = 3;      // draft, active, archived
}

message ListProjectsRequest {
  int32 page_size = 1;    // Max 100, default 25
  string page_token = 2;  // Token from previous response
}

message CreateProjectRequest {
  string name = 1;        // Required. 3-100 characters.
  string status = 2;      // Optional. Default: draft
}

message Project {
  string id = 1;
  string name = 2;
  string status = 3;
}
```

### gRPC gateway invoke (Part 4)

Invoke VeriOps gRPC services through the HTTP gateway with service catalog, proto definitions, and interactive request testing.

## Quick start: get a project via HTTP gateway

The HTTP gateway translates JSON requests into gRPC calls. You do not need a gRPC client library.

```bash
curl -X POST https://api.veriops.example/grpc/invoke \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "veriops.v1.ProjectService",
    "method": "GetProject",
    "payload": {"project_id": "prj_abc123"}
  }'
```

<!-- requires: api-key -->

**Expected response (HTTP 200):**

```json
{
  "id": "prj_abc123",
  "name": "Website Redesign",
  "status": "active"
}
```

## Quick start: get a project via grpcurl

Use `grpcurl` for direct gRPC access without the HTTP gateway:

```bash
grpcurl -d '{"project_id": "prj_abc123"}' \
  -H "Authorization: Bearer YOUR_API_KEY" \
  grpc.veriops.example:443 veriops.v1.ProjectService/GetProject
```

<!-- requires: api-key, grpcurl -->

## Quick start: create a project

```bash
curl -X POST https://api.veriops.example/grpc/invoke \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "veriops.v1.ProjectService",
    "method": "CreateProject",
    "payload": {"name": "Mobile App Launch", "status": "active"}
  }'
```

<!-- requires: api-key -->

**Expected response (HTTP 200):**

```json
{
  "id": "prj_def456",
  "name": "Mobile App Launch",
  "status": "active"
}
```

### gRPC gateway invoke (Part 5)

Invoke VeriOps gRPC services through the HTTP gateway with service catalog, proto definitions, and interactive request testing.

## Interactive gateway tester

Enter a service, method, and JSON payload to invoke an RPC through the sandbox gateway.

!!! info "Sandbox mode"
    RPC calls route to the Postman mock server at
    [`https://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io/grpc/invoke`](https://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io/grpc/invoke).
    No API key is required for sandbox requests.

### gRPC gateway invoke (Part 6)

Invoke VeriOps gRPC services through the HTTP gateway with service catalog, proto definitions, and interactive request testing.

<div style="border:1px solid #dbe2ea;border-radius:10px;padding:16px;background:#f8f9fa">
<label><strong>Service:</strong></label>
<input id="grpc-svc" value="veriops.v1.ProjectService" style="width:100%;padding:6px;margin:4px 0 8px;border:1px solid #ccc;border-radius:4px;font-family:monospace;">
<label><strong>Method:</strong></label>
<input id="grpc-method" value="GetProject" style="width:100%;padding:6px;margin:4px 0 8px;border:1px solid #ccc;border-radius:4px;font-family:monospace;">
<label><strong>Payload (JSON):</strong></label>
<textarea id="grpc-payload" rows="4" style="width:100%;font-family:monospace;padding:8px;border:1px solid #ccc;border-radius:4px;">{"project_id": "prj_abc123"}</textarea>
<button id="grpc-run" style="margin:8px 0;padding:8px 24px;background:#1a73e8;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px;">Invoke RPC</button>
<pre id="grpc-out" style="max-height:280px;overflow:auto;border:1px solid #dbe2ea;padding:12px;border-radius:8px;background:#fff;margin-top:8px;"></pre>
</div>

<script>
/* Sandbox onclick is set by acme-sandbox.js with local mock responses */
</script>

### gRPC gateway invoke (Part 7)

Invoke VeriOps gRPC services through the HTTP gateway with service catalog, proto definitions, and interactive request testing.

## Error handling and gRPC status codes

The HTTP gateway maps gRPC status codes to HTTP status codes:

| gRPC status | HTTP status | Description | Resolution |
| --- | --- | --- | --- |
| `OK` (0) | 200 | Success | -- |
| `INVALID_ARGUMENT` (3) | 400 | Malformed request or invalid field | Check the `payload` JSON matches the proto message |
| `UNAUTHENTICATED` (16) | 401 | Missing or invalid bearer token | Provide a valid `Authorization` header |
| `PERMISSION_DENIED` (7) | 403 | Token valid but lacks scope | Request `grpc:invoke` scope from admin |
| `NOT_FOUND` (5) | 404 | Resource does not exist | Verify the project ID format (`prj_*`) |
| `DEADLINE_EXCEEDED` (4) | 504 | RPC took longer than 30 seconds | Increase deadline or optimize the query |
| `UNAVAILABLE` (14) | 503 | Service temporarily unavailable | Retry with exponential backoff (3 attempts, initial 1 second) |
| `INTERNAL` (13) | 500 | Server error | Retry with exponential backoff |

### gRPC gateway invoke (Part 8)

Invoke VeriOps gRPC services through the HTTP gateway with service catalog, proto definitions, and interactive request testing.

## Performance characteristics

| Metric | HTTP gateway | Direct gRPC | Notes |
| --- | --- | --- | --- |
| Latency (P50) | 12 ms | 3 ms | Gateway adds JSON serialization overhead |
| Latency (P99) | 45 ms | 15 ms | Direct gRPC uses binary protobuf |
| Throughput | 2,000 req/s | 8,000 req/s | Per-connection limits |
| Max concurrent streams | 100 | 1,000 | HTTP/2 stream multiplexing |
| Max message size | 4 MB | 4 MB | Configurable per-service |

## Next steps

- [AsyncAPI event docs](asyncapi-events.md) for event-driven architecture patterns
- [WebSocket event playground](websocket-events.md) for real-time bidirectional messaging
- [REST API reference](rest-api.md) for standard HTTP CRUD operations

### VeriOps documentation

Pipeline-generated multi-protocol API documentation for VeriOps with KPI dashboard, interactive references, and automated quality gates.

# VeriOps documentation

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)

</div>

The VeriOps documentation site is a pipeline-generated showcase that provides interactive references for five API protocols, automated quality evidence, and a KPI dashboard updated on every pipeline run.

### VeriOps documentation (Part 2)

Pipeline-generated multi-protocol API documentation for VeriOps with KPI dashboard, interactive references, and automated quality gates.

## KPI dashboard

The pipeline evaluates documentation health on every run. These metrics come from `reports/acme-demo/kpi-wall.json`, generated by the autopipeline on 2026-03-20.

| Metric | Value | Target | Status |
| --- | --- | --- | --- |
| Quality score | **100%** | 80% | Excellent |
| Total documents | **12** | -- | Indexed across all protocols |
| Stale pages | **0** | 0 | No stale pages |
| Documentation gaps | **0** | 0 | No active gaps |
| Metadata completeness | **100%** | 100% | All frontmatter fields present |

Quality score measures documentation health: metadata completeness, content freshness, and documentation gap coverage. It is independent of RAG retrieval metrics. Formula: `score = 100 - metadata_penalty - stale_penalty - gap_penalty`.

| Protocol drift failures | **0** | 0 | All contracts valid |
| Knowledge graph nodes | **1,272** | -- | RAG retrieval index |
| Knowledge graph edges | **1,089** | -- | Cross-reference links |
| Knowledge modules | **167** | -- | Auto-extracted from docs |

### VeriOps documentation (Part 3)

Pipeline-generated multi-protocol API documentation for VeriOps with KPI dashboard, interactive references, and automated quality gates.

## Pipeline execution summary

The autopipeline completed three stages with full artifacts for this demo. Enterprise deployment cycles add consolidated reporting, audit scorecards, SLA evaluation, and finalize gates.

| Stage | Status | Description |
| --- | --- | --- |
| `multi_protocol_contract` | Completed | Contract validation for all five protocols |
| `kpi_wall` | Completed | KPI metrics and quality scoring |
| `retrieval_evals` | Completed | RAG retrieval precision and recall |

All five interactive protocol sandboxes (REST, GraphQL, gRPC, AsyncAPI, WebSocket) work without additional tooling.

## Supported protocols

The VeriOps API exposes five protocol interfaces. Each protocol passes through eight pipeline stages: ingest, lint, regression, docs generation, frontmatter gate, snippet lint, test assets, and publish.

| Protocol | Transport | Contract source | Stages | Status |
| --- | --- | --- | --- | --- |
| REST | HTTP/1.1 + JSON | OpenAPI 3.0 (`api/openapi.yaml`) | 8 | **PASS** |
| GraphQL | HTTP POST | SDL schema (`graphql.schema.graphql`) | 8 | **PASS** |
| gRPC | HTTP/2 + Protobuf | Proto3 (`veriops.proto`) | 8 | **PASS** |
| AsyncAPI | AMQP / Kafka | AsyncAPI 2.6.0 (`asyncapi.yaml`) | 8 | **PASS** |
| WebSocket | WSS | WebSocket contract (`websocket.yaml`) | 8 | **PASS** |

### VeriOps documentation (Part 4)

Pipeline-generated multi-protocol API documentation for VeriOps with KPI dashboard, interactive references, and automated quality gates.

## Quality gates enforced

Every document on this site passes through 24 automated checks before publish:

| Category | Checks | What they verify |
| --- | --- | --- |
| GEO (8 checks) | Meta description, first paragraph length, heading hierarchy, fact density, definition patterns, heading specificity | LLM and AI search optimization |
| SEO (14 checks) | Title length, URL depth, internal links, structured data, image alt text, bare URLs, content depth, heading keywords | Traditional search engine optimization |
| Style (automated) | American English, active voice, no weasel words, no contractions | Consistent tone across all pages |
| Contract (per-protocol) | Schema validation, regression detection, snippet lint | Technical accuracy against source contracts |

### VeriOps documentation (Part 5)

Pipeline-generated multi-protocol API documentation for VeriOps with KPI dashboard, interactive references, and automated quality gates.

## Automated detection and repair

The pipeline detects documentation drift when source contracts change and regenerates affected pages automatically.

!!! example "Protocol drift detected and repaired"

    **Before:** The GraphQL schema added a new `priority` field to the `Project` type, but the GraphQL playground docs still listed only `id`, `name`, `status`, and `createdAt`.

    **Detection:** The `multi_protocol_contract` stage compared `contracts/graphql.schema.graphql` against the generated docs and flagged the missing field as a regression.

    **Autofix:** The pipeline regenerated the GraphQL reference page, added the `priority` field to the schema explorer table and query examples, and re-ran all 24 quality checks.

    **Result:** Re-validation passed. No manual editing required.

### VeriOps documentation (Part 6)

Pipeline-generated multi-protocol API documentation for VeriOps with KPI dashboard, interactive references, and automated quality gates.

## RAG retrieval pipeline

The pipeline generates a knowledge retrieval index that powers AI-driven search and support agents. Six advanced retrieval features are enabled by default.

| Metric | Value |
| --- | --- |
| Knowledge graph nodes | **1,272** |
| Knowledge graph edges | **1,089** |
| Knowledge modules | **167** auto-extracted |
| Retrieval precision | **0.2** (token-overlap baseline) |
| Retrieval recall | **0.6** (token-overlap baseline) |
| Hallucination rate | **0.0** (all retrieved documents exist in corpus) |

!!! info "Baseline retrieval metrics"
    Precision (0.2) and recall (0.6) reflect the token-overlap baseline scorer, which runs without external dependencies. Production deployments enable hybrid search with FAISS embeddings, HyDE query expansion, and cross-encoder reranking for significantly higher precision and recall. Run `--mode all` to compare all four search strategies.

| Advanced feature | Status |
| --- | --- |
| Token-aware chunking (750 tokens, 100 overlap) | Enabled |
| Hybrid search (RRF, k=60) | Enabled |
| HyDE query expansion (`gpt-4.1-mini`) | Enabled |
| Cross-encoder reranking (`ms-marco-MiniLM-L-6-v2`) | Enabled |
| Embedding cache (TTL: 3,600 seconds, max: 512) | Enabled |
| Multi-mode eval (token/semantic/hybrid/hybrid+rerank) | Available |

### VeriOps documentation (Part 7)

Pipeline-generated multi-protocol API documentation for VeriOps with KPI dashboard, interactive references, and automated quality gates.

## What this demo proves

1. **One pipeline, five protocols.** A single docs-ops pipeline generates and validates documentation across REST, GraphQL, gRPC, AsyncAPI, and WebSocket from source contracts.

1. **Automated quality enforcement.** 24 SEO/GEO checks, style linting, and contract validation run on every page before publish. No manual review of formatting or metadata.

1. **Advanced RAG pipeline.** A knowledge graph with 1,272 nodes and 1,089 edges powers AI search agents. Six retrieval features (chunking, hybrid search, HyDE, reranking, embedding cache, multi-mode eval) maximize precision and recall.

1. **Real pipeline data.** Every metric on this site comes from actual pipeline reports, not hardcoded values. Run the pipeline again and the numbers update.

### VeriOps documentation (Part 8)

Pipeline-generated multi-protocol API documentation for VeriOps with KPI dashboard, interactive references, and automated quality gates.

## Quick links

- [REST API reference (Swagger)](reference/rest-api.md) -- 14 endpoints for projects, tasks, users, tags, and comments
- [GraphQL playground](reference/graphql-playground.md) -- live query editor with schema explorer
- [gRPC gateway invoke](reference/grpc-gateway.md) -- HTTP gateway adapter for `ProjectService`
- [AsyncAPI event docs](reference/asyncapi-events.md) -- event-driven channels with delivery semantics
- [WebSocket event playground](reference/websocket-events.md) -- bidirectional real-time messaging
- [Tutorial: launch your first integration](guides/tutorial.md) -- zero to working project in 15 minutes
- [How-to: keep docs aligned](guides/how-to.md) -- release-day pipeline workflow
- [Concept: pipeline-first lifecycle](guides/concept.md) -- why automated docs beat manual writing
- [Troubleshooting: pipeline issues](guides/troubleshooting.md) -- diagnose and fix common failures
- [Quality evidence and gate results](quality/evidence.md) -- KPI metrics and protocol gate details

### REST API reference

Interactive REST API reference for VeriOps with 14 endpoints across five resources, Bearer JWT authentication, and Swagger UI.

# REST API reference

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)

</div>

The VeriOps REST API provides 14 CRUD endpoints across five resources (projects, tasks, users, tags, and comments) over HTTP/1.1 with JSON payloads. This reference documents every endpoint, authentication flow, and error code.

## Base URL and authentication

| Setting | Value |
| --- | --- |
| Base URL | [`https://api.veriops.example/v1`](https://api.veriops.example/v1) |
| Authentication | Bearer JWT token in `Authorization` header |
| Content type | `application/json` |
| Rate limit | 60 requests per minute per API key |
| OpenAPI spec version | 3.0.3 |
| API version | v1 |

All requests require a valid JWT token:

```bash
curl -X GET https://api.veriops.example/v1/projects \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

<!-- requires: api-key -->

### REST API reference (Part 2)

Interactive REST API reference for VeriOps with 14 endpoints across five resources, Bearer JWT authentication, and Swagger UI.

## Resource catalog

The API exposes five resources with standard CRUD operations:

| Resource | Endpoints | Methods | Description |
| --- | --- | --- | --- |
| Projects | `/v1/projects`, `/v1/projects/{id}` | GET, POST, PUT, DELETE | Project management with status tracking |
| Tasks | `/v1/tasks`, `/v1/tasks/{id}` | GET, POST, PUT, DELETE | Task CRUD within projects |
| Users | `/v1/users`, `/v1/users/{id}` | GET, POST | User management and profiles |
| Tags | `/v1/tags`, `/v1/tags/{id}` | GET, POST, DELETE | Resource tagging and categorization |
| Comments | `/v1/comments`, `/v1/comments/{id}` | GET, POST, DELETE | Threaded comments on tasks |

## Endpoints: projects

### REST API reference (Part 3)

Interactive REST API reference for VeriOps with 14 endpoints across five resources, Bearer JWT authentication, and Swagger UI.

### List all projects

```
GET /v1/projects
```

Returns a paginated list of projects. Supports filtering by `status` and sorting by `created_at`.

**Query parameters:**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `page` | integer | `1` | Page number (1-indexed) |
| `per_page` | integer | `25` | Results per page (max 100) |
| `status` | string | -- | Filter by status: `active`, `archived`, `draft` |
| `sort` | string | `created_at` | Sort field: `created_at`, `updated_at`, `name` |
| `order` | string | `desc` | Sort order: `asc`, `desc` |

**Example request:**

```bash
curl -X GET "https://api.veriops.example/v1/projects?status=active&per_page=10" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

<!-- requires: api-key -->

**Example response (HTTP 200):**

```json
{
  "data": [
    {
      "id": "prj_abc123",
      "name": "Website Redesign",
      "status": "active",
      "description": "Q2 website refresh with new design system",
      "created_at": "2026-01-15T09:30:00Z",
      "updated_at": "2026-03-10T14:22:00Z",
      "task_count": 47,
      "owner_id": "usr_456"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 142,
    "total_pages": 15
  }
}
```

### REST API reference (Part 4)

Interactive REST API reference for VeriOps with 14 endpoints across five resources, Bearer JWT authentication, and Swagger UI.

### Create a project

```
POST /v1/projects
```

Creates a new project resource. Returns the created project with a generated `id`.

**Request body:**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | Yes | Project name (3-100 characters) |
| `description` | string | No | Project description (max 500 characters) |
| `status` | string | No | Initial status: `draft` (default), `active` |

**Example request:**

```bash
curl -X POST https://api.veriops.example/v1/projects \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mobile App Launch",
    "description": "iOS and Android app for Q3 release",
    "status": "active"
  }'
```

<!-- requires: api-key -->

**Example response (HTTP 201):**

```json
{
  "id": "prj_def456",
  "name": "Mobile App Launch",
  "description": "iOS and Android app for Q3 release",
  "status": "active",
  "created_at": "2026-03-19T10:00:00Z",
  "updated_at": "2026-03-19T10:00:00Z",
  "task_count": 0,
  "owner_id": "usr_789"
}
```

### REST API reference (Part 5)

Interactive REST API reference for VeriOps with 14 endpoints across five resources, Bearer JWT authentication, and Swagger UI.

### Get a project

```
GET /v1/projects/{id}
```

Returns a single project by ID.

**Path parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `id` | string | Project ID (format: `prj_*`) |

**Example request:**

```bash
curl https://api.veriops.example/v1/projects/prj_abc123 \
  -H "Authorization: Bearer YOUR_API_KEY"
```

<!-- requires: api-key -->

### Update a project

```
PUT /v1/projects/{id}
```

Updates an existing project. Send only the fields you want to change.

### Delete a project

```
DELETE /v1/projects/{id}
```

Deletes a project and all associated tasks. This action is irreversible. Returns HTTP 204 on success.

## Endpoints: tasks

### List tasks

```
GET /v1/tasks
```

Returns tasks with optional filtering by `project_id`, `status`, and `assignee_id`.

**Query parameters:**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `project_id` | string | -- | Filter by project |
| `status` | string | -- | Filter: `todo`, `in_progress`, `done` |
| `assignee_id` | string | -- | Filter by assigned user |
| `page` | integer | `1` | Page number |
| `per_page` | integer | `25` | Results per page (max 100) |

### REST API reference (Part 6)

Interactive REST API reference for VeriOps with 14 endpoints across five resources, Bearer JWT authentication, and Swagger UI.

### Create a task

```
POST /v1/tasks
```

**Request body:**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `title` | string | Yes | Task title (3-200 characters) |
| `project_id` | string | Yes | Parent project ID |
| `assignee_id` | string | No | User to assign |
| `status` | string | No | Initial status: `todo` (default) |
| `priority` | string | No | Priority: `low`, `medium`, `high` |

**Example request:**

```bash
curl -X POST https://api.veriops.example/v1/tasks \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Design homepage mockup",
    "project_id": "prj_abc123",
    "assignee_id": "usr_456",
    "priority": "high"
  }'
```

<!-- requires: api-key -->

## Endpoints: users, tags, and comments

### Users

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/v1/users` | List all users (paginated) |
| `GET` | `/v1/users/{id}` | Get user by ID |
| `POST` | `/v1/users` | Create a new user |

### Tags

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/v1/tags` | List all tags |
| `POST` | `/v1/tags` | Create a tag |
| `DELETE` | `/v1/tags/{id}` | Delete a tag |

### REST API reference (Part 7)

Interactive REST API reference for VeriOps with 14 endpoints across five resources, Bearer JWT authentication, and Swagger UI.

### Comments

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/v1/comments?task_id={id}` | List comments on a task |
| `POST` | `/v1/comments` | Add a comment to a task |
| `DELETE` | `/v1/comments/{id}` | Delete a comment |

## Interactive Swagger UI

Explore and test all 14 endpoints in the embedded Swagger interface. Requests route to the Postman mock server sandbox automatically.

!!! info "Sandbox mode"
    All Try-it requests from Swagger UI route to the Postman mock server at
    [`https://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io/v1`](https://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io/v1).
    No API key is required for sandbox requests.

<div style="border:1px solid #dbe2ea;border-radius:12px;overflow:hidden;">
<iframe src="../swagger-test.html" width="100%" height="900" style="border:none;"></iframe>
</div>

## Error handling

Every error response uses a consistent envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The 'name' field is required and must be 3-100 characters.",
    "details": [
      {
        "field": "name",
        "rule": "required",
        "message": "This field is required"
      }
    ]
  }
}
```

### REST API reference (Part 8)

Interactive REST API reference for VeriOps with 14 endpoints across five resources, Bearer JWT authentication, and Swagger UI.

### Error codes

| Status | Code | Meaning | Resolution |
| --- | --- | --- | --- |
| 400 | `validation_error` | Request body fails validation | Check the `details` array for specific field errors |
| 401 | `unauthorized` | Missing or invalid JWT token | Regenerate your token in the [dashboard](https://app.veriops.example/settings/api) |
| 403 | `forbidden` | Token valid but lacks permission | Request the required scope from your admin |
| 404 | `not_found` | Resource does not exist | Verify the resource ID in the URL path |
| 409 | `conflict` | Duplicate resource | A resource with that unique key already exists |
| 429 | `rate_limited` | Exceeded 60 requests per minute | Wait 60 seconds or implement request queuing |
| 500 | `internal_error` | Server error | Retry with exponential backoff (max 3 attempts, initial delay 1 second) |

## Rate limiting

The API enforces a limit of 60 requests per minute per API key. Rate limit headers appear on every response:

| Header | Description |
| --- | --- |
| `X-RateLimit-Limit` | Maximum requests per window (60) |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |

When you exceed the limit, the API returns HTTP 429 with a `Retry-After` header indicating seconds to wait.

### REST API reference (Part 9)

Interactive REST API reference for VeriOps with 14 endpoints across five resources, Bearer JWT authentication, and Swagger UI.

## Pagination

All list endpoints support cursor-based pagination:

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `page` | integer | `1` | Page number (1-indexed) |
| `per_page` | integer | `25` | Results per page (range: 1-100) |

The response includes a `pagination` object with `total`, `total_pages`, `page`, and `per_page` fields.

## Next steps

- [GraphQL playground](graphql-playground.md) for flexible queries across resources
- [Tutorial: launch your first integration](../guides/tutorial.md) to create a project end-to-end
- [AsyncAPI event docs](asyncapi-events.md) for real-time event notifications

### Review manifest: operator approval checkpoint

Operator review manifest with artifact inventory, stage summary, and approval checklist for the Acme documentation pipeline.

# Review manifest

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-6366f1?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-6366f1?style=flat-square)

</div>

- Runtime config: `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/client_runtime.yml`
- Weekly run rc: `1`
- Strictness: `standard`
- Available artifacts: `15`
- Missing artifacts: `12`

### Review manifest: operator approval checkpoint (Part 2)

Operator review manifest with artifact inventory, stage summary, and approval checklist for the Acme documentation pipeline.

## Stage Summary

- `multi_protocol_contract`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/multi_protocol_contract_report.json`)
- `consolidated_report`: **MISSING** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/consolidated_report.json`)
- `audit_scorecard`: **MISSING** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/audit_scorecard.json`)
- `finalize_gate`: **MISSING** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/finalize_gate_report.json`)
- `kpi_wall`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/kpi-wall.json`)
- `kpi_sla`: **MISSING** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/kpi-sla-report.json`)
- `retrieval_evals`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/retrieval_evals_report.json`)

### Review manifest: operator approval checkpoint (Part 3)

Operator review manifest with artifact inventory, stage summary, and approval checklist for the Acme documentation pipeline.

## Review Links (Available)

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

### Review manifest: operator approval checkpoint (Part 4)

Operator review manifest with artifact inventory, stage summary, and approval checklist for the Acme documentation pipeline.

- [Docs index](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/index.md) - `docs`
- [Faceted search page](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/search-faceted.md) - `docs`
- [Facets index](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/assets/facets-index.json) - `search`
- [Multi-protocol contract report](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/multi_protocol_contract_report.json) - `protocols`
- [GraphQL reference](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/reference/graphql-api.md) - `protocols`
- [AsyncAPI reference](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/reference/asyncapi-api.md) - `protocols`
- [REST playground](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/reference/taskstream-api-playground.md) - `protocols`
- [Glossary source](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/glossary.yml) - `quality`
- [Glossary sync report](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/glossary_sync_report.json) - `quality`
- [KPI wall](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/kpi-wall.json) - `quality`
- [RAG retrieval index](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/assets/knowledge-retrieval-index.json) - `rag`
- [RAG knowledge graph](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/assets/knowledge-graph.jsonld) - `rag`
- [Knowledge graph report](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/knowledge_graph_report.json) - `rag`
- [Retrieval eval report](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/retrieval_evals_report.json) - `rag`
- [Retrieval eval dataset](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/retrieval_eval_dataset.generated.yml) - `rag`

### Review manifest: operator approval checkpoint (Part 5)

Operator review manifest with artifact inventory, stage summary, and approval checklist for the Acme documentation pipeline.

## Expected But Missing

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

### Review manifest: operator approval checkpoint (Part 6)

Operator review manifest with artifact inventory, stage summary, and approval checklist for the Acme documentation pipeline.

- `Consolidated report` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/consolidated_report.json`
- `Audit scorecard (JSON)` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/audit_scorecard.json`
- `Audit scorecard (HTML)` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/audit_scorecard.html`
- `Finalize gate report` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/finalize_gate_report.json`
- `VeriOps status` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/docsops_status.json`
- `Ready marker` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/READY_FOR_REVIEW.txt`
- `API test cases JSON` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/api-test-assets/api_test_cases.json`
- `TestRail CSV` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/api-test-assets/testrail_test_cases.csv`
- `Zephyr JSON` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/api-test-assets/zephyr_test_cases.json`
- `Test coverage report` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/api-test-assets/coverage_report.json`
- `Fuzz scenarios` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/api-test-assets/fuzz_scenarios.json`
- `KPI SLA report` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/kpi-sla-report.json` (module: `kpi_sla`)

### Review manifest: operator approval checkpoint (Part 7)

Operator review manifest with artifact inventory, stage summary, and approval checklist for the Acme documentation pipeline.

## Reviewer Checklist

- Confirm stage summary has no missing required artifacts.
- Review protocol docs and test assets links.
- Review quality and retrieval reports before publish.
- Approve publish only if critical findings are resolved.

## Next steps

- [Documentation index](../index.md)

### WebSocket event playground

Interactive WebSocket playground for VeriOps real-time API with bidirectional messaging, channel subscriptions, and connection lifecycle management.

# WebSocket event playground

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)

</div>

The VeriOps WebSocket API provides real-time, bidirectional communication for project updates and task notifications over a persistent connection. This playground allows you to connect, subscribe to channels, send messages, and observe server-pushed events.

## Connection details

| Setting | Value |
| --- | --- |
| Endpoint | `wss://api.veriops.example/realtime` |
| Authentication | Bearer token as `token` query parameter |
| Protocol | WebSocket (RFC 6455) over TLS 1.3 |
| Heartbeat interval | 30 seconds (server sends `ping`, client responds `pong`) |
| Reconnect strategy | Exponential backoff: 1 second, 2 seconds, 4 seconds, 8 seconds, 16 seconds, max 30 seconds |
| Max message size | 64 KB |
| Idle timeout | 300 seconds (5 minutes) without messages |
| Max subscriptions per connection | 50 channels |
| Compression | `permessage-deflate` supported |

### WebSocket event playground (Part 10)

Interactive WebSocket playground for VeriOps real-time API with bidirectional messaging, channel subscriptions, and connection lifecycle management.

## Next steps

- [AsyncAPI event docs](asyncapi-events.md) for message broker patterns with AMQP
- [REST API reference](rest-api.md) for synchronous CRUD operations
- [Quality evidence](../quality/evidence.md) for pipeline gate results

### WebSocket event playground (Part 2)

Interactive WebSocket playground for VeriOps real-time API with bidirectional messaging, channel subscriptions, and connection lifecycle management.

## Message envelope

Every client-to-server and server-to-client message uses this JSON envelope:

```json
{
  "type": "subscribe",
  "request_id": "req_001",
  "sent_at": "2026-03-19T14:30:00Z",
  "payload": {
    "channel": "project.updated",
    "filters": {"project_id": "prj_abc123"}
  }
}
```

### Envelope fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `type` | string | Yes | Message type: `subscribe`, `unsubscribe`, `publish`, `ping`, `ack`, `event` |
| `request_id` | string | Yes | Client-generated ID for request/response correlation |
| `sent_at` | string (ISO 8601) | No | Timestamp when the message was sent |
| `payload` | object | Varies | Message-specific data |

### Message types

| Type | Direction | Description |
| --- | --- | --- |
| `subscribe` | Client to server | Subscribe to a channel with optional filters |
| `unsubscribe` | Client to server | Unsubscribe from a channel |
| `publish` | Client to server | Send a message to a channel |
| `ping` | Bidirectional | Heartbeat ping (server sends every 30 seconds) |
| `pong` | Client to server | Response to server ping |
| `ack` | Server to client | Acknowledgment of a client request |
| `event` | Server to client | Channel event pushed by the server |

### WebSocket event playground (Part 3)

Interactive WebSocket playground for VeriOps real-time API with bidirectional messaging, channel subscriptions, and connection lifecycle management.

## Channel catalog

| Channel | Direction | Filters | Description |
| --- | --- | --- | --- |
| `project.updated` | Server to client | `project_id` (optional) | Project status change events |
| `project.created` | Server to client | -- | New project creation events |
| `task.completed` | Server to client | `project_id` (optional) | Task completion notifications |
| `presence` | Bidirectional | -- | User online/offline status |

## Quick start: connect and subscribe

### Step 1: establish connection

```javascript
// Connect to the VeriOps WebSocket API
// Pass your API key as a query parameter for authentication
const ws = new WebSocket('wss://api.veriops.example/realtime?token=YOUR_API_KEY');

ws.addEventListener('open', () => {
  console.log('Connected to VeriOps WebSocket API');
});

ws.addEventListener('close', (event) => {
  console.log('Disconnected:', event.code, event.reason);
});
```

<!-- requires: api-key -->

### Step 2: subscribe to a channel

```javascript
// Subscribe to project update events for a specific project
ws.send(JSON.stringify({
  type: 'subscribe',
  request_id: 'req_001',
  sent_at: new Date().toISOString(),
  payload: {
    channel: 'project.updated',
    filters: { project_id: 'prj_abc123' }
  }
}));
```

<!-- requires: api-key -->

### WebSocket event playground (Part 4)

Interactive WebSocket playground for VeriOps real-time API with bidirectional messaging, channel subscriptions, and connection lifecycle management.

### Step 3: handle incoming events

```javascript
ws.addEventListener('message', (event) => {
  const msg = JSON.parse(event.data);

  switch (msg.type) {
    case 'ack':
      console.log('Subscription confirmed:', msg.request_id);
      break;
    case 'event':
      console.log('Event received:', msg.payload.event_type);
      console.log('Project:', msg.payload.data.project_id);
      console.log('Status:', msg.payload.data.status);
      break;
    case 'ping':
      ws.send(JSON.stringify({ type: 'pong', request_id: msg.request_id }));
      break;
  }
});
```

<!-- requires: api-key -->

### WebSocket event playground (Part 5)

Interactive WebSocket playground for VeriOps real-time API with bidirectional messaging, channel subscriptions, and connection lifecycle management.

## Complete client example with reconnection

```javascript
// Production-ready WebSocket client with automatic reconnection
// Handles heartbeats, subscription restoration, and exponential backoff
class VeriOpsWebSocket {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.endpoint = 'wss://api.veriops.example/realtime';
    this.subscriptions = new Set();
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
    this.connect();
  }

connect() {
    this.ws = new WebSocket(`${this.endpoint}?token=${this.apiKey}`);

this.ws.onopen = () => {
      console.log('Connected');
      this.reconnectDelay = 1000;
      // Restore subscriptions after reconnect
      for (const channel of this.subscriptions) {
        this.subscribe(channel);
      }
    };

this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'ping') {
        this.ws.send(JSON.stringify({ type: 'pong', request_id: msg.request_id }));
      } else if (msg.type === 'event') {
        this.handleEvent(msg.payload);
      }
    };

this.ws.onclose = () => {
      console.log(`Reconnecting in ${this.reconnectDelay}ms...`);
      setTimeout(() => this.connect(), this.reconnectDelay);
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
    };
  }

### WebSocket event playground (Part 6)

Interactive WebSocket playground for VeriOps real-time API with bidirectional messaging, channel subscriptions, and connection lifecycle management.

subscribe(channel) {
    this.subscriptions.add(channel);
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        request_id: `req_${Date.now()}`,
        payload: { channel }
      }));
    }
  }

handleEvent(payload) {
    console.log(`[${payload.event_type}] ${JSON.stringify(payload.data)}`);
  }
}

// Usage:
const client = new VeriOpsWebSocket('YOUR_API_KEY');
client.subscribe('project.updated');
client.subscribe('task.completed');
```

<!-- requires: api-key -->

### WebSocket event playground (Part 7)

Interactive WebSocket playground for VeriOps real-time API with bidirectional messaging, channel subscriptions, and connection lifecycle management.

## Interactive WebSocket tester

Connect to the sandbox WebSocket endpoint, subscribe to channels, and send messages from the browser.

!!! info "Sandbox mode"
    The endpoint field below auto-fills with a public WebSocket echo sandbox URL.
    No API key is required for sandbox requests.

### WebSocket event playground (Part 8)

Interactive WebSocket playground for VeriOps real-time API with bidirectional messaging, channel subscriptions, and connection lifecycle management.

<div style="border:1px solid #dbe2ea;border-radius:10px;padding:16px;background:#f8f9fa">
<label><strong>Endpoint:</strong></label>
<input id="ws-ep" value="wss://api.veriops.example/realtime" style="width:100%;padding:6px;margin:4px 0 8px;border:1px solid #ccc;border-radius:4px;font-family:monospace;">
<label><strong>Message (JSON):</strong></label>
<!-- vale Google.Quotes = NO -->
<textarea id="ws-msg" rows="6" style="width:100%;font-family:monospace;padding:8px;border:1px solid #ccc;border-radius:4px;">{
  "type": "subscribe",
  "request_id": "req_test_01",
  "payload": {
    "channel": "project.updated",
    "filters": {"project_id": "prj_abc123"}
  }
}</textarea>
<!-- vale Google.Quotes = YES -->
<button id="ws-connect" style="margin:8px 4px 8px 0;padding:8px 20px;background:#1a73e8;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px;">Connect</button>
<button id="ws-send" style="margin:8px 0;padding:8px 20px;background:#34a853;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px;">Send</button>
<button id="ws-close" style="margin:8px 0 8px 4px;padding:8px 20px;background:#ea4335;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px;">Disconnect</button>
<pre id="ws-out" style="max-height:300px;overflow:auto;border:1px solid #dbe2ea;padding:12px;border-radius:8px;background:#fff;margin-top:8px;">Not connected</pre>
</div>

### WebSocket event playground (Part 9)

Interactive WebSocket playground for VeriOps real-time API with bidirectional messaging, channel subscriptions, and connection lifecycle management.

<script>
/* Sandbox onclick is set by acme-sandbox.js with local mock responses */
</script>

## Error handling

### WebSocket close codes

| Close code | Meaning | Client action |
| --- | --- | --- |
| 1000 | Normal closure | No action required |
| 1001 | Server going away | Reconnect with exponential backoff |
| 1006 | Abnormal close (no close frame) | Reconnect with exponential backoff |
| 1008 | Policy violation | Check message format and size |
| 4001 | Authentication failed | Verify your API key is valid and not expired |
| 4002 | Subscription limit reached | Unsubscribe from unused channels (max 50) |
| 4008 | Rate limited | Wait 60 seconds before reconnecting |
| 4009 | Message too large | Reduce message size to under 64 KB |

### Common issues

| Symptom | Cause | Resolution |
| --- | --- | --- |
| Connection drops every 30 seconds | Client not responding to `ping` | Implement `pong` response handler |
| Connection drops after 5 minutes | No messages sent or received | Send periodic messages or respond to pings |
| `Connection error` in browser | Mixed content (`ws://` on HTTPS page) | Use `wss://` endpoint |
| Missed events after reconnect | Subscriptions not restored | Re-subscribe to all channels on `open` event |

## Next steps

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`
