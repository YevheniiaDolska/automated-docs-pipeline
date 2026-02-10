---
title: "Configuration reference"
description: "Complete configuration reference for [Product]. All environment variables, configuration files, and settings with defaults and examples."
content_type: reference
product: both
tags:
  - Reference
---

# Configuration reference

This reference covers all configuration options for [Product].

## Configuration methods

[Product] can be configured via:

1. **Environment variables** (recommended for secrets)
2. **Configuration file** (`[product].config.js` or `[product].yml`)
3. **Constructor options** (programmatic)

Priority: Constructor options > Environment variables > Config file > Defaults

## Environment variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `[PRODUCT]_API_KEY` | API key for authentication | `sk_live_abc123` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `[PRODUCT]_ENVIRONMENT` | `test` or `live` | `live` |
| `[PRODUCT]_API_URL` | Custom API URL | `https://api.[product].com` |
| `[PRODUCT]_TIMEOUT` | Request timeout (ms) | `30000` |
| `[PRODUCT]_MAX_RETRIES` | Max retry attempts | `3` |
| `[PRODUCT]_LOG_LEVEL` | Logging level | `warn` |

### Webhook configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `[PRODUCT]_WEBHOOK_SECRET` | Webhook signing secret | — |
| `[PRODUCT]_WEBHOOK_TOLERANCE` | Signature tolerance (seconds) | `300` |

### Advanced

| Variable | Description | Default |
|----------|-------------|---------|
| `[PRODUCT]_PROXY` | HTTP proxy URL | — |
| `[PRODUCT]_CA_CERT` | Custom CA certificate path | — |
| `[PRODUCT]_DISABLE_TELEMETRY` | Disable anonymous telemetry | `false` |

## Configuration file

### JavaScript/TypeScript

```javascript
// [product].config.js
module.exports = {
  apiKey: process.env.[PRODUCT]_API_KEY,
  environment: 'live',
  timeout: 30000,
  retries: {
    max: 3,
    initialDelay: 1000,
    maxDelay: 30000
  },
  logging: {
    level: 'info',
    format: 'json'
  },
  webhooks: {
    secret: process.env.[PRODUCT]_WEBHOOK_SECRET,
    tolerance: 300
  }
};
```

### YAML

```yaml
# [product].yml
apiKey: ${[PRODUCT]_API_KEY}
environment: live
timeout: 30000

retries:
  max: 3
  initialDelay: 1000
  maxDelay: 30000

logging:
  level: info
  format: json

webhooks:
  secret: ${[PRODUCT]_WEBHOOK_SECRET}
  tolerance: 300
```

### JSON

```json
{
  "apiKey": "${[PRODUCT]_API_KEY}",
  "environment": "live",
  "timeout": 30000,
  "retries": {
    "max": 3,
    "initialDelay": 1000,
    "maxDelay": 30000
  }
}
```

## Configuration options

### Core settings

#### `apiKey`

- **Type:** `string`
- **Required:** Yes
- **Environment:** `[PRODUCT]_API_KEY`

Your API key for authentication. Use test keys (`sk_test_`) in development and live keys (`sk_live_`) in production.

```javascript
// Never hardcode keys
apiKey: process.env.[PRODUCT]_API_KEY
```

#### `environment`

- **Type:** `'test' | 'live'`
- **Default:** `'live'`
- **Environment:** `[PRODUCT]_ENVIRONMENT`

The API environment to use.

| Environment | Use case | API URL |
|-------------|----------|---------|
| `test` | Development, testing | `https://api.test.[product].com` |
| `live` | Production | `https://api.[product].com` |

#### `baseUrl`

- **Type:** `string`
- **Default:** Based on environment
- **Environment:** `[PRODUCT]_API_URL`

Override the API base URL. Useful for proxies or custom deployments.

```javascript
baseUrl: 'https://api.custom.[product].com'
```

### Request settings

#### `timeout`

- **Type:** `number` (milliseconds)
- **Default:** `30000`
- **Environment:** `[PRODUCT]_TIMEOUT`

Request timeout in milliseconds. Requests exceeding this duration are aborted.

```javascript
timeout: 60000 // 60 seconds
```

#### `maxRetries`

- **Type:** `number`
- **Default:** `3`
- **Environment:** `[PRODUCT]_MAX_RETRIES`

Maximum number of retry attempts for failed requests. Set to `0` to disable retries.

#### `retries`

- **Type:** `object`

Fine-grained retry configuration:

```javascript
retries: {
  max: 3,                    // Max attempts
  initialDelay: 1000,        // First retry delay (ms)
  maxDelay: 30000,           // Max retry delay (ms)
  multiplier: 2,             // Backoff multiplier
  retryCondition: (error) => // Custom retry condition
    error.status >= 500 || error.status === 429
}
```

### Logging

#### `logging.level`

- **Type:** `'debug' | 'info' | 'warn' | 'error' | 'none'`
- **Default:** `'warn'`
- **Environment:** `[PRODUCT]_LOG_LEVEL`

Minimum log level to output.

#### `logging.format`

- **Type:** `'json' | 'pretty'`
- **Default:** `'json'` in production, `'pretty'` otherwise

Log output format.

#### `logging.logger`

- **Type:** `Logger`
- **Default:** Console logger

Custom logger instance:

```javascript
logging: {
  logger: winston.createLogger({ /* ... */ })
}
```

### Webhook settings

#### `webhooks.secret`

- **Type:** `string`
- **Environment:** `[PRODUCT]_WEBHOOK_SECRET`

Secret for verifying webhook signatures.

#### `webhooks.tolerance`

- **Type:** `number` (seconds)
- **Default:** `300`
- **Environment:** `[PRODUCT]_WEBHOOK_TOLERANCE`

Maximum age of webhook timestamp. Older webhooks are rejected (replay attack protection).

### Network settings

#### `proxy`

- **Type:** `string`
- **Environment:** `[PRODUCT]_PROXY`

HTTP proxy URL for all requests:

```javascript
proxy: 'http://proxy.example.com:8080'
```

#### `agent`

- **Type:** `http.Agent`

Custom HTTP agent for connection pooling:

```javascript
import https from 'https';

agent: new https.Agent({
  keepAlive: true,
  maxSockets: 50
})
```

#### `caCert`

- **Type:** `string | Buffer`
- **Environment:** `[PRODUCT]_CA_CERT`

Custom CA certificate for TLS verification.

### Telemetry

#### `telemetry`

- **Type:** `boolean`
- **Default:** `true`
- **Environment:** `[PRODUCT]_DISABLE_TELEMETRY=true`

Enable anonymous usage telemetry. Helps improve the SDK.

## Self-hosted configuration

For self-hosted [Product] deployments:

### Docker

```yaml
# docker-compose.yml
services:
  [product]:
    image: [product]/[product]:latest
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/[product]
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - [OTHER_VARS]
    ports:
      - "3000:3000"
```

### Kubernetes

```yaml
# configmap.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: [product]-config
data:
  DATABASE_URL: "postgres://db:5432/[product]"
  LOG_LEVEL: "info"
---
# secret.yml
apiVersion: v1
kind: Secret
metadata:
  name: [product]-secrets
type: Opaque
data:
  SECRET_KEY: <base64-encoded>
  API_KEY: <base64-encoded>
```

## Configuration validation

The SDK validates configuration on initialization:

```javascript
import { [Product]Client, ConfigError } from '[package]';

try {
  const client = new [Product]Client({
    // Invalid configuration
  });
} catch (error) {
  if (error instanceof ConfigError) {
    console.error('Invalid configuration:', error.message);
    console.error('Invalid fields:', error.fields);
  }
}
```

## Examples

### Minimal configuration

```javascript
const client = new [Product]Client({
  apiKey: process.env.[PRODUCT]_API_KEY
});
```

### Full configuration

```javascript
const client = new [Product]Client({
  apiKey: process.env.[PRODUCT]_API_KEY,
  environment: process.env.NODE_ENV === 'production' ? 'live' : 'test',
  timeout: 60000,
  retries: {
    max: 5,
    initialDelay: 500,
    maxDelay: 60000
  },
  logging: {
    level: process.env.NODE_ENV === 'production' ? 'warn' : 'debug',
    format: 'json'
  },
  webhooks: {
    secret: process.env.[PRODUCT]_WEBHOOK_SECRET,
    tolerance: 300
  }
});
```

## Related

- [Authentication](../how-to/authentication.md)
- [SDK Reference](./sdk.md)
- [Deployment guide](../how-to/deployment.md)
