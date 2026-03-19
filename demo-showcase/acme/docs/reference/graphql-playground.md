---
title: "GraphQL playground"
description: "Interactive GraphQL playground for Acme API with schema explorer, live query editor, and subscription support for real-time events."
content_type: reference
product: both
tags:
  - Reference
  - API
---

# GraphQL playground

The Acme GraphQL API provides a single endpoint for flexible queries across projects, tasks, and users. This page documents the full schema, provides a live query editor, and covers authentication, error handling, and performance limits.

!!! success "Powered by VeriDoc"
    This page is generated and maintained by the VeriDoc documentation pipeline.
    Schema definitions come from the GraphQL SDL contract at `contracts/graphql.schema.graphql`.

## Endpoint and authentication

| Setting | Value |
| --- | --- |
| Endpoint | `https://api.acme.example/graphql` |
| Method | POST |
| Authentication | Bearer token in `Authorization` header |
| Content type | `application/json` |
| Max query depth | 10 levels |
| Max query complexity | 500 points |
| Rate limit | 60 requests per minute |
| Introspection | Enabled in development, disabled in production |

## Schema overview

The Acme GraphQL schema exposes three operation types and one core object type:

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
curl -X POST https://api.acme.example/graphql \
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

Subscriptions require a WebSocket connection to `wss://api.acme.example/graphql/ws`.

## Live query editor

Enter a GraphQL query and click **Run query** to execute it against the Postman mock sandbox.

!!! info "Sandbox mode"
    Queries route to the Postman mock server at
    `https://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io/graphql`.
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
(() => {
  var sandbox = (window.ACME_SANDBOX && window.ACME_SANDBOX.graphql_url) || '';
  var endpoint = sandbox || 'https://api.acme.example/graphql';
  var run = document.getElementById('gql-run');
  var query = document.getElementById('gql-q');
  var out = document.getElementById('gql-out');
  if (!run) return;
  if (sandbox) { out.textContent = 'Sandbox: ' + sandbox; }
  run.onclick = async function () {
    out.textContent = 'Executing query against ' + (sandbox ? 'sandbox' : 'API') + '...';
    try {
      var r = await fetch(endpoint, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ query: query.value })
      });
      out.textContent = JSON.stringify(JSON.parse(await r.text()), null, 2);
    } catch (e) { out.textContent = 'Error: ' + String(e); }
  };
})();
</script>

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
        "timestamp": "2026-03-19T14:30:00Z"
      }
    }
  ]
}
```

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

## Next steps

- [REST API reference](rest-api.md) for standard CRUD operations
- [gRPC gateway invoke](grpc-gateway.md) for high-performance Remote Procedure Calls
- [Tutorial: launch your first integration](../guides/tutorial.md) to use GraphQL in practice
