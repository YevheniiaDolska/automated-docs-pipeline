---
title: "Intent experience: secure for developer"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

# Intent experience: secure for developer

This page is assembled for the `secure` intent and the `developer` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent secure --audience developer --channel docs
```

## Included modules

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
