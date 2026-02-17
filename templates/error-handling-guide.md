---
title: "Error handling guide"
description: "Build resilient integrations with [Product] by classifying errors, retrying safely, surfacing actionable messages, and instrumenting failures."
content_type: how-to
product: both
tags:
  - How-To
  - API
  - Performance
---

# Error handling guide

Use this guide to make failures predictable for both users and operators.

## Error envelope (canonical shape)

```json
{
  "error": {
    "type": "validation_error",
    "code": "invalid_parameter",
    "message": "Field 'email' must be a valid email address",
    "param": "email",
    "request_id": "req_01abc123xyz"
  }
}
```

## Error classes and handling strategy

| Class | HTTP range | Retry? | User action |
| --- | --- | --- | --- |
| Validation | `400`, `422` | No | Fix request payload |
| Authentication | `401` | Conditional | Refresh token/re-authenticate |
| Authorization | `403` | No | Update scopes/permissions |
| Not found | `404` | No | Verify resource ID |
| Conflict | `409` | Conditional | Retry with idempotency key |
| Rate limit | `429` | Yes | Exponential backoff + jitter |
| Server/transient | `5xx` | Yes | Retry with circuit breaker |

## Retry policy (safe defaults)

```javascript
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const shouldRetry = (status) => [408, 409, 429, 500, 502, 503, 504].includes(status);

async function requestWithRetry(send, maxAttempts = 4) {
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      return await send();
    } catch (err) {
      const status = err.status || 0;
      if (!shouldRetry(status) || attempt === maxAttempts) throw err;

      const base = 200 * 2 ** (attempt - 1);
      const jitter = Math.floor(Math.random() * 100);
      await sleep(base + jitter);
    }
  }
}
```

## Idempotency for write operations

Use idempotency keys for create/update endpoints to prevent duplicates on retries.

```http
Idempotency-Key: order-2026-02-17-00042
```

Guidelines:

- One unique key per logical operation.
- Reuse the same key across retries.
- Keep keys for at least 24 hours on server side.

## User-facing vs operator-facing messages

| Audience | Message style |
| --- | --- |
| End user | Clear action, no internal details |
| Developer/operator | Include `request_id`, code, and context |

Example:

- User: "We could not save your profile. Please check email format."
- Operator log: `validation_error invalid_parameter param=email request_id=req_...`

## Logging and tracing requirements

Always log:

- `request_id`
- endpoint and method
- normalized error code
- retry attempt count
- latency and downstream dependency

Never log:

- access tokens
- API keys
- full personal data payloads

## Common pitfalls

- Retrying non-idempotent writes without idempotency keys
- Infinite retries without dead-letter strategy
- Returning raw internal errors to external users

## Adaptation notes for template users

Replace placeholders for your domain error codes and include links to endpoint-specific docs.

## Related docs

- `templates/authentication-guide.md`
- `templates/testing-guide.md`
- `templates/security-guide.md`
