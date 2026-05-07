---
title: "gRPC API reference"
description: "Stripe-quality gRPC reference template with service/method contracts, status codes, retries, deadlines, and streaming guidance."
content_type: reference
product: both
tags:
  - API
  - gRPC
  - Reference
---

# gRPC API reference

Use this template for production gRPC service documentation driven by `.proto` contracts.

## Endpoint and transport

```text
Endpoint: {{ grpc_endpoint }}
Transport: HTTP/2 + TLS
Package: {{ proto_package }}
```

## Service catalog

| Service | Method | Type | Purpose |
| --- | --- | --- | --- |
| `ProjectService` | `GetProject` | Unary | Fetch one project |
| `ProjectService` | `ListProjects` | Unary | Cursor-based listing |
| `ProjectService` | `WatchProject` | Server-streaming | Live status updates |

## Unary method example

```proto
rpc GetProject(GetProjectRequest) returns (GetProjectResponse);
```

```bash
grpcurl -H "authorization: Bearer ${TOKEN}" \
  -d '{"project_id":"prj_123"}' \
  {{ grpc_endpoint }} {{ proto_package }}.ProjectService/GetProject
```

## Streaming example

```proto
rpc WatchProject(WatchProjectRequest) returns (stream ProjectEvent);
```

Document reconnect semantics, heartbeat policy, and consumer idempotency here.

## Status codes and retry policy

| Code | Meaning | Retry |
| --- | --- | --- |
| `OK` | Success | No |
| `INVALID_ARGUMENT` | Invalid request field | No |
| `UNAUTHENTICATED` | Missing/invalid token | No |
| `PERMISSION_DENIED` | Scope/role mismatch | No |
| `UNAVAILABLE` | Transient transport/service issue | Yes, exponential backoff |
| `DEADLINE_EXCEEDED` | Timeout reached | Maybe, with tighter payload |

## Deadlines and budgets

- Unary default deadline: `2s`
- Streaming heartbeat timeout: `30s`
- Maximum inbound message size: `4 MB`

## Contract and compatibility

- Never reuse field numbers.
- Prefer additive changes over removals.
- Mark deprecated fields with migration deadline.
- Keep one release of dual-write/dual-read for breaking migrations.

## Test checklist

- Unary positive/negative coverage.
- Streaming reconnect and duplicate event handling.
- Proto regression snapshot and compatibility checks.
- Authz matrix by role and environment.

## Next steps

- [Documentation index](../index.md)
