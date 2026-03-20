---
title: "WebSocket event playground"
description: "Interactive WebSocket playground for VeriOps real-time API with bidirectional messaging, channel subscriptions, and connection lifecycle management."
content_type: reference
product: both
tags:
  - Reference
  - API
last_reviewed: "2026-03-19"
---

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

## Interactive WebSocket tester

Connect to the sandbox WebSocket endpoint, subscribe to channels, and send messages from the browser.

!!! info "Sandbox mode"
    The endpoint field below auto-fills with a public WebSocket echo sandbox URL.
    No API key is required for sandbox requests.

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

- [AsyncAPI event docs](asyncapi-events.md) for message broker patterns with AMQP
- [REST API reference](rest-api.md) for synchronous CRUD operations
- [Quality evidence](../quality/evidence.md) for pipeline gate results
