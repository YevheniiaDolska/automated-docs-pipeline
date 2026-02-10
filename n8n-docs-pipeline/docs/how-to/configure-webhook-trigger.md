---
title: "Configure Webhook trigger authentication in n8n"
description: "Set up HMAC signature verification, basic auth, or header-based authentication for n8n Webhook trigger nodes to secure incoming requests."
content_type: how-to
product: both
n8n_component: webhook
tags:
  - How-To
  - Webhook
  - Cloud
  - Self-hosted
---

# Configure Webhook trigger authentication in n8n

The n8n Webhook node accepts incoming HTTP requests to trigger workflow execution. By default, the Webhook endpoint is open to any request. To prevent unauthorized access, configure one of the authentication methods described in this guide.

## Prerequisites

- A workflow with a Webhook trigger node. See [Build your first workflow](../getting-started/quickstart.md) if you need one.
- The Webhook node must be in **Listening** state (Test or Production mode).

## Option 1: Header-based authentication

Header authentication checks for a specific key-value pair in the request headers. This is the simplest approach and works with most webhook senders.

1. Open the Webhook node settings.
2. Set **Authentication** to **Header Auth**.
3. Create a **Header Auth credential** with:
    - **Name**: `X-API-Key` (or any custom header name)
    - **Value**: a strong random string (minimum 32 characters)
4. Save the workflow.

Requests without the correct header receive a `403 Forbidden` response.

```bash
# Authenticated request
curl -X POST https://your-instance.n8n.cloud/webhook/abc123 \
  -H "X-API-Key: your-secret-value" \
  -H "Content-Type: application/json" \
  -d '{"event": "order.created"}'
```

## Option 2: Basic authentication

Basic authentication uses a username and password encoded in the `Authorization` header. Use this when the sending service supports HTTP Basic Auth.

1. Open the Webhook node settings.
2. Set **Authentication** to **Basic Auth**.
3. Create a **Basic Auth credential** with a username and password.
4. Save the workflow.

## Option 3: HMAC signature verification

HMAC (Hash-based Message Authentication Code) verification is the most secure option. The sending service signs each request body with a shared secret, and n8n verifies the signature matches. Services like GitHub, Stripe, and Shopify use HMAC webhooks.

!!! warning "n8n version requirement"
    HMAC verification in the Webhook node requires n8n version 1.40.0 or later. For earlier versions, use a Code node after the Webhook to verify manually.

1. Open the Webhook node settings.
2. Set **Authentication** to **None** (HMAC is verified in a subsequent node).
3. Add a **Code node** after the Webhook node with the following JavaScript:

```javascript
const crypto = require('crypto');

const secret = 'your-shared-secret';
const signature = $input.first().headers['x-hub-signature-256'];
const body = JSON.stringify($input.first().json);

const expected = 'sha256=' + crypto
  .createHmac('sha256', secret)
  .update(body)
  .digest('hex');

if (signature !== expected) {
  throw new Error('Invalid HMAC signature');
}

return $input.all();
```

4. Connect the workflow continuation after the Code node.

## Which method to choose

| Method | Security level | Best for |
|--------|---------------|----------|
| Header Auth | Medium | Internal services, simple integrations |
| Basic Auth | Medium | Services that support HTTP Basic Auth |
| HMAC | High | GitHub, Stripe, Shopify, any service that signs requests |

## Related

- [Webhook node reference](../reference/nodes/webhook.md)
- [Webhook not firing](../troubleshooting/webhook-not-firing.md)
