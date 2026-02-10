---
title: "[Language] SDK reference"
description: "Complete reference for the [Product] [Language] SDK. Covers installation, client configuration, all methods, error handling, and code examples."
content_type: reference
product: both
tags:
  - Reference
---

# [Language] SDK reference

Official [Language] SDK for [Product].

| | |
|--|--|
| **Package** | `[package-name]` |
| **Version** | `[version]` |
| **Source** | [GitHub]([url]) |
| **License** | MIT |

## Installation

=== "npm"

    ```bash
    npm install [package-name]
    ```

=== "yarn"

    ```bash
    yarn add [package-name]
    ```

=== "pnpm"

    ```bash
    pnpm add [package-name]
    ```

**Requirements:**

- Node.js 18+ (for JavaScript)
- Python 3.8+ (for Python)
- [Other requirements]

## Quick start

```javascript
import { [Product]Client } from '[package-name]';

const client = new [Product]Client({
  apiKey: process.env.[PRODUCT]_API_KEY
});

// Create a [resource]
const [resource] = await client.[resources].create({
  name: 'Example'
});

console.log([resource].id);
```

## Client configuration

### Constructor options

```javascript
const client = new [Product]Client(options);
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiKey` | `string` | — | API key (required unless using OAuth) |
| `accessToken` | `string` | — | OAuth access token |
| `environment` | `'test' \| 'live'` | `'live'` | API environment |
| `timeout` | `number` | `30000` | Request timeout (ms) |
| `maxRetries` | `number` | `3` | Max retry attempts |
| `baseUrl` | `string` | API URL | Custom API URL |

### TypeScript support

Full TypeScript support with exported types:

```typescript
import {
  [Product]Client,
  [Resource],
  Create[Resource]Params,
  [Resource]ListParams
} from '[package-name]';

const client = new [Product]Client({ apiKey: '...' });

const params: Create[Resource]Params = {
  name: 'Example',
  status: 'active'
};

const [resource]: [Resource] = await client.[resources].create(params);
```

## Resources

### [Resources]

#### List [resources]

```javascript
const { data, pagination } = await client.[resources].list({
  limit: 20,
  status: 'active'
});
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | `number` | Results per page (1-100) |
| `starting_after` | `string` | Cursor for pagination |
| `status` | `string` | Filter by status |

**Returns:** `{ data: [Resource][], pagination: Pagination }`

#### Get [resource]

```javascript
const [resource] = await client.[resources].get('[resource_id]');
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | `string` | [Resource] ID |

**Returns:** `[Resource]`

**Throws:** `NotFoundError` if [resource] doesn't exist.

#### Create [resource]

```javascript
const [resource] = await client.[resources].create({
  name: 'New [resource]',
  [field]: 'value'
});
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `string` | Yes | [Resource] name |
| `[field]` | `string` | No | [Field description] |
| `metadata` | `object` | No | Custom key-value pairs |

**Returns:** `[Resource]`

#### Update [resource]

```javascript
const [resource] = await client.[resources].update('[resource_id]', {
  name: 'Updated name'
});
```

Only provided fields are updated.

**Returns:** `[Resource]`

#### Delete [resource]

```javascript
await client.[resources].delete('[resource_id]');
```

**Returns:** `void`

**Throws:** `NotFoundError` if [resource] doesn't exist.

### [Other resources]

[Repeat pattern for other resources]

## Pagination

All list methods return paginated results:

```javascript
// Manual pagination
let cursor = null;
do {
  const { data, pagination } = await client.[resources].list({
    limit: 100,
    starting_after: cursor
  });

  for (const item of data) {
    process(item);
  }

  cursor = pagination.has_more ? data[data.length - 1].id : null;
} while (cursor);
```

### Auto-pagination

```javascript
// Async iterator (recommended)
for await (const [resource] of client.[resources].list({ limit: 100 })) {
  process([resource]);
}

// Or collect all
const all = await client.[resources].list({ limit: 100 }).toArray();
```

## Error handling

### Error types

```javascript
import {
  [Product]Error,
  ValidationError,
  AuthenticationError,
  NotFoundError,
  RateLimitError
} from '[package-name]';

try {
  await client.[resources].create({ /* invalid data */ });
} catch (error) {
  if (error instanceof ValidationError) {
    console.error('Validation failed:', error.param, error.message);
  } else if (error instanceof AuthenticationError) {
    console.error('Auth failed:', error.message);
  } else if (error instanceof NotFoundError) {
    console.error('Not found:', error.message);
  } else if (error instanceof RateLimitError) {
    console.error('Rate limited. Retry after:', error.retryAfter);
  } else if (error instanceof [Product]Error) {
    console.error('API error:', error.code, error.message);
    console.error('Request ID:', error.requestId);
  } else {
    throw error;
  }
}
```

### Error properties

| Property | Type | Description |
|----------|------|-------------|
| `type` | `string` | Error type |
| `code` | `string` | Error code |
| `message` | `string` | Error message |
| `param` | `string` | Invalid parameter (validation errors) |
| `requestId` | `string` | Request ID for debugging |
| `status` | `number` | HTTP status code |
| `retryAfter` | `number` | Seconds to wait (rate limits) |

## Webhooks

### Verify webhook signatures

```javascript
import { verifyWebhookSignature } from '[package-name]';

app.post('/webhooks', (req, res) => {
  const signature = req.headers['x-[product]-signature'];
  const isValid = verifyWebhookSignature(
    req.rawBody,
    signature,
    process.env.WEBHOOK_SECRET
  );

  if (!isValid) {
    return res.status(401).send('Invalid signature');
  }

  const event = JSON.parse(req.rawBody);
  // Handle event...

  res.sendStatus(200);
});
```

### Construct event

```javascript
import { constructWebhookEvent } from '[package-name]';

const event = constructWebhookEvent(
  req.rawBody,
  req.headers['x-[product]-signature'],
  process.env.WEBHOOK_SECRET
);

console.log(event.type); // '[resource].created'
console.log(event.data); // Event data
```

## Idempotency

Prevent duplicate operations with idempotency keys:

```javascript
const [resource] = await client.[resources].create(
  { name: 'Example' },
  { idempotencyKey: 'unique-request-id-123' }
);
```

## Metadata

Attach custom data to resources:

```javascript
const [resource] = await client.[resources].create({
  name: 'Example',
  metadata: {
    customField: 'value',
    anotherField: '123'
  }
});

// Access metadata
console.log([resource].metadata.customField);
```

## Logging

Enable debug logging:

```javascript
const client = new [Product]Client({
  apiKey: '...',
  logger: console, // or custom logger
  logLevel: 'debug' // 'debug' | 'info' | 'warn' | 'error'
});
```

## Testing

### Mock client

```javascript
import { Mock[Product]Client } from '[package-name]/testing';

const mockClient = new Mock[Product]Client();

mockClient.[resources].create.mockResolvedValue({
  id: 'mock_123',
  name: 'Mocked'
});

// Use in tests
const result = await mockClient.[resources].create({ name: 'Test' });
expect(result.id).toBe('mock_123');
```

## Types reference

### [Resource]

```typescript
interface [Resource] {
  id: string;
  name: string;
  status: '[Resource]Status';
  created_at: string;
  updated_at: string;
  metadata: Record<string, string>;
}

type [Resource]Status = 'active' | 'inactive' | 'pending';
```

### Pagination

```typescript
interface Pagination {
  has_more: boolean;
  total?: number;
}

interface PaginatedResponse<T> {
  data: T[];
  pagination: Pagination;
}
```

## Migration guides

- [Migrating from v1 to v2](../how-to/sdk-migration-v2.md)

## Related

- [API Reference](./api.md)
- [Authentication](../how-to/authentication.md)
- [Error handling](../how-to/error-handling.md)
