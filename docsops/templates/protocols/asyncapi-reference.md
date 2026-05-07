---
title: "AsyncAPI reference"
description: "Stripe-quality AsyncAPI reference template for event-driven architectures with publish/subscribe contracts, schema evolution, and delivery semantics."
content_type: reference
product: both
tags:
  - API
  - AsyncAPI
  - Reference
---

# AsyncAPI reference

Use this template for event-driven API docs (Kafka, RabbitMQ, WebSocket, MQTT) with explicit producer/consumer contracts.

## Broker and auth

```text
Broker: {{ broker_url }}
Protocol: {{ broker_protocol }}
Auth: {{ auth_model }}
```

## Channels

| Channel | Direction | Payload schema | Retention |
| --- | --- | --- | --- |
| `project.created` | publish | `ProjectCreated` | 7 days |
| `project.updated` | publish | `ProjectUpdated` | 7 days |
| `project.commands` | subscribe | `ProjectCommand` | 24 hours |

## Event example

```json
{
  "event_id": "evt_01J1",
  "event_type": "project.updated",
  "occurred_at": "2026-03-19T12:00:00Z",
  "producer": "project-service",
  "trace_id": "trace_7f41",
  "data": {
    "project_id": "prj_123",
    "status": "active"
  }
}
```

## Delivery semantics

- Delivery guarantee: `at-least-once`
- Ordering key: `project_id`
- Deduplication key: `event_id`
- Replay window: `7 days`

## Consumer contract

- Validate payload schema version before processing.
- Route unknown versions to quarantine queue.
- Enforce idempotent handlers.
- Emit processing metrics and dead-letter counts.

## Schema evolution

- Backward-compatible fields only in minor changes.
- Breaking changes require new event type suffix/version.
- Provide migration guide and dual-publish window.

## Reliability tests

- Publish contract validation for each channel.
- Consumer resilience under duplicate and out-of-order events.
- Dead-letter routing and replay verification.
- Throughput and lag thresholds under load.

## Next steps

- [Documentation index](../index.md)
