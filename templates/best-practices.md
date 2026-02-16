---
title: "[Product] best practices"
description: "Best practices for building reliable, secure, and performant integrations with [Product]. Covers architecture, security, error handling, and optimization."
content_type: concept
product: both
tags:

  - Concept
  - How-To

---

## Best practices

This guide covers best practices for building production-ready integrations with [Product]. Follow these recommendations to create reliable, secure, and maintainable applications.

## Architecture

### Use a wrapper/service layer

Don't call the API directly from your business logic. Create a service layer:

```javascript
// Good: Service layer
class [Product]Service {
  constructor(apiClient) {
    this.client = apiClient;
  }

  async create[Resource](data) {
    const validated = this.validate(data);
    const result = await this.client.[resources].create(validated);
    return this.transform(result);
  }

  validate(data) { /* ... */ }
  transform(result) { /* ... */ }
}

// Usage
const service = new [Product]Service(apiClient);
await service.create[Resource](userData);
```

```javascript
// Bad: Direct API calls scattered in code
await apiClient.[resources].create(data);  // In controller
await apiClient.[resources].create(data);  // In another file
```

### Separate configuration

Keep configuration separate from code:

```javascript
// config/[product].js
export const config = {
  apiKey: process.env.[PRODUCT]_API_KEY,
  environment: process.env.NODE_ENV === 'production' ? 'live' : 'test',
  timeout: 30000,
  retries: 3
};

// Usage
import { config } from './config/[product]';
const client = new [Product]Client(config);
```

### Use dependency injection

Make your code testable:

```javascript
// Good: Dependency injection
class OrderService {
  constructor([product]Service) {
    this.[product] = [product]Service;
  }

  async createOrder(data) {
    return this.[product].create[Resource](data);
  }
}

// Easy to test with mocks
const mockService = { create[Resource]: jest.fn() };
const orderService = new OrderService(mockService);
```

## Security

### Credential management

| Do | Don't |
| ---- | ------- |
| Use environment variables | Hardcode credentials |
| Use secrets managers (Vault, AWS Secrets) | Commit credentials to git |
| Rotate keys regularly | Share keys across environments |
| Use minimum required permissions | Use admin keys everywhere |

```javascript
// Good
const apiKey = process.env.[PRODUCT]_API_KEY;

// Bad
const apiKey = 'sk_live_abc123'; // Never do this
```

### Input validation

Validate all input before sending to the API:

```javascript
import Joi from 'joi';

const [resource]Schema = Joi.object({
  name: Joi.string().min(1).max(255).required(),
  email: Joi.string().email().required(),
  amount: Joi.number().positive().max(1000000)
});

const create[Resource] = async (input) => {
  // Validate first
  const { error, value } = [resource]Schema.validate(input);
  if (error) {
    throw new ValidationError(error.details);
  }

  return apiClient.[resources].create(value);
};
```

### Webhook security

Always verify webhook signatures:

```javascript
// Good: Verify signature
app.post('/webhooks', (req, res) => {
  if (!verifySignature(req.body, req.headers['x-signature'])) {
    return res.status(401).send('Invalid signature');
  }
  // Process webhook
});

// Bad: No verification
app.post('/webhooks', (req, res) => {
  processWebhook(req.body); // Dangerous!
});
```

### Rate limit your own endpoints

Protect your webhook endpoints from abuse:

```javascript
import rateLimit from 'express-rate-limit';

const webhookLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100 // 100 requests per minute
});

app.post('/webhooks', webhookLimiter, webhookHandler);
```

## Error handling

### Always handle errors

Never let API errors crash your application:

```javascript
// Good: Comprehensive error handling
try {
  const result = await apiClient.[resources].create(data);
  return result;
} catch (error) {
  if (error.type === 'validation_error') {
    throw new UserError(error.message);
  }
  if (error.type === 'rate_limit_error') {
    await scheduleRetry(data);
    return { status: 'pending' };
  }
  logger.error('API error', { error, requestId: error.requestId });
  throw new SystemError('Service temporarily unavailable');
}

// Bad: No error handling
const result = await apiClient.[resources].create(data);
```

### Implement retries

Retry transient failures with exponential backoff:

```javascript
const withRetry = async (fn, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (!isRetryable(error) || i === maxRetries - 1) throw error;
      await sleep(Math.pow(2, i) * 1000);
    }
  }
};

const isRetryable = (error) =>
  [429, 500, 502, 503, 504].includes(error.status);
```

### Log with context

Include relevant context in error logs:

```javascript
// Good: Contextual logging
logger.error('Failed to create [resource]', {
  requestId: error.requestId,
  userId: user.id,
  input: sanitize(data), // Remove sensitive fields
  errorType: error.type,
  errorCode: error.code
});

// Bad: Minimal logging
console.log('Error:', error.message);
```

## Performance

### Use pagination

Don't fetch all records at once:

```javascript
// Good: Paginate results
const fetchAll[Resources] = async () => {
  const all = [];
  let hasMore = true;
  let cursor = null;

  while (hasMore) {
    const { data, pagination } = await apiClient.[resources].list({
      limit: 100,
      starting_after: cursor
    });
    all.push(...data);
    hasMore = pagination.has_more;
    cursor = data[data.length - 1]?.id;
  }

  return all;
};

// Bad: Single large request
const all = await apiClient.[resources].list({ limit: 10000 });
```

### Cache when appropriate

Cache stable data to reduce API calls:

```javascript
import NodeCache from 'node-cache';

const cache = new NodeCache({ stdTTL: 300 }); // 5 minutes

const get[Resource] = async (id) => {
  const cached = cache.get(id);
  if (cached) return cached;

  const [resource] = await apiClient.[resources].get(id);
  cache.set(id, [resource]);
  return [resource];
};
```

### Batch operations

Use batch endpoints when available:

```javascript
// Good: Batch create
await apiClient.[resources].createMany([
  { name: 'Resource 1' },
  { name: 'Resource 2' },
  { name: 'Resource 3' }
]);

// Bad: Individual creates
for (const data of items) {
  await apiClient.[resources].create(data); // N API calls
}
```

### Use webhooks instead of polling

```javascript
// Good: React to webhooks
app.post('/webhooks', (req, res) => {
  const event = req.body;
  if (event.type === '[resource].updated') {
    updateLocal[Resource](event.data);
  }
  res.sendStatus(200);
});

// Bad: Poll for changes
setInterval(async () => {
  const [resources] = await apiClient.[resources].list();
  syncLocal[Resources]([resources]);
}, 60000);
```

## Testing

### Use test/sandbox environment

Never test against production:

```javascript
// Good: Use test environment
const client = new [Product]Client({
  apiKey: process.env.[PRODUCT]_TEST_API_KEY,
  environment: 'test'
});

// Bad: Test against production
const client = new [Product]Client({
  apiKey: process.env.[PRODUCT]_LIVE_API_KEY // Dangerous!
});
```

### Mock API calls in unit tests

```javascript
// Jest mock
jest.mock('@[product]/sdk', () => ({
  [Product]Client: jest.fn().mockImplementation(() => ({
    [resources]: {
      create: jest.fn().mockResolvedValue({ id: 'mock_123' }),
      get: jest.fn().mockResolvedValue({ id: 'mock_123', name: 'Test' })
    }
  }))
}));

test('creates [resource]', async () => {
  const result = await service.create[Resource]({ name: 'Test' });
  expect(result.id).toBe('mock_123');
});
```

### Test error scenarios

```javascript
test('handles rate limiting', async () => {
  apiClient.[resources].create.mockRejectedValue({
    status: 429,
    type: 'rate_limit_error'
  });

  await expect(service.create[Resource]({}))
    .rejects.toThrow('Rate limited');
});
```

## Monitoring

### Track key metrics

| Metric | Why |
| -------- | ----- |
| API response time | Detect slowdowns |
| Error rate | Identify issues |
| Rate limit usage | Prevent throttling |
| Webhook processing time | Ensure timely handling |

### Set up alerts

```javascript
// Example: Alert on high error rate
const metrics = {
  requests: 0,
  errors: 0
};

const trackRequest = (success) => {
  metrics.requests++;
  if (!success) metrics.errors++;

  const errorRate = metrics.errors / metrics.requests;
  if (errorRate > 0.05 && metrics.requests > 100) {
    alertOps('High [Product] API error rate', { errorRate });
  }
};
```

### Include request IDs in logs

```javascript
const makeRequest = async (method, data) => {
  try {
    const result = await apiClient[method](data);
    logger.info('[Product] request succeeded', {
      method,
      requestId: result._requestId
    });
    return result;
  } catch (error) {
    logger.error('[Product] request failed', {
      method,
      requestId: error.requestId, // Critical for debugging
      error: error.message
    });
    throw error;
  }
};
```

## Checklist

### Before going live

- [ ] Using production API keys (not test)
- [ ] Credentials in environment variables
- [ ] Error handling for all API calls
- [ ] Retry logic for transient failures
- [ ] Rate limiting respected
- [ ] Webhook signatures verified
- [ ] Input validation implemented
- [ ] Logging with request IDs
- [ ] Monitoring and alerts set up
- [ ] Tested with real data volume

## Related

- [Integration guide](./integration-guide.md)
- [Error handling](./error-handling.md)
- [Security guide](./security.md)
- [Performance optimization](./performance.md)
