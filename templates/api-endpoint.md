---
title: "[Method] [resource] endpoint"
description: "[Method] [resource] endpoint [creates/retrieves/updates/deletes] [resource description]. Returns [response type] with [key fields]."
content_type: reference
product: both
tags:
  - Reference
  - API
---

# [Method] [resource]

The [Method] [resource] endpoint [creates/retrieves/updates/deletes] [resource description]. It returns [response description] and supports [pagination/filtering/sorting].

## Request

```
[METHOD] {{ api_url }}/{{ api_version }}/[resources]/{id}
```

### Authentication

This endpoint requires a Bearer token:

```bash
curl -X [METHOD] {{ api_url }}/{{ api_version }}/[resources] \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | Yes | Unique identifier of the [resource]. Format: UUID v4. Example: `res_abc123def456` |

### Query parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `limit` | integer | 20 | Number of results per page. Range: 1-100. |
| `offset` | integer | 0 | Number of results to skip for pagination. |
| `sort` | string | `created_at` | Sort field. Options: `created_at`, `updated_at`, `name`. |
| `order` | string | `desc` | Sort order. Options: `asc`, `desc`. |

### Request body

```json
{
  "name": "Production webhook",
  "url": "https://api.yourapp.com/webhooks/incoming",
  "events": ["order.created", "payment.completed"],
  "active": true,
  "metadata": {
    "environment": "production",
    "team": "payments"
  }
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | Yes | Display name for the [resource]. Max 255 characters. |
| `url` | string | Yes | Destination URL. Must be HTTPS in production. |
| `events` | array | Yes | List of event types to subscribe to. Min 1, max 50. |
| `active` | boolean | No | Whether the [resource] is active. Default: `true`. |
| `metadata` | object | No | Key-value pairs for custom data. Max 20 keys, 500 chars per value. |

## Response

### Success (HTTP [200/201])

```json
{
  "id": "res_abc123def456",
  "name": "Production webhook",
  "url": "https://api.yourapp.com/webhooks/incoming",
  "events": ["order.created", "payment.completed"],
  "active": true,
  "metadata": {
    "environment": "production",
    "team": "payments"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Unique identifier. Format: `res_` prefix + 12 alphanumeric characters. |
| `created_at` | string | ISO 8601 timestamp of creation. |
| `updated_at` | string | ISO 8601 timestamp of last update. |

### Error responses

| Status | Error code | Description | Resolution |
| --- | --- | --- | --- |
| 400 | `validation_error` | Request body fails validation. | Check required fields and value constraints. |
| 401 | `unauthorized` | Missing or invalid API key. | Verify your API key in the dashboard. |
| 403 | `forbidden` | API key lacks permission for this action. | Check API key scopes. |
| 404 | `not_found` | [Resource] with this ID does not exist. | Verify the ID and check if [resource] was deleted. |
| 409 | `conflict` | [Resource] with this name already exists. | Use a different name or update the existing [resource]. |
| 429 | `rate_limited` | Exceeded {{ rate_limit_requests_per_minute }} requests/minute. | Implement exponential backoff. Retry after `Retry-After` header value. |
| 500 | `internal_error` | Unexpected server error. | Retry the request. If persistent, contact {{ support_email }}. |

**Error response body:**

```json
{
  "error": {
    "code": "validation_error",
    "message": "The 'url' field must be a valid HTTPS URL.",
    "param": "url",
    "doc_url": "{{ docs_url }}/reference/errors#validation_error"
  }
}
```

## Code examples

### Create a [resource]

```javascript
// Create a new [resource] with event subscriptions
const response = await fetch('{{ api_url }}/{{ api_version }}/[resources]', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'Production webhook',
    url: 'https://api.yourapp.com/webhooks/incoming',
    events: ['order.created', 'payment.completed'],
    active: true
  })
});

const resource = await response.json();
console.log('Created:', resource.id);
// Output: "Created: res_abc123def456"
```

### List [resources] with pagination

```python
import requests

response = requests.get(
    "{{ api_url }}/{{ api_version }}/[resources]",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    params={"limit": 10, "offset": 0, "sort": "created_at", "order": "desc"}
)

data = response.json()
print(f"Total: {data['total']}, Returned: {len(data['items'])}")
# Output: "Total: 42, Returned: 10"
```

## Rate limits

| Plan | Requests/minute | Burst | Daily limit |
| --- | --- | --- | --- |
| Free | 20 | 5 | 1,000 |
| Pro | {{ rate_limit_requests_per_minute }} | 20 | 100,000 |
| Enterprise | 600 | 100 | Unlimited |

## Related endpoints

- [List [resources]](./list-[resources].md) to retrieve all [resources]
- [Update [resource]](./update-[resource].md) to modify an existing [resource]
- [Delete [resource]](./delete-[resource].md) to remove a [resource]
