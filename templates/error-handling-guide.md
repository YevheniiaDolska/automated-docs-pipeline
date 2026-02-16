---
title: "Error handling guide"
description: "Handle [Product] API errors effectively. Covers error types, response formats, retry strategies, and debugging techniques."
content_type: how-to
product: both
tags:

  - How-To
  - Reference

---

## Error handling

This guide covers how to handle errors from the [Product] API, including error types, response formats, and best practices for building resilient integrations.

## Error response format

All API errors return a consistent JSON structure:

```json
{
  "error": {
    "type": "validation_error",
    "code": "invalid_parameter",
    "message": "The 'email' field must be a valid email address",
    "param": "email",
    "request_id": "req_abc123xyz"
  }
}
```

| Field | Type | Description |
| ------- | ------ | ------------- |
| `type` | string | Error category (see [Error types](#error-types)) |
| `code` | string | Specific error code |
| `message` | string | Human-readable description |
| `param` | string | Parameter that caused the error (if applicable) |
| `request_id` | string | Unique ID for debugging |

## HTTP status codes

| Status | Meaning | Action |
| -------- | --------- | -------- |
| `400` | Bad Request | Fix request parameters |
| `401` | Unauthorized | Check authentication |
| `403` | Forbidden | Check permissions |
| `404` | Not Found | Verify resource exists |
| `409` | Conflict | Handle race condition |
| `422` | Unprocessable | Fix validation errors |
| `429` | Rate Limited | Implement backoff |
| `500` | Server Error | Retry with backoff |
| `502` | Bad Gateway | Retry with backoff |
| `503` | Unavailable | Retry with backoff |
| `504` | Timeout | Retry with backoff |

## Error types

### `validation_error`

Invalid request parameters.

```json
{
  "error": {
    "type": "validation_error",
    "code": "invalid_parameter",
    "message": "Name cannot be empty",
    "param": "name"
  }
}
```

**Handling:**

```javascript
if (error.type === 'validation_error') {
  // Show error to user
  showFieldError(error.param, error.message);
}
```

### `authentication_error`

Invalid or missing credentials.

```json
{
  "error": {
    "type": "authentication_error",
    "code": "invalid_api_key",
    "message": "The API key provided is invalid"
  }
}
```

**Handling:**

```javascript
if (error.type === 'authentication_error') {
  // Refresh token or prompt for re-authentication
  await refreshCredentials();
}
```

### `authorization_error`

Valid credentials but insufficient permissions.

```json
{
  "error": {
    "type": "authorization_error",
    "code": "insufficient_permissions",
    "message": "Your API key does not have 'write' permission"
  }
}
```

**Handling:** Request additional permissions or use different credentials.

### `not_found_error`

Requested resource doesn't exist.

```json
{
  "error": {
    "type": "not_found_error",
    "code": "resource_not_found",
    "message": "No [resource] found with ID 'abc123'"
  }
}
```

**Handling:**

```javascript
if (error.type === 'not_found_error') {
  // Resource may have been deleted
  await removeLocalReference(resourceId);
}
```

### `conflict_error`

Request conflicts with current state.

```json
{
  "error": {
    "type": "conflict_error",
    "code": "resource_exists",
    "message": "A [resource] with this name already exists"
  }
}
```

**Handling:** Fetch current state and retry or prompt user.

### `rate_limit_error`

Too many requests.

```json
{
  "error": {
    "type": "rate_limit_error",
    "code": "rate_limited",
    "message": "Rate limit exceeded. Retry after 30 seconds"
  }
}
```

**Headers:**

```text
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704067230
Retry-After: 30
```

**Handling:** See [Rate limit handling](#rate-limit-handling).

### `api_error`

Server-side error.

```json
{
  "error": {
    "type": "api_error",
    "code": "internal_error",
    "message": "An unexpected error occurred",
    "request_id": "req_abc123"
  }
}
```

**Handling:** Retry with exponential backoff.

## Error handling implementation

### Basic error handling

```javascript
const makeApiRequest = async (endpoint, options) => {
  const response = await fetch(`${API_URL}${endpoint}`, options);

  if (!response.ok) {
    const error = await response.json();
    throw new ApiError(response.status, error.error);
  }

  return response.json();
};

class ApiError extends Error {
  constructor(status, error) {
    super(error.message);
    this.status = status;
    this.type = error.type;
    this.code = error.code;
    this.param = error.param;
    this.requestId = error.request_id;
  }
}
```

### Comprehensive error handler

```javascript
const handleApiError = (error) => {
  switch (error.type) {
    case 'validation_error':
      return {
        action: 'fix_input',
        field: error.param,
        message: error.message
      };

    case 'authentication_error':
      return {
        action: 'reauthenticate',
        message: 'Please sign in again'
      };

    case 'authorization_error':
      return {
        action: 'request_permission',
        message: 'Additional permissions required'
      };

    case 'not_found_error':
      return {
        action: 'remove_reference',
        message: 'Resource no longer exists'
      };

    case 'rate_limit_error':
      return {
        action: 'retry_later',
        retryAfter: error.retryAfter || 30
      };

    case 'api_error':
    default:
      return {
        action: 'retry',
        message: 'Something went wrong. Please try again.',
        requestId: error.requestId
      };
  }
};
```

## Retry strategies

### Exponential backoff

```javascript
const withRetry = async (fn, options = {}) => {
  const {
    maxRetries = 3,
    baseDelay = 1000,
    maxDelay = 30000,
    retryableStatuses = [429, 500, 502, 503, 504]
  } = options;

  let lastError;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry non-retryable errors
      if (!retryableStatuses.includes(error.status)) {
        throw error;
      }

      // Don't retry after max attempts
      if (attempt === maxRetries) {
        throw error;
      }

      // Calculate delay with jitter
      const delay = Math.min(
        baseDelay * Math.pow(2, attempt) + Math.random() * 1000,
        maxDelay
      );

      console.log(`Retry ${attempt + 1}/${maxRetries} after ${delay}ms`);
      await sleep(delay);
    }
  }

  throw lastError;
};

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
```

### Usage

```javascript
const result = await withRetry(
  () => apiClient.createResource({ name: 'Example' }),
  { maxRetries: 3, baseDelay: 1000 }
);
```

## Rate limit handling

### Check rate limit headers

```javascript
const checkRateLimit = (response) => {
  const remaining = parseInt(response.headers.get('X-RateLimit-Remaining'));
  const reset = parseInt(response.headers.get('X-RateLimit-Reset'));

  if (remaining < 10) {
    console.warn(`Rate limit warning: ${remaining} requests remaining`);
  }

  return { remaining, reset };
};
```

### Handle 429 errors

```javascript
const handleRateLimit = async (error, retryFn) => {
  const retryAfter = error.headers?.['retry-after'] || 30;

  console.log(`Rate limited. Retrying after ${retryAfter}s`);
  await sleep(retryAfter * 1000);

  return retryFn();
};
```

### Proactive rate limiting

```javascript
class RateLimiter {
  constructor(requestsPerMinute) {
    this.tokens = requestsPerMinute;
    this.maxTokens = requestsPerMinute;
    this.lastRefill = Date.now();
  }

  async acquire() {
    this.refill();

    if (this.tokens < 1) {
      const waitTime = 60000 / this.maxTokens;
      await sleep(waitTime);
      this.refill();
    }

    this.tokens--;
  }

  refill() {
    const now = Date.now();
    const elapsed = now - this.lastRefill;
    const refillAmount = (elapsed / 60000) * this.maxTokens;

    this.tokens = Math.min(this.maxTokens, this.tokens + refillAmount);
    this.lastRefill = now;
  }
}

// Usage
const limiter = new RateLimiter(100);

const makeRequest = async () => {
  await limiter.acquire();
  return apiClient.request();
};
```

## Debugging errors

### Use request IDs

Every response includes a `request_id`. Include it when contacting support:

```javascript
try {
  await apiClient.createResource(data);
} catch (error) {
  console.error('API Error:', {
    message: error.message,
    requestId: error.requestId, // Include this in support tickets
    type: error.type,
    code: error.code
  });
}
```

### Enable debug logging

```javascript
const apiClient = new ApiClient({
  debug: true, // Logs all requests and responses
  logger: console
});
```

### Common debugging steps

1. **Check request ID:** Look up in [Dashboard]([URL]) → Logs
1. **Verify request format:** Log raw request before sending
1. **Check credentials:** Ensure correct environment (test/live)
1. **Review rate limits:** Check headers for remaining quota

## Error codes reference

### Validation errors

| Code | Description |
| ------ | ------------- |
| `invalid_parameter` | Parameter value is invalid |
| `missing_parameter` | Required parameter not provided |
| `invalid_format` | Wrong data format (e.g., invalid email) |
| `out_of_range` | Value outside allowed range |
| `too_long` | String exceeds max length |

### Resource errors

| Code | Description |
| ------ | ------------- |
| `resource_not_found` | Resource doesn't exist |
| `resource_exists` | Resource already exists |
| `resource_locked` | Resource is locked for editing |
| `resource_deleted` | Resource was deleted |

### Authentication errors

| Code | Description |
| ------ | ------------- |
| `invalid_api_key` | API key is invalid |
| `expired_api_key` | API key has expired |
| `invalid_token` | OAuth token is invalid |
| `expired_token` | OAuth token has expired |

## Related

- [API Reference](../reference/api.md)
- [Rate limits](../reference/rate-limits.md)
- [Authentication](./authentication.md)
