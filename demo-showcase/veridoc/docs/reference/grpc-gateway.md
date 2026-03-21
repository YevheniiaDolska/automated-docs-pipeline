---
title: "gRPC gateway invoke"
description: "Invoke VeriOps gRPC services through the HTTP gateway with service catalog, proto definitions, and interactive request testing."
content_type: reference
product: both
tags:
  - Reference
  - API
last_reviewed: "2026-03-21"
---

# gRPC gateway invoke

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-0b6bcb?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-0b6bcb?style=flat-square)

</div>

The VeriOps gRPC API provides high-performance Remote Procedure Call (RPC) access to project services over HTTP/2 with Protocol Buffers serialization. The HTTP gateway adapter allows you to invoke gRPC methods from any HTTP client without a gRPC library.

!!! info "Sandbox mode"
    Interactive requests route to the Postman mock server. No gRPC tooling required.

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

## Service catalog

The `veriops.v1` package exposes one service with three RPC methods:

| Service | Method | Type | Request | Response | Description |
| --- | --- | --- | --- | --- | --- |
| `ProjectService` | `GetProject` | Unary | `GetProjectRequest` | `GetProjectResponse` | Retrieve a project by ID |
| `ProjectService` | `ListProjects` | Server streaming | `ListProjectsRequest` | `stream Project` | Stream project list with pagination |
| `ProjectService` | `CreateProject` | Unary | `CreateProjectRequest` | `Project` | Create a new project resource |

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

## Interactive gateway tester

Enter a service, method, and JSON payload to invoke an RPC through the sandbox gateway.

!!! info "Sandbox mode"
    RPC calls route to the Postman mock server at
    [`https://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io/grpc/invoke`](https://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io/grpc/invoke).
    No API key is required for sandbox requests.

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
/* Sandbox onclick is set by veriops-sandbox.js with local mock responses */
</script>

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
