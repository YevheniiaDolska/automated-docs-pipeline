---
title: "[Component] reference"
description: "[Component] [what it does in one sentence]. Supports [key capability] with [specific metric] throughput."
content_type: reference
product: both
tags:
  - Reference
  - API
---

# [Component] reference

The [Component] [what it does in one sentence]. Available in {{ product_name }} {{ current_version }}+.

## Quick example

```javascript
const component = new Component({
  required: "value",
  port: 8080,
  timeout: 30000
});

const result = await component.process(data);
// Returns: { success: true, processed: 1000, duration: 127 }
```

## Constructor

### `new Component(options)`

Creates a new [Component] instance.

```typescript
interface ComponentOptions {
  // Required
  required: string;        // Primary identifier

  // Connection settings
  host?: string;           // Default: "localhost"
  port?: number;           // Default: 8080, range: 1024-65535
  secure?: boolean;        // Default: false (true enables TLS)

  // Performance
  timeout?: number;        // Default: 30000ms, max: 300000ms
  maxConnections?: number; // Default: 100, max: 1000
  poolSize?: number;       // Default: 10, max: 100

  // Behavior
  retries?: number;        // Default: 3, max: 10
  retryDelay?: number;     // Default: 1000ms
  debug?: boolean;         // Default: false
}
```

### Parameter details

#### `required` (string, required)

The primary identifier for this component instance. Must be unique within your application.

- Format: Alphanumeric with hyphens, 3-63 characters
- Example: `"production-worker-1"`

#### `port` (number, optional)

TCP port for connections.

- Default: `8080`
- Range: `1024-65535`
- Common values: `8080` (HTTP), `443` (HTTPS), `5432` (PostgreSQL), `6379` (Redis)

#### `timeout` (number, optional)

Maximum time to wait for operations in milliseconds.

- Default: `30000` (30 seconds)
- Range: `100-300000` (0.1 second to 5 minutes)
- Recommended: `30000` for normal operations, `60000` for large payloads

#### `poolSize` (number, optional)

Number of concurrent connections to maintain.

- Default: `10`
- Range: `1-100`
- Formula: Set to `expected_concurrent_requests / 10`

## Methods

### `process(data, options?)`

Processes input data according to configuration.

**Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `data` | `any` | Yes | Input data to process |
| `options` | `ProcessOptions` | No | Override default settings |

**Options:**

```typescript
interface ProcessOptions {
  priority?: 'low' | 'normal' | 'high';  // Default: 'normal'
  timeout?: number;                       // Override instance timeout
  metadata?: Record<string, any>;        // Attach custom metadata
}
```

**Returns:** `Promise<ProcessResult>`

```typescript
interface ProcessResult {
  success: boolean;
  processed: number;      // Items processed
  failed: number;         // Items failed
  duration: number;       // Processing time in ms
  details: {
    throughput: number;   // Items per second
    errorRate: number;    // Percentage of failures
  };
}
```

**Example:**

```javascript
const result = await component.process(
  [/* array of 1000 items */],
  { priority: 'high', timeout: 60000 }
);

console.log(`Processed ${result.processed} items in ${result.duration}ms`);
console.log(`Throughput: ${result.details.throughput} items/sec`);
```

### `batch(items, batchSize?)`

Processes items in optimized batches.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `items` | `Array<any>` | — | Items to process |
| `batchSize` | `number` | `100` | Items per batch |

**Returns:** `Promise<BatchResult>`

**Example:**

```javascript
const results = await component.batch(largeArray, 500);
// Processes in batches of 500, optimizing memory usage
```

### `stream(source, options?)`

Processes data as a stream for memory efficiency.

**Parameters:**

```typescript
interface StreamOptions {
  highWaterMark?: number;  // Default: 16384 (16KB)
  encoding?: string;        // Default: 'utf8'
  transform?: Function;     // Custom transformation
}
```

**Example:**

```javascript
const stream = component.stream(fs.createReadStream('large-file.json'));

stream.on('data', (chunk) => {
  console.log(`Processed chunk: ${chunk.length} bytes`);
});

stream.on('end', () => {
  console.log('Stream processing complete');
});
```

### `healthCheck()`

Verifies component health and connectivity.

**Returns:** `Promise<HealthStatus>`

```typescript
interface HealthStatus {
  healthy: boolean;
  latency: number;        // Round-trip time in ms
  connections: {
    active: number;
    idle: number;
    max: number;
  };
  memory: {
    used: number;         // Bytes
    limit: number;        // Bytes
  };
}
```

**Example:**

```javascript
const health = await component.healthCheck();
if (!health.healthy) {
  console.error('Component unhealthy, restarting...');
  await component.restart();
}
```

## Events

The component extends EventEmitter and emits these events:

### `ready`

Emitted when the component is initialized and ready.

```javascript
component.on('ready', (info) => {
  console.log(`Component ready: ${info.id}`);
  console.log(`Listening on port: ${info.port}`);
});
```

### `error`

Emitted on errors. Always attach a handler to prevent crashes.

```javascript
component.on('error', (error) => {
  console.error(`Component error: ${error.code}`);

  if (error.code === 'ECONNREFUSED') {
    // Handle connection errors
  } else if (error.code === 'TIMEOUT') {
    // Handle timeout errors
  }
});
```

### `metrics`

Emitted periodically with performance metrics.

```javascript
component.on('metrics', (metrics) => {
  console.log(`Current throughput: ${metrics.throughput}/sec`);
  console.log(`Error rate: ${metrics.errorRate}%`);
  console.log(`P99 latency: ${metrics.latency.p99}ms`);
});
```

## Configuration examples

### High throughput configuration

```javascript
// Optimized for >10,000 requests/second
const highThroughput = new Component({
  required: "high-throughput",
  port: 8080,
  poolSize: 50,           // More connections
  maxConnections: 500,    // Higher limit
  timeout: 10000,         // Lower timeout
  retries: 1              // Fail fast
});
```

### High reliability configuration

```javascript
// Optimized for 99.99% uptime
const highReliability = new Component({
  required: "high-reliability",
  port: 8080,
  poolSize: 20,
  timeout: 60000,         // Generous timeout
  retries: 5,             // More retries
  retryDelay: 2000        // Exponential backoff
});
```

### Low latency configuration

```javascript
// Optimized for <10ms P99 latency
const lowLatency = new Component({
  required: "low-latency",
  port: 8080,
  poolSize: 100,          // Pre-warmed connections
  maxConnections: 200,
  timeout: 5000,          // Fail fast
  retries: 0              // No retries
});
```

## Error codes

| Code | Description | Common cause | Solution |
| --- | --- | --- | --- |
| `ECONNREFUSED` | Connection refused | Service not running | Start the service or check port |
| `TIMEOUT` | Operation timed out | Slow network/processing | Increase timeout or optimize |
| `POOL_EXHAUSTED` | No connections available | Too many concurrent requests | Increase poolSize |
| `INVALID_INPUT` | Input validation failed | Malformed data | Validate input before sending |
| `RATE_LIMITED` | Too many requests | Hitting rate limits | Implement backoff strategy |
| `AUTH_FAILED` | Authentication failed | Invalid credentials | Check API keys/tokens |

## Performance benchmarks

Tested on AWS t3.large (2 vCPU, 8GB RAM):

| Scenario | Configuration | Throughput | P50 Latency | P99 Latency | CPU | Memory |
| --- | --- | --- | --- | --- | --- | --- |
| Light load | Default | 100 req/s | 8ms | 15ms | 5% | 120MB |
| Normal load | Default | 1,000 req/s | 12ms | 45ms | 35% | 250MB |
| Heavy load | High throughput | 10,000 req/s | 25ms | 95ms | 75% | 1.2GB |
| Burst traffic | High reliability | 5,000 req/s | 30ms | 120ms | 60% | 800MB |

## Limits and quotas

| Resource | Default | Maximum | Notes |
| --- | --- | --- | --- |
| Connections | 100 | 1,000 | Per instance |
| Request size | 1MB | 100MB | Configurable |
| Response size | 10MB | 1GB | Streaming recommended for large |
| Requests/second | 1,000 | 50,000 | Depends on configuration |
| Timeout | 30s | 5 minutes | Per request |

## Migration guide

### From v1.x

```javascript
// Old (v1.x)
const old = new OldComponent();
old.configure({ port: 8080 });

// New (v2.x)
const component = new Component({
  required: "migration-test",  // Now required
  port: 8080
});
```

### From competitor product

```javascript
// Competitor
const other = competitor.create({
  url: "http://localhost:8080"
});

// This component (with compatibility mode)
const component = new Component({
  required: "migrated",
  host: "localhost",
  port: 8080,
  compatibility: "competitor-mode"  // Special flag
});
```

## Related resources

- [Getting started tutorial](../tutorials/component-tutorial.md) - 15-minute quickstart
- [Configuration guide](../how-to/configure-component.md) - Detailed setup
- [Architecture overview](../concepts/component-architecture.md) - How it works
- [Troubleshooting guide](../troubleshooting/component-issues.md) - Common problems
