---
title: "Acme API platform architecture"
description: "Interactive architecture diagram showing the Acme API platform with 5 protocol gateways, 4 microservices, and data infrastructure across 5 layers."
content_type: concept
product: both
tags:
  - Concept
  - Reference
last_reviewed: "2026-03-19"
---

# Acme API platform architecture

The Acme API platform is a multi-protocol system that exposes 5 API interfaces (REST, GraphQL, gRPC, AsyncAPI, WebSocket) through a unified gateway layer backed by microservices and event-driven infrastructure.

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-6366f1?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyTDEgMTJsNCA0IDctNyA3IDcgNC00TDEyIDJ6Ii8+PC9zdmc+)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-6366f1?style=flat-square)
![Endpoints](https://img.shields.io/badge/Endpoints-19-3b82f6?style=flat-square)

</div>

## Interactive platform diagram

Click any component in the diagram to view its description, key metrics, and technology tags in the detail panel below.

<div class="interactive-diagram" markdown>
<iframe src="../diagrams/acme-architecture.html" title="Acme API platform architecture diagram"></iframe>
</div>

## Layer breakdown

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

## Next steps

- [REST API reference](../reference/rest-api.md) for the full 19-endpoint specification
- [Concept: pipeline-first lifecycle](concept.md) for how the documentation pipeline works
- [Quality evidence](../quality/evidence.md) for gate results and metrics
