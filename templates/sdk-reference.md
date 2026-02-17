---
title: "SDK reference"
description: "Reference for the official [Language] SDK: installation, client initialization, resources, errors, pagination, retries, and versioning."
content_type: reference
product: both
tags:
  - Reference
  - API
---

# SDK reference

This page documents the exact behavior of the [Language] SDK.

## Package information

| Field | Value |
| --- | --- |
| Package | `[package-name]` |
| Current version | `[x.y.z]` |
| Runtime requirement | `[for example: Node.js 18+]` |
| Source repository | `[link]` |

## Installation

```bash
npm install [package-name]
```

## Initialize client

```javascript
import { ProductClient } from '[package-name]';

const client = new ProductClient({
  apiKey: process.env.PRODUCT_API_KEY,
  baseUrl: 'https://api.example.com',
  timeout: 30000,
  maxRetries: 3
});
```

## Client options

| Option | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `apiKey` | `string` | Yes* | - | API key for server auth |
| `accessToken` | `string` | Yes* | - | OAuth token alternative |
| `baseUrl` | `string` | No | SDK default | Custom endpoint |
| `timeout` | `number` | No | `30000` | Request timeout in ms |
| `maxRetries` | `number` | No | `3` | Retry attempts for transient failures |

`*` Provide either `apiKey` or `accessToken`.

## Resource namespaces

### `client.projects`

- `create(params)`
- `get(id)`
- `list(params)`
- `update(id, params)`
- `delete(id)`

### `client.runs`

- `create(params)`
- `get(id)`
- `cancel(id)`

## Pagination pattern

```javascript
let cursor;
do {
  const page = await client.projects.list({ limit: 100, cursor });
  for (const item of page.data) {
    handle(item);
  }
  cursor = page.nextCursor;
} while (cursor);
```

## Error model

```javascript
try {
  await client.projects.create({ name: '' });
} catch (err) {
  console.error(err.type, err.code, err.requestId);
}
```

| Field | Description |
| --- | --- |
| `type` | Error class (`validation_error`, `auth_error`, `rate_limit`) |
| `code` | Stable machine-readable error code |
| `requestId` | Request identifier for support |

## Retries and idempotency

- SDK retries transient errors only.
- For write operations, pass idempotency key when supported.

## Versioning and compatibility

Document:

- Supported API versions
- Breaking changes by SDK major version
- Migration link for deprecated methods

## Related docs

- `templates/error-handling-guide.md`
- `templates/integration-guide.md`
