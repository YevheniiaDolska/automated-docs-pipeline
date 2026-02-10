---
title: "Testing guide"
description: "Test your [Product] integration effectively. Covers test environments, mocking, unit tests, integration tests, and end-to-end testing strategies."
content_type: how-to
product: both
tags:
  - How-To
---

# Testing guide

This guide covers testing strategies for [Product] integrations, from unit tests to end-to-end testing in production-like environments.

## Test environments

### Sandbox vs. Production

| Environment | Use | API Keys | Data |
|-------------|-----|----------|------|
| **Sandbox** | Development, testing | `sk_test_*` | Test data, no real effects |
| **Production** | Live application | `sk_live_*` | Real data, real effects |

### Configure test environment

```javascript
// Use test keys for testing
const client = new [Product]Client({
  apiKey: process.env.[PRODUCT]_TEST_API_KEY,
  environment: 'test'
});
```

### Test data

The sandbox provides test data for common scenarios:

| Test input | Behavior |
|------------|----------|
| `test_success_*` | Simulates successful operations |
| `test_fail_*` | Simulates failures |
| `test_slow_*` | Simulates slow responses |

## Unit testing

### Mock the SDK

```javascript
// __mocks__/[product].js
export const Mock[Product]Client = {
  [resources]: {
    create: jest.fn(),
    get: jest.fn(),
    list: jest.fn(),
    update: jest.fn(),
    delete: jest.fn()
  }
};

// test/[resource].test.js
import { Mock[Product]Client } from '../__mocks__/[product]';
import { create[Resource] } from '../src/[resource]';

jest.mock('[product]-sdk', () => ({
  [Product]Client: jest.fn(() => Mock[Product]Client)
}));

describe('create[Resource]', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('creates a [resource] successfully', async () => {
    Mock[Product]Client.[resources].create.mockResolvedValue({
      id: 'res_123',
      name: 'Test',
      status: 'active'
    });

    const result = await create[Resource]({ name: 'Test' });

    expect(result.id).toBe('res_123');
    expect(Mock[Product]Client.[resources].create).toHaveBeenCalledWith({
      name: 'Test'
    });
  });

  it('handles validation errors', async () => {
    Mock[Product]Client.[resources].create.mockRejectedValue({
      type: 'validation_error',
      code: 'invalid_parameter',
      param: 'name',
      message: 'Name is required'
    });

    await expect(create[Resource]({}))
      .rejects
      .toThrow('Name is required');
  });

  it('handles rate limiting', async () => {
    Mock[Product]Client.[resources].create
      .mockRejectedValueOnce({ status: 429 })
      .mockResolvedValueOnce({ id: 'res_123' });

    const result = await create[Resource]({ name: 'Test' });

    expect(result.id).toBe('res_123');
    expect(Mock[Product]Client.[resources].create).toHaveBeenCalledTimes(2);
  });
});
```

### Test error handling

```javascript
describe('error handling', () => {
  it('handles authentication errors', async () => {
    Mock[Product]Client.[resources].get.mockRejectedValue({
      type: 'authentication_error',
      code: 'invalid_api_key'
    });

    await expect(get[Resource]('res_123'))
      .rejects
      .toMatchObject({ type: 'authentication_error' });
  });

  it('handles not found errors', async () => {
    Mock[Product]Client.[resources].get.mockRejectedValue({
      type: 'not_found_error',
      code: 'resource_not_found'
    });

    const result = await get[Resource]OrNull('res_123');
    expect(result).toBeNull();
  });

  it('retries on server errors', async () => {
    Mock[Product]Client.[resources].create
      .mockRejectedValueOnce({ status: 500 })
      .mockRejectedValueOnce({ status: 500 })
      .mockResolvedValueOnce({ id: 'res_123' });

    const result = await create[Resource]WithRetry({ name: 'Test' });

    expect(result.id).toBe('res_123');
    expect(Mock[Product]Client.[resources].create).toHaveBeenCalledTimes(3);
  });
});
```

## Integration testing

### Test against sandbox

```javascript
// integration/[resource].integration.test.js
import { [Product]Client } from '[product]-sdk';

describe('[Resource] integration', () => {
  let client;

  beforeAll(() => {
    client = new [Product]Client({
      apiKey: process.env.[PRODUCT]_TEST_API_KEY,
      environment: 'test'
    });
  });

  it('creates and retrieves a [resource]', async () => {
    // Create
    const created = await client.[resources].create({
      name: 'Integration Test'
    });
    expect(created.id).toBeDefined();

    // Retrieve
    const retrieved = await client.[resources].get(created.id);
    expect(retrieved.name).toBe('Integration Test');

    // Cleanup
    await client.[resources].delete(created.id);
  });

  it('handles pagination', async () => {
    // Create multiple resources
    const ids = [];
    for (let i = 0; i < 5; i++) {
      const res = await client.[resources].create({ name: `Test ${i}` });
      ids.push(res.id);
    }

    // List with pagination
    const { data, pagination } = await client.[resources].list({ limit: 2 });
    expect(data.length).toBe(2);
    expect(pagination.has_more).toBe(true);

    // Cleanup
    for (const id of ids) {
      await client.[resources].delete(id);
    }
  });
});
```

### Test webhooks

```javascript
// integration/webhook.integration.test.js
import express from 'express';
import { verifyWebhookSignature } from '[product]-sdk';

describe('Webhook integration', () => {
  let server;
  let receivedEvents = [];

  beforeAll((done) => {
    const app = express();
    app.post('/webhooks', express.raw({ type: 'application/json' }), (req, res) => {
      const isValid = verifyWebhookSignature(
        req.body,
        req.headers['x-[product]-signature'],
        process.env.[PRODUCT]_WEBHOOK_SECRET
      );

      if (!isValid) {
        return res.status(401).send('Invalid signature');
      }

      receivedEvents.push(JSON.parse(req.body));
      res.sendStatus(200);
    });

    server = app.listen(3001, done);
  });

  afterAll((done) => {
    server.close(done);
  });

  beforeEach(() => {
    receivedEvents = [];
  });

  it('receives webhook events', async () => {
    // Trigger an action that sends a webhook
    await client.[resources].create({
      name: 'Webhook Test',
      webhookUrl: 'http://localhost:3001/webhooks'
    });

    // Wait for webhook
    await waitFor(() => receivedEvents.length > 0, { timeout: 10000 });

    expect(receivedEvents[0].type).toBe('[resource].created');
  });
});
```

## End-to-end testing

### Full flow testing

```javascript
// e2e/[use-case].e2e.test.js
describe('[Use case] E2E', () => {
  it('completes full workflow', async () => {
    // Step 1: Create initial resource
    const resource = await client.[resources].create({
      name: 'E2E Test'
    });

    // Step 2: Trigger processing
    await client.[resources].process(resource.id);

    // Step 3: Wait for completion
    const completed = await pollUntilComplete(resource.id);
    expect(completed.status).toBe('completed');

    // Step 4: Verify results
    const results = await client.[resources].getResults(resource.id);
    expect(results.data).toBeDefined();
  });
});

// Helper function
const pollUntilComplete = async (id, timeout = 60000) => {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const resource = await client.[resources].get(id);

    if (resource.status === 'completed') {
      return resource;
    }

    if (resource.status === 'failed') {
      throw new Error(`Resource failed: ${resource.error}`);
    }

    await sleep(1000);
  }

  throw new Error('Timeout waiting for completion');
};
```

## Testing webhooks locally

### Using ngrok

```bash
# Start your local server
npm run dev

# In another terminal, expose it
ngrok http 3000

# Use the ngrok URL as webhook endpoint
# https://abc123.ngrok.io/webhooks
```

### Using the CLI

```bash
# Trigger test webhook
[product] webhooks trigger \
  --event [resource].created \
  --endpoint http://localhost:3000/webhooks
```

### Mock webhook server

```javascript
// test/helpers/mockWebhookServer.js
import express from 'express';
import crypto from 'crypto';

export const createMockWebhookServer = (secret) => {
  const app = express();
  const events = [];

  app.post('/webhooks', express.json(), (req, res) => {
    events.push(req.body);
    res.sendStatus(200);
  });

  return {
    app,
    getEvents: () => events,
    clearEvents: () => events.length = 0,
    sendEvent: async (url, event) => {
      const payload = JSON.stringify(event);
      const timestamp = Math.floor(Date.now() / 1000);
      const signature = crypto
        .createHmac('sha256', secret)
        .update(`${timestamp}.${payload}`)
        .digest('hex');

      await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-[product]-signature': `t=${timestamp},v1=${signature}`
        },
        body: payload
      });
    }
  };
};
```

## Test fixtures

### Create test data

```javascript
// test/fixtures/[resources].js
export const valid[Resource] = {
  name: 'Test Resource',
  status: 'active',
  config: {
    option1: 'value1'
  }
};

export const invalid[Resource] = {
  // Missing required 'name' field
  status: 'active'
};

export const [resource]List = [
  { id: 'res_1', name: 'Resource 1' },
  { id: 'res_2', name: 'Resource 2' },
  { id: 'res_3', name: 'Resource 3' }
];
```

### Factory functions

```javascript
// test/factories/[resource].factory.js
let counter = 0;

export const build[Resource] = (overrides = {}) => ({
  id: `res_${++counter}`,
  name: `Test Resource ${counter}`,
  status: 'active',
  created_at: new Date().toISOString(),
  ...overrides
});

export const build[Resource]List = (count, overrides = {}) =>
  Array.from({ length: count }, () => build[Resource](overrides));
```

## CI/CD testing

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm test

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run test:integration
        env:
          [PRODUCT]_TEST_API_KEY: ${{ secrets.[PRODUCT]_TEST_API_KEY }}
          [PRODUCT]_WEBHOOK_SECRET: ${{ secrets.[PRODUCT]_WEBHOOK_SECRET }}
```

## Best practices

### Test isolation

- Each test should be independent
- Clean up created resources
- Use unique identifiers

### Test coverage

| Area | Coverage goal |
|------|--------------|
| API operations | 100% |
| Error handling | 100% |
| Webhook processing | 100% |
| Edge cases | High priority scenarios |

### Performance testing

```javascript
describe('performance', () => {
  it('handles high volume', async () => {
    const start = Date.now();
    const promises = [];

    for (let i = 0; i < 100; i++) {
      promises.push(client.[resources].create({ name: `Perf ${i}` }));
    }

    await Promise.all(promises);

    const duration = Date.now() - start;
    expect(duration).toBeLessThan(30000); // 30 seconds
  });
});
```

## Related

- [Best practices](./best-practices.md)
- [Error handling](./error-handling.md)
- [SDK reference](../reference/sdk.md)
