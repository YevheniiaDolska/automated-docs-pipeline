---
title: "[Endpoint/Resource] API reference"
description: "Complete API reference for [endpoint] including request/response schemas, authentication, and code examples in multiple languages."
content_type: reference
product: both
tags:
  - Reference
---

# [Endpoint/Resource] API reference

The [endpoint] API allows you to [primary capability]. Use this endpoint to [common use case].

## Base URL

```
https://api.n8n.io/v1/[resource]
```

## Authentication

All requests require authentication via API key:

```bash
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### List [resources]

Retrieves a paginated list of [resources].

**Request:**

```
GET /v1/[resources]
```

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | `integer` | No | Number of results (1-100). Default: `20` |
| `offset` | `integer` | No | Pagination offset. Default: `0` |
| `sort` | `string` | No | Sort field. Options: `created_asc`, `created_desc` |

**Response:**

```json
{
  "data": [
    {
      "id": "res_abc123",
      "name": "Example resource",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "total": 150,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

**Code examples:**

=== "cURL"

    ```bash
    curl -X GET "https://api.n8n.io/v1/[resources]?limit=10" \
      -H "Authorization: Bearer YOUR_API_KEY"
    ```

=== "JavaScript"

    ```javascript
    const response = await fetch('https://api.n8n.io/v1/[resources]', {
      headers: {
        'Authorization': 'Bearer YOUR_API_KEY'
      }
    });
    const data = await response.json();
    ```

=== "Python"

    ```python
    import requests

    response = requests.get(
        'https://api.n8n.io/v1/[resources]',
        headers={'Authorization': 'Bearer YOUR_API_KEY'}
    )
    data = response.json()
    ```

---

### Get [resource]

Retrieves a single [resource] by ID.

**Request:**

```
GET /v1/[resources]/{id}
```

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | `string` | The [resource] ID |

**Response:**

```json
{
  "id": "res_abc123",
  "name": "Example resource",
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T14:45:00Z"
}
```

---

### Create [resource]

Creates a new [resource].

**Request:**

```
POST /v1/[resources]
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | [Resource] name (1-255 characters) |
| `description` | `string` | No | Optional description |
| `config` | `object` | No | Configuration options |

**Example request:**

```json
{
  "name": "My new resource",
  "description": "Optional description",
  "config": {
    "option1": "value1"
  }
}
```

**Response:** `201 Created`

```json
{
  "id": "res_xyz789",
  "name": "My new resource",
  "status": "active",
  "created_at": "2024-01-15T16:00:00Z"
}
```

---

### Update [resource]

Updates an existing [resource].

**Request:**

```
PATCH /v1/[resources]/{id}
```

**Request body:**

Only include fields you want to update.

```json
{
  "name": "Updated name"
}
```

**Response:** `200 OK`

---

### Delete [resource]

Permanently deletes a [resource].

**Request:**

```
DELETE /v1/[resources]/{id}
```

**Response:** `204 No Content`

!!! warning "Irreversible action"
    Deletion cannot be undone. Consider deactivating instead if you might need the [resource] later.

## Error responses

| Status code | Error type | Description |
|-------------|------------|-------------|
| `400` | `VALIDATION_ERROR` | Invalid request parameters |
| `401` | `UNAUTHORIZED` | Missing or invalid API key |
| `403` | `FORBIDDEN` | Insufficient permissions |
| `404` | `NOT_FOUND` | [Resource] not found |
| `429` | `RATE_LIMITED` | Too many requests |
| `500` | `INTERNAL_ERROR` | Server error |

**Error response format:**

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid request parameters",
  "details": [
    {
      "field": "name",
      "message": "Name is required"
    }
  ],
  "request_id": "req_abc123xyz"
}
```

## Rate limits

- **Standard:** 60 requests per minute
- **Burst:** 100 requests per minute (short bursts allowed)

Rate limit headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705320000
```

## Webhooks

[Resource] changes can trigger webhooks. See [Webhooks guide](../how-to/webhooks.md).

## Related

- [Authentication guide](../how-to/authentication.md)
- [Error handling](../concepts/error-handling.md)
- [Rate limits](../reference/rate-limits.md)
