---
title: "REST API reference"
description: "Stripe-quality REST reference template for OpenAPI-driven docs with auth, pagination, idempotency, errors, retries, and operational limits."
content_type: reference
product: both
tags:
  - API
  - REST
  - OpenAPI
  - Reference
---

# REST API reference

Use this template to document a production REST API from your OpenAPI contract. Start with one complete request and response that users can run immediately.

## Base URL and authentication

```text
Base URL: https://{{ api_host }}/v1
Auth: Authorization: Bearer {{ api_token_example }}
Content-Type: application/json
Idempotency: Idempotency-Key header required for create/update endpoints
```

## Quick start request

```bash
curl -X POST "https://{{ api_host }}/v1/projects" \
  -H "Authorization: Bearer {{ api_token_example }}" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: 6c37f5aa-bfd7-4e90-b694-f3a1aef8d146" \
  -d '{
    "name": "Payments reliability",
    "environment": "production",
    "owner_email": "owner@example.com"
  }'
```

```json
{
  "id": "prj_01J4D4M2WY3Q",
  "name": "Payments reliability",
  "environment": "production",
  "status": "active",
  "created_at": "2026-03-31T09:12:41Z"
}
```

## Endpoint catalog

| Method | Path | Purpose | Auth scope |
| --- | --- | --- | --- |
| `POST` | `/projects` | Create a project | `projects:write` |
| `GET` | `/projects/{project_id}` | Fetch one project | `projects:read` |
| `GET` | `/projects` | List projects with pagination | `projects:read` |
| `PATCH` | `/projects/{project_id}` | Update project fields | `projects:write` |
| `DELETE` | `/projects/{project_id}` | Archive a project | `projects:write` |

## Pagination

- Cursor pagination: `?limit=50&starting_after=prj_...`
- Maximum `limit`: `100`
- Default `limit`: `25`
- Response includes `has_more` and `next_cursor`

## Error model

```json
{
  "error": {
    "type": "invalid_request_error",
    "code": "validation_failed",
    "message": "environment must be one of: development, staging, production",
    "request_id": "req_01J4D4M9F56T"
  }
}
```

| Status | Code | Meaning | Retry |
| --- | --- | --- | --- |
| `400` | `validation_failed` | Invalid field or payload shape | No |
| `401` | `unauthorized` | Missing or invalid token | No |
| `403` | `forbidden` | Scope/role does not allow action | No |
| `404` | `not_found` | Resource does not exist | No |
| `409` | `idempotency_conflict` | Key reused with different payload | No |
| `429` | `rate_limited` | Per-tenant quota exceeded | Yes |
| `500` | `internal_error` | Unexpected server fault | Yes |

## Reliability and performance

- Timeout budget: client `10s`, server `8s`.
- Retry only `429`, `500`, and `503` with exponential backoff and jitter.
- Include `X-Request-Id` in support tickets and incident timelines.
- Respect rate-limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`.

## Security checklist

- Enforce TLS 1.2+ for all endpoints.
- Validate tenant ownership on every resource operation.
- Never log full tokens or secrets.
- Restrict write scopes for automation tokens.

## Testing checklist

- Contract validation against bundled OpenAPI.
- Positive and negative auth matrix.
- Idempotency replay behavior.
- Pagination consistency across inserts/deletes.
- Error schema shape and request ID presence.

## Next steps

- [API endpoint template](../api-endpoint.md)
- [Protocol snippet pack](api-protocol-snippets.md)
