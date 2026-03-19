---
title: "REST API reference"
description: "Interactive REST API reference for Acme with 14 endpoints across five resources, Bearer JWT authentication, and Swagger UI."
content_type: reference
product: both
tags:
  - Reference
  - API
last_reviewed: "2026-03-19"
---

# REST API reference

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-6366f1?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-6366f1?style=flat-square)

</div>

The Acme REST API provides 14 CRUD endpoints across five resources (projects, tasks, users, tags, and comments) over HTTP/1.1 with JSON payloads. This reference documents every endpoint, authentication flow, and error code.

## Base URL and authentication

| Setting | Value |
| --- | --- |
| Base URL | [`https://api.acme.example/v1`](https://api.acme.example/v1) |
| Authentication | Bearer JWT token in `Authorization` header |
| Content type | `application/json` |
| Rate limit | 60 requests per minute per API key |
| OpenAPI spec version | 3.0.3 |
| API version | v1 |

All requests require a valid JWT token:

```bash
curl -X GET https://api.acme.example/v1/projects \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

<!-- requires: api-key -->

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
curl -X GET "https://api.acme.example/v1/projects?status=active&per_page=10" \
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
curl -X POST https://api.acme.example/v1/projects \
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
curl https://api.acme.example/v1/projects/prj_abc123 \
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
curl -X POST https://api.acme.example/v1/tasks \
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

### Error codes

| Status | Code | Meaning | Resolution |
| --- | --- | --- | --- |
| 400 | `validation_error` | Request body fails validation | Check the `details` array for specific field errors |
| 401 | `unauthorized` | Missing or invalid JWT token | Regenerate your token in the [dashboard](https://app.acme.example/settings/api) |
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
