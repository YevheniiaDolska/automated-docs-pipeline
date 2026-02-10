---
title: "[Product] glossary"
description: "Definitions of key terms, concepts, and abbreviations used in [Product] documentation. Understand API terminology, features, and technical concepts."
content_type: reference
product: both
tags:
  - Reference
---

# Glossary

Definitions of terms used throughout [Product] documentation.

## A

### Access token
A credential used to authenticate API requests. Access tokens have limited validity (typically 1 hour) and should not be stored long-term. See [Authentication](../how-to/authentication.md).

### API key
A permanent credential for authenticating server-to-server requests. API keys should be kept secret and never exposed in client-side code. See [API key authentication](../how-to/authentication.md#api-key-authentication).

### API version
[Product] uses dated API versions (e.g., `2024-01-01`) to manage breaking changes. Pin your integration to a specific version for stability. See [Versioning](../reference/versioning.md).

## B

### Base URL
The root URL for API requests: `https://api.[product].com/v1/`. All endpoints are relative to this URL.

### Bearer token
An access token passed in the `Authorization` header: `Authorization: Bearer <token>`.

## C

### Client credentials
OAuth 2.0 flow for machine-to-machine authentication without user interaction. Returns an access token for your application. See [OAuth 2.0](../how-to/authentication.md#oauth-20).

### Cursor
A pointer used for pagination. Instead of page numbers, cursors provide stable pagination through changing data. See [Pagination](../reference/api.md#pagination).

## E

### Endpoint
A specific URL path that accepts API requests. For example, `/v1/[resources]` is the endpoint for listing [resources].

### Environment
[Product] provides two environments:
- **Test/Sandbox:** For development and testing (uses `sk_test_` keys)
- **Live/Production:** For production traffic (uses `sk_live_` keys)

### Event
An occurrence in [Product] that can trigger a webhook. Events have types like `[resource].created` or `[resource].updated`. See [Events reference](../reference/events.md).

### Exponential backoff
A retry strategy that increases wait time between attempts (e.g., 1s, 2s, 4s, 8s). Used for handling rate limits and transient errors. See [Error handling](../how-to/error-handling.md).

## I

### Idempotency
The property where repeating a request produces the same result. Use idempotency keys to safely retry requests without duplicating actions. See [Idempotency](../reference/api.md#idempotency).

### Idempotency key
A unique identifier sent with requests to prevent duplicate operations. If a request with the same key is repeated, the original response is returned.

## O

### OAuth 2.0
An authorization framework for granting third-party applications access to user accounts. [Product] supports Authorization Code and Client Credentials flows. See [OAuth 2.0](../how-to/authentication.md#oauth-20).

## P

### Pagination
The process of splitting large result sets into pages. [Product] uses cursor-based pagination with `limit` and `starting_after` parameters. See [Pagination](../reference/api.md#pagination).

### Publishable key
An API key safe for client-side use (prefix: `pk_`). Limited to specific endpoints and read-only operations.

## R

### Rate limit
The maximum number of API requests allowed per time period. Exceeding limits returns `429 Too Many Requests`. See [Rate limits](../reference/rate-limits.md).

### Refresh token
A long-lived token used to obtain new access tokens without re-authentication. Store securely and rotate regularly.

### Request ID
A unique identifier included in every API response (`request_id`). Use when contacting support or reviewing logs.

### [Resource]
[Definition specific to your product]. See [[Resource] reference](../reference/[resource].md).

## S

### Sandbox
See [Environment](#environment).

### SDK (Software Development Kit)
Official client libraries for [Product] in various languages. SDKs handle authentication, errors, and retries automatically.

### Secret key
An API key for server-side use (prefix: `sk_`). Never expose in client-side code or public repositories.

### Signing secret
A secret used to verify webhook signatures. Each webhook endpoint has a unique signing secret.

## T

### Test mode
See [Environment](#environment).

### Token
See [Access token](#access-token) or [Refresh token](#refresh-token).

## W

### Webhook
An HTTP callback that sends real-time notifications when events occur. Your application provides an endpoint, and [Product] sends POST requests with event data. See [Webhooks guide](../how-to/webhooks.md).

### Webhook endpoint
A URL in your application that receives webhook events.

### Webhook signature
A cryptographic signature in webhook headers used to verify the request came from [Product]. Always verify signatures before processing webhooks.

---

## See also

- [API Reference](../reference/api.md)
- [Authentication guide](../how-to/authentication.md)
- [Webhooks guide](../how-to/webhooks.md)
