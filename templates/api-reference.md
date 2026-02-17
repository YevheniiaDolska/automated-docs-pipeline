---
title: "[Resource] API"
description: "[Resource] API for [primary capability]. Process [X] requests/second with [Y]ms latency. Full CRUD operations with webhook support."
content_type: reference
product: both
tags:
  - API
  - Reference
---

# [Resource] API

The [Resource] API provides programmatic access to [capability]. Process up to [10,000] [operations] per minute with [sub-100ms] latency.

## Quick start

```bash
# Your first API call (takes 30 seconds)
curl https://{{ api_url }}/v1/[resources] \
  -H "Authorization: Bearer sk_live_[your-key]" \
  -d name="My First Resource" \
  -d type="production"

# Response (23ms)
{
  "id": "res_1a2b3c4d5e",
  "name": "My First Resource",
  "created": 1705320000
}
```

## Base URL

```text
Production: https://{{ api_url }}/v1
Sandbox:    https://sandbox.{{ api_url }}/v1
EU Region:  https://eu.{{ api_url }}/v1
```

Rate limits: 10,000 req/min (standard), 50,000 req/min (enterprise)

## Authentication

```bash
# Header authentication (recommended)
Authorization: Bearer sk_live_abc123xyz987

# Query parameter (webhooks only)
?api_key=sk_live_abc123xyz987
```

Test vs Live keys:

- Test: `sk_test_` - Safe for development, no real operations
- Live: `sk_live_` - Production use, real operations

## Endpoints

### List [resources]

`GET /v1/[resources]`

Returns paginated [resources]. Default page size: 20, max: 100.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | `20` | Results per page (1-100) |
| `starting_after` | string | — | Cursor for pagination |
| `created` | object | — | Filter by creation date |
| `created.gte` | integer | — | Created on or after (Unix timestamp) |
| `created.lte` | integer | — | Created on or before |
| `status` | enum | — | Filter by status: `active`, `pending`, `archived` |
| `expand[]` | array | — | Expand nested objects |

#### Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "res_1a2b3c4d5e",
      "object": "resource",
      "created": 1705320000,
      "name": "Production Resource",
      "status": "active",
      "metadata": {
        "order_id": "6789"
      },
      "metrics": {
        "requests_today": 4521,
        "success_rate": 99.97,
        "avg_latency_ms": 47
      }
    }
  ],
  "has_more": true,
  "total_count": 1547
}
```

#### Examples

<details>
<summary>JavaScript (Node.js)</summary>

```javascript
const resources = await fetch('https://{{ api_url }}/v1/resources?limit=10', {
  headers: {
    'Authorization': 'Bearer sk_live_...',
    'Content-Type': 'application/json'
  }
});

const data = await resources.json();
console.log(`Found ${data.total_count} resources`);
// Output: Found 1547 resources
```

</details>

<details>
<summary>Python</summary>

```python
import requests

response = requests.get(
    'https://{{ api_url }}/v1/resources',
    headers={'Authorization': 'Bearer sk_live_...'},
    params={'limit': 10, 'status': 'active'}
)

data = response.json()
print(f"Active resources: {data['total_count']}")
# Output: Active resources: 892
```

</details>

<details>
<summary>Go</summary>

```go
client := &http.Client{Timeout: 10 * time.Second}
req, _ := http.NewRequest("GET", "https://{{ api_url }}/v1/resources", nil)
req.Header.Add("Authorization", "Bearer sk_live_...")

resp, _ := client.Do(req)
// Process response
```

</details>

---

### Create [resource]

`POST /v1/[resources]`

Creates a new [resource]. Returns immediately (< 100ms) while processing happens asynchronously.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | **Yes** | Display name (3-255 chars) |
| `type` | enum | **Yes** | Type: `production`, `staging`, `development` |
| `configuration` | object | No | Configuration settings |
| `configuration.timeout_ms` | integer | No | Timeout in ms (100-30000, default: 5000) |
| `configuration.retry_count` | integer | No | Retry attempts (0-5, default: 3) |
| `configuration.batch_size` | integer | No | Batch size (1-1000, default: 100) |
| `metadata` | object | No | Key-value pairs (max 20 keys, 500 chars per value) |
| `idempotency_key` | string | No | Ensure exactly-once execution |

#### Request

```bash
curl https://{{ api_url }}/v1/resources \
  -H "Authorization: Bearer sk_live_..." \
  -H "Idempotency-Key: unique_key_123" \
  -d name="Production API Resource" \
  -d type="production" \
  -d "configuration[timeout_ms]=10000" \
  -d "configuration[retry_count]=5" \
  -d "metadata[team]"="platform" \
  -d "metadata[environment]"="prod"
```

#### Response

```json
{
  "id": "res_7x8y9z0a1b",
  "object": "resource",
  "created": 1705320000,
  "name": "Production API Resource",
  "type": "production",
  "status": "pending",
  "configuration": {
    "timeout_ms": 10000,
    "retry_count": 5,
    "batch_size": 100
  },
  "metadata": {
    "team": "platform",
    "environment": "prod"
  },
  "provisioning": {
    "status": "in_progress",
    "estimated_completion": 1705320030,
    "steps_completed": 2,
    "steps_total": 5
  }
}
```

#### Idempotency

Use `Idempotency-Key` header to safely retry requests:

```bash
Idempotency-Key: order_12345_create_resource
```

Keys are stored for 24 hours. Retrying with same key returns cached response.

---

### Get [resource]

`GET /v1/[resources]/{id}`

Retrieves a single [resource] with full details.

#### Parameters

| Parameter | Type | Description |
| --- | --- | --- |
| `id` | string | Resource ID (e.g., `res_1a2b3c4d5e`) |
| `expand[]` | array | Expand nested objects: `metrics`, `logs`, `related_resources` |

#### Response

```json
{
  "id": "res_1a2b3c4d5e",
  "object": "resource",
  "created": 1705320000,
  "updated": 1705406400,
  "name": "Production Resource",
  "type": "production",
  "status": "active",
  "configuration": {
    "timeout_ms": 5000,
    "retry_count": 3,
    "batch_size": 100,
    "rate_limit": 1000
  },
  "metrics": {
    "lifetime": {
      "requests": 1547289,
      "success_rate": 99.97,
      "errors": 463
    },
    "last_24h": {
      "requests": 48291,
      "success_rate": 99.99,
      "errors": 5,
      "avg_latency_ms": 47,
      "p95_latency_ms": 124,
      "p99_latency_ms": 201
    }
  },
  "limits": {
    "max_requests_per_minute": 10000,
    "max_batch_size": 1000,
    "max_payload_bytes": 10485760
  }
}
```

---

### Update [resource]

`PATCH /v1/[resources]/{id}`

Updates specified fields. Only include fields you want to change.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | New display name |
| `configuration` | object | Updated configuration (merged with existing) |
| `metadata` | object | Updated metadata (replaces entirely) |
| `status` | enum | Change status: `active`, `paused`, `archived` |

#### Request

```bash
curl -X PATCH https://{{ api_url }}/v1/resources/res_1a2b3c4d5e \
  -H "Authorization: Bearer sk_live_..." \
  -d name="Updated Resource Name" \
  -d "configuration[timeout_ms]=7500" \
  -d status="paused"
```

#### Response

Returns updated resource object with `updated` timestamp.

---

### Delete [resource]

`DELETE /v1/[resources]/{id}`

Permanently deletes a [resource]. This cannot be undone.

#### Request

```bash
curl -X DELETE https://{{ api_url }}/v1/resources/res_1a2b3c4d5e \
  -H "Authorization: Bearer sk_live_..."
```

#### Response

```json
{
  "id": "res_1a2b3c4d5e",
  "object": "resource",
  "deleted": true,
  "deleted_at": 1705406400
}
```

⚠️ **Warning**: Deletion is immediate and permanent. Consider using `status: archived` instead.

---

## Batch operations

Process multiple operations in a single request (up to 100 operations).

### Batch request

`POST /v1/batch`

```json
{
  "operations": [
    {
      "method": "POST",
      "path": "/v1/resources",
      "body": { "name": "Resource 1", "type": "production" }
    },
    {
      "method": "PATCH",
      "path": "/v1/resources/res_abc123",
      "body": { "status": "active" }
    },
    {
      "method": "DELETE",
      "path": "/v1/resources/res_xyz789"
    }
  ]
}
```

### Batch response

```json
{
  "results": [
    {
      "status": 201,
      "body": { "id": "res_new123", "name": "Resource 1" }
    },
    {
      "status": 200,
      "body": { "id": "res_abc123", "status": "active" }
    },
    {
      "status": 204,
      "body": { "deleted": true }
    }
  ],
  "summary": {
    "total": 3,
    "successful": 3,
    "failed": 0,
    "duration_ms": 127
  }
}
```

## Error handling

### Error response format

```json
{
  "error": {
    "type": "invalid_request_error",
    "code": "parameter_invalid",
    "message": "The 'name' parameter must be between 3 and 255 characters.",
    "param": "name",
    "doc_url": "https://docs.example.com/errors/parameter_invalid",
    "request_id": "req_8a7b6c5d4e3f2g1h",
    "request_log_url": "https://dashboard.example.com/logs/req_8a7b6c5d4e3f2g1h"
  }
}
```

### Error types

| Type | HTTP Status | Description | Recovery |
|------|-------------|-------------|----------|
| `api_error` | 500 | Server error | Retry with exponential backoff |
| `authentication_error` | 401 | Invalid API key | Check your API key |
| `invalid_request_error` | 400 | Invalid parameters | Fix parameters and retry |
| `permission_error` | 403 | Insufficient permissions | Check API key scopes |
| `rate_limit_error` | 429 | Too many requests | Retry after `Retry-After` header |
| `resource_not_found` | 404 | Resource doesn't exist | Check resource ID |
| `conflict_error` | 409 | Resource already exists | Use different identifier |
| `timeout_error` | 504 | Request timeout | Retry with idempotency key |

### Retry strategy

```javascript
async function retryWithBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429) {
        // Rate limited - use Retry-After header
        const delay = error.headers['Retry-After'] * 1000;
        await sleep(delay);
      } else if (error.status >= 500) {
        // Server error - exponential backoff
        const delay = Math.min(1000 * Math.pow(2, i), 30000);
        await sleep(delay);
      } else {
        // Client error - don't retry
        throw error;
      }
    }
  }
  throw new Error(`Failed after ${maxRetries} attempts`);
}
```

## Rate limits

### Limits by plan

| Plan | Requests/min | Burst | Concurrent | Monthly quota |
| --- | --- | --- | --- | --- |
| Free | 60 | 100 | 10 | 10,000 |
| Starter | 600 | 1,000 | 50 | 100,000 |
| Growth | 3,000 | 5,000 | 200 | 1,000,000 |
| Scale | 10,000 | 15,000 | 500 | 10,000,000 |
| Enterprise | Custom | Custom | Custom | Unlimited |

### Rate limit headers

```http
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 9847
X-RateLimit-Reset: 1705320600
X-RateLimit-Reset-After: 42
Retry-After: 42
```

### Handling rate limits

```python
import time
import requests

def api_call_with_retry(url, headers):
    while True:
        response = requests.get(url, headers=headers)

        if response.status_code == 429:
            # Rate limited
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            continue

        return response
```

## Webhooks

Receive real-time notifications for [resource] events.

### Available events

| Event | Description | Payload includes |
| --- | --- | --- |
| `resource.created` | Resource was created | Full resource object |
| `resource.updated` | Resource was modified | Changes and full object |
| `resource.deleted` | Resource was deleted | ID and deletion timestamp |
| `resource.status_changed` | Status changed | Old status, new status |
| `resource.limit_exceeded` | Limit was exceeded | Limit type, current value |

### Webhook payload

```json
{
  "id": "evt_1a2b3c4d5e6f7g8h",
  "object": "event",
  "type": "resource.updated",
  "created": 1705320000,
  "api_version": "2024-01-15",
  "data": {
    "object": { /* Full resource object */ },
    "previous_attributes": {
      "name": "Old Name",
      "updated": 1705319900
    }
  },
  "request": {
    "id": "req_8a7b6c5d4e3f2g1h",
    "idempotency_key": "unique_key_123"
  }
}
```

### Webhook security

Verify webhook signatures:

```javascript
const crypto = require('crypto');

function verifyWebhook(payload, signature, secret) {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}
```

## Pagination

Use cursor-based pagination for consistent results:

```javascript
async function* getAllResources(apiKey) {
  let hasMore = true;
  let startingAfter = null;

  while (hasMore) {
    const params = new URLSearchParams({
      limit: 100,
      ...(startingAfter && { starting_after: startingAfter })
    });

    const response = await fetch(
      `https://{{ api_url }}/v1/resources?${params}`,
      { headers: { 'Authorization': `Bearer ${apiKey}` } }
    );

    const data = await response.json();

    for (const resource of data.data) {
      yield resource;
    }

    hasMore = data.has_more;
    if (hasMore && data.data.length > 0) {
      startingAfter = data.data[data.data.length - 1].id;
    }
  }
}

// Usage
for await (const resource of getAllResources('sk_live_...')) {
  console.log(resource.id);
}
```

## Performance

### Response times

| Endpoint | P50 | P95 | P99 |
|----------|-----|-----|-----|
| List resources | 45ms | 120ms | 250ms |
| Get resource | 23ms | 67ms | 145ms |
| Create resource | 67ms | 189ms | 420ms |
| Update resource | 54ms | 156ms | 340ms |
| Delete resource | 31ms | 89ms | 180ms |

### Best practices

1. **Use connection pooling** - Reuse HTTPS connections
1. **Implement retries** - Handle transient failures automatically
1. **Use idempotency keys** - Safely retry write operations
1. **Paginate large datasets** - Use `limit` and `starting_after`
1. **Expand nested objects** - Reduce number of API calls
1. **Cache when possible** - Resources are cache-friendly (ETag support)

## SDKs and libraries

Official SDKs with full type safety and automatic retries:

- **Node.js**: `npm install @example/api-sdk`
- **Python**: `pip install example-api`
- **Go**: `go get github.com/example/example-go`
- **Ruby**: `gem install example`
- **PHP**: `composer require example/example-php`
- **Java**: Maven `com.example:example-java:2.0.0`
- **.NET**: `dotnet add package Example.Api`

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2024-01-15 | Jan 15, 2024 | Added batch operations, improved error messages |
| 2023-11-01 | Nov 1, 2023 | Increased rate limits, added EU region |
| 2023-09-15 | Sep 15, 2023 | Added webhook signature verification |

## Support

- **Documentation**: <https://docs.example.com/api>
- **Status page**: <https://status.example.com>
- **Support**: <support@example.com>
- **Response time**: < 2 hours (business), < 30 min (enterprise)
