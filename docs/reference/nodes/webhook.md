---
title: "Webhook node reference for n8n"
description: "Complete parameter reference for the n8n Webhook trigger node including HTTP methods, authentication, response modes, and binary data handling."
content_type: reference
product: both
n8n_component: webhook
n8n_version: "2.0"
tags:
  - Reference
  - Webhook
  - Nodes
---

# Webhook node reference

The Webhook node is a trigger node that starts a workflow when it receives an HTTP request at a unique URL. It supports GET, POST, PUT, PATCH, DELETE, and HEAD methods.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **HTTP Method** | enum | `GET` | HTTP method the webhook responds to. Options: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD` |
| **Path** | string | auto-generated UUID | URL path segment. The full URL is `{base_url}/webhook/{path}` |
| **Authentication** | enum | `None` | Authentication method. Options: `None`, `Basic Auth`, `Header Auth` |
| **Respond** | enum | `When Last Node Finishes` | When to send the HTTP response. Options: `Immediately`, `When Last Node Finishes`, `Using Respond to Webhook Node` |
| **Response Code** | number | `200` | HTTP status code returned to the caller |
| **Response Data** | enum | `First Entry JSON` | What data to return. Options: `All Entries`, `First Entry JSON`, `First Entry Binary`, `No Response Body` |

## Authentication options

| Method | Credential type | Header checked |
|--------|----------------|----------------|
| None | — | — |
| Basic Auth | Basic Auth | `Authorization: Basic {base64}` |
| Header Auth | Header Auth | Custom header name/value pair |

## URLs

Each Webhook node generates two URLs:

- **Test URL**: Active only while the workflow editor is open and listening. Format: `{base_url}/webhook-test/{path}`
- **Production URL**: Active when the workflow is toggled to Active. Format: `{base_url}/webhook/{path}`

=== "n8n Cloud"

    Base URL: `https://your-instance.app.n8n.cloud`

=== "Self-hosted"

    Base URL: your configured `WEBHOOK_URL` environment variable, or `http://localhost:5678` by default.

## Output

The Webhook node outputs a single item with the following structure:

```json
{
  "json": {
    "headers": { "content-type": "application/json", "...": "..." },
    "params": {},
    "query": { "key": "value" },
    "body": { "...": "request body..." }
  }
}
```

For binary data (file uploads), the node outputs an additional `binary` key.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBHOOK_URL` | `http://localhost:5678` | Base URL for webhook endpoints |
| `N8N_PAYLOAD_SIZE_MAX` | `16` | Maximum request body size in MB |

## Related

- [Configure Webhook authentication](../../how-to/configure-webhook-trigger.md)
- [Webhook not firing](../../troubleshooting/webhook-not-firing.md)
- [Workflow execution model](../../concepts/workflow-execution-model.md)
