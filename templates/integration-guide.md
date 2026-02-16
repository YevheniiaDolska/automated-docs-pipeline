---
title: "[Product] integration guide"
description: "Complete guide to integrating [Product] into your [application/platform]. Covers authentication, API calls, webhooks, and production deployment."
content_type: how-to
product: both
tags:

  - How-To
  - Tutorial

---

## [Product] integration guide

This guide walks you through integrating [Product] into your [application type]. You'll learn authentication, making API requests, handling webhooks, and deploying to production.

**Time required:** [30-60] minutes

## Integration overview

```mermaid
sequenceDiagram
    participant App as Your App
    participant API as [Product] API
    participant WH as Webhooks

    App->>API: 1. Authenticate
    API-->>App: Access token
    App->>API: 2. API requests
    API-->>App: Responses
    API->>WH: 3. Events occur
    WH->>App: Webhook notifications

```text

## Prerequisites

Before you begin:

- [ ] [Product] account ([sign up]([URL]))
- [ ] API credentials ([get them]([URL]))
- [ ] Development environment with [language/framework]
- [ ] Basic knowledge of [REST APIs/GraphQL/etc.]

## Step 1: Set up authentication

[Product] uses [authentication method] for API access.

### Get your credentials

1. Go to [Dashboard]([URL]) → Settings → API Keys
1. Create a new API key with these permissions:
   - [Permission 1]
   - [Permission 2]
1. Copy both the **Client ID** and **Client Secret**

### Configure authentication

=== "Environment variables (recommended)"

    ```bash
    export [PRODUCT]_CLIENT_ID="your-client-id"
    export [PRODUCT]_CLIENT_SECRET="your-client-secret"
```

=== "Configuration file"

    ```yaml
    # config/[product].yml
    client_id: ${[PRODUCT]_CLIENT_ID}
    client_secret: ${[PRODUCT]_CLIENT_SECRET}

```text

!!! danger "Security warning"
    Never hardcode credentials in source code. Always use environment variables or a secrets manager.

### Obtain access token

=== "OAuth 2.0 Client Credentials"

    ```javascript
    const getAccessToken = async () => {
      const response = await fetch('[AUTH_URL]/oauth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
          grant_type: 'client_credentials',
          client_id: process.env.[PRODUCT]_CLIENT_ID,
          client_secret: process.env.[PRODUCT]_CLIENT_SECRET
        })
      });

      const { access_token, expires_in } = await response.json();
      return access_token;
    };
```

=== "API Key"

    ```javascript
    // Include in every request header
    const headers = {
      'Authorization': `Bearer ${process.env.[PRODUCT]_API_KEY}`,
      'Content-Type': 'application/json'
    };

```text

## Step 2: Install the SDK (optional)

Using the official SDK simplifies integration:

=== "JavaScript/Node.js"

    ```bash
    npm install @[product]/sdk
```

    ```javascript
    import { [Product]Client } from '@[product]/sdk';

    const client = new [Product]Client({
      clientId: process.env.[PRODUCT]_CLIENT_ID,
      clientSecret: process.env.[PRODUCT]_CLIENT_SECRET
    });

```text

=== "Python"

    ```bash
    pip install [product]-sdk
```

    ```python
    from [product] import Client

    client = Client(
        client_id=os.environ['[PRODUCT]_CLIENT_ID'],
        client_secret=os.environ['[PRODUCT]_CLIENT_SECRET']
    )

```text

=== "REST API (no SDK)"

    You can use the REST API directly with any HTTP client.

## Step 3: Make your first API call

### Create a [resource]

=== "SDK"

    ```javascript
    const [resource] = await client.[resources].create({
      name: 'My first [resource]',
      [field]: '[value]'
    });

    console.log('[Resource] created:', [resource].id);
```

=== "REST API"

    ```bash
    curl -X POST [API_URL]/v1/[resources] \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "My first [resource]",
        "[field]": "[value]"
      }'

```text

### List [resources]

```javascript
const [resources] = await client.[resources].list({
  limit: 20,
  status: 'active'
});

for (const [resource] of [resources].data) {
  console.log([resource].name);
}
```

### Get a single [resource]

```javascript
const [resource] = await client.[resources].get('[resource_id]');

```text

### Update a [resource]

```javascript
const updated = await client.[resources].update('[resource_id]', {
  name: 'Updated name'
});
```

### Delete a [resource]

```javascript
await client.[resources].delete('[resource_id]');

```text

## Step 4: Handle responses and errors

### Success responses

```javascript
try {
  const result = await client.[resources].create({ ... });

  // Access response data
  console.log('ID:', result.id);
  console.log('Created at:', result.created_at);

} catch (error) {
  // Handle errors (see below)
}
```

### Error handling

```javascript
import { [Product]Error, ValidationError, AuthError } from '@[product]/sdk';

try {
  const result = await client.[resources].create({ ... });
} catch (error) {
  if (error instanceof ValidationError) {
    // Invalid request data
    console.error('Validation failed:', error.details);
  } else if (error instanceof AuthError) {
    // Authentication failed
    console.error('Auth error:', error.message);
    // Refresh token and retry
  } else if (error instanceof [Product]Error) {
    // Other API error
    console.error(`Error ${error.code}: ${error.message}`);
  } else {
    // Network or unexpected error
    throw error;
  }
}

```text

### Implement retry logic

```javascript
const withRetry = async (fn, maxRetries = 3) => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429 || error.status >= 500) {
        if (attempt === maxRetries) throw error;

        const delay = Math.pow(2, attempt) * 1000;
        await new Promise(r => setTimeout(r, delay));
      } else {
        throw error;
      }
    }
  }
};

// Usage
const result = await withRetry(() =>
  client.[resources].create({ ... })
);
```

## Step 5: Set up webhooks

Webhooks notify your application of events in real-time.

### Create a webhook endpoint

```javascript
// Express.js example
app.post('/webhooks/[product]', express.raw({ type: 'application/json' }), (req, res) => {
  const signature = req.headers['x-[product]-signature'];

  // Verify signature (important!)
  if (!verifySignature(req.body, signature)) {
    return res.status(401).send('Invalid signature');
  }

  const event = JSON.parse(req.body);

  // Handle event
  switch (event.type) {
    case '[resource].created':
      handle[Resource]Created(event.data);
      break;
    case '[resource].updated':
      handle[Resource]Updated(event.data);
      break;
    default:
      console.log('Unhandled event:', event.type);
  }

  res.status(200).send('OK');
});

```text

### Verify webhook signatures

```javascript
import crypto from 'crypto';

const verifySignature = (payload, signature) => {
  const expected = crypto
    .createHmac('sha256', process.env.[PRODUCT]_WEBHOOK_SECRET)
    .update(payload)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
};
```

### Register your webhook

=== "Dashboard"

    1. Go to [Dashboard]([URL]) → Webhooks
    1. Click "Add endpoint"
    1. Enter your URL: `<https://yourapp.com/webhooks/[product]`>
    1. Select events to subscribe to
    1. Save

=== "API"

    ```javascript
    await client.webhooks.create({
      url: '<https://yourapp.com/webhooks/[product]',>
      events: ['[resource].created', '[resource].updated'],
      secret: 'your-webhook-secret'
    });

```text

## Step 6: Test your integration

### Use test mode

[Product] provides a test environment:

```javascript
const client = new [Product]Client({
  // ... credentials
  environment: 'sandbox' // or 'test'
});
```

Test credentials: Use keys starting with `test_` or `sk_test_`.

### Test scenarios

Verify these scenarios work:

- [ ] Authentication succeeds
- [ ] Create [resource] returns expected response
- [ ] List [resources] with pagination works
- [ ] Error handling catches validation errors
- [ ] Webhook signature verification works
- [ ] Retry logic handles rate limits

### Local webhook testing

Use [ngrok](https://ngrok.com) to test webhooks locally:

```bash
ngrok http 3000
## Use the generated URL as your webhook endpoint

```text

## Step 7: Go to production

### Production checklist

- [ ] **Credentials:** Switch from test to production API keys
- [ ] **Environment:** Set `environment: 'production'` in SDK
- [ ] **Error handling:** All errors are caught and logged
- [ ] **Retries:** Implemented for transient failures
- [ ] **Webhooks:** Signature verification enabled
- [ ] **Logging:** Request/response logging for debugging
- [ ] **Monitoring:** Alerts for error rates and latency
- [ ] **Rate limits:** Implemented backoff for 429 errors

### Environment configuration

```javascript
// config.js
export const config = {
  [product]: {
    clientId: process.env.[PRODUCT]_CLIENT_ID,
    clientSecret: process.env.[PRODUCT]_CLIENT_SECRET,
    environment: process.env.NODE_ENV === 'production'
      ? 'production'
      : 'sandbox',
    webhookSecret: process.env.[PRODUCT]_WEBHOOK_SECRET
  }
};
```

### Monitoring recommendations

Monitor these metrics:

| Metric | Alert threshold |
| -------- | ----------------- |
| API error rate | > 1% |
| API latency (p95) | > 2s |
| Webhook delivery failures | > 5 consecutive |
| Authentication failures | Any |

## Complete example

Here's a full working integration:

```javascript
// [product]-integration.js
import { [Product]Client } from '@[product]/sdk';
import express from 'express';

// Initialize client
const client = new [Product]Client({
  clientId: process.env.[PRODUCT]_CLIENT_ID,
  clientSecret: process.env.[PRODUCT]_CLIENT_SECRET,
  environment: process.env.NODE_ENV === 'production' ? 'production' : 'sandbox'
});

// API operations
export const create[Resource] = async (data) => {
  try {
    return await client.[resources].create(data);
  } catch (error) {
    console.error('Failed to create [resource]:', error);
    throw error;
  }
};

// Webhook handler
export const setupWebhooks = (app) => {
  app.post('/webhooks/[product]', express.raw({ type: 'application/json' }), async (req, res) => {
    // Verify and process webhook
    // ... (see Step 5)
    res.status(200).send('OK');
  });
};

```text

## Troubleshooting

### Authentication errors

**Error:** `401 Unauthorized`

**Causes:**

- Invalid or expired credentials
- Wrong environment (test vs. production)
- Missing required scopes

**Fix:** Verify credentials and regenerate if needed.

### Rate limiting

**Error:** `429 Too Many Requests`

**Fix:** Implement exponential backoff (see Step 4).

### Webhook not received

**Causes:**

- Incorrect URL
- Firewall blocking requests
- SSL certificate issues

**Fix:** Verify URL accessibility and check [webhook logs]([URL]).

## Related resources

- [API Reference](../reference/api.md)
- [Authentication guide](./authentication.md)
- [Webhooks reference](../reference/webhooks.md)
- [Error codes](../reference/errors.md)
- [Rate limits](../reference/rate-limits.md)
