---
title: "WebSocket API reference"
description: "Stripe-quality WebSocket reference template with channel contracts, handshake/auth, message envelopes, backpressure, and reconnection patterns."
content_type: reference
product: both
tags:
  - API
  - WebSocket
  - Reference
---

# WebSocket API reference

Use this template for real-time WebSocket APIs with clear connect/auth/send/receive behavior.

## Connection setup

```text
URL: wss://{{ ws_host }}/realtime
Auth: Bearer token in header or signed query param
Heartbeat: ping every 25s, timeout after 60s
```

## Message envelope

```json
{
  "type": "project.update",
  "request_id": "req_01HZY",
  "sent_at": "2026-03-19T12:00:00Z",
  "payload": {
    "project_id": "prj_123",
    "status": "active"
  }
}
```

## Channels/events

| Event | Direction | Payload | Notes |
| --- | --- | --- | --- |
| `project.subscribe` | client -> server | `{ project_id }` | starts stream |
| `project.update` | server -> client | `ProjectUpdate` | incremental change |
| `error` | server -> client | `ErrorEnvelope` | recoverable/fatal |

## Send/receive example

```javascript
const ws = new WebSocket('wss://api.example.com/realtime');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'project.subscribe',
    request_id: 'req_01',
    payload: { project_id: 'prj_123' }
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(msg.type, msg.payload);
};
```

## Reconnect and backpressure

- Reconnect with exponential backoff (`1s`, `2s`, `4s`, max `30s`).
- Resume from last acknowledged offset when supported.
- Apply client-side queue limits to avoid memory growth.
- Drop or compact low-priority updates under pressure.

## Security and limits

- Rotate tokens every `15m`.
- Reject oversized messages (`>128KB`).
- Enforce origin and tenant checks.
- Rate-limit subscription churn.

## Test checklist

- Handshake + auth failures.
- Event contract validation by type.
- Reconnect continuity and duplicate suppression.
- Burst-load behavior and latency SLO.

## Next steps

- [Documentation index](../index.md)
