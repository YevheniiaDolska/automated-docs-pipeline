---
title: Configure webhook triggers
description: Set up and configure webhook trigger nodes to start workflows from incoming
  HTTP requests with authentication.
content_type: how-to
product: both
tags:
- Webhook
- How-To
last_reviewed: '2026-03-07'
app_component: webhook
original_author: JaneDo
---


<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

# Configure webhook triggers

The {{ product_name }} webhook trigger node starts workflows when it
receives HTTP requests. It supports GET, POST, PUT, PATCH, and DELETE
methods with built-in authentication options including Basic Auth,
Header Auth, and JWT validation.

## Before you start

You need:

- {{ product_name }} {{ current_version }} or later
- Access to create workflows
- A publicly accessible URL (or a tunnel for local development)

## Create a webhook trigger

1. Open the {{ product_name }} editor
1. Add a new workflow
1. Select **Webhook** as the trigger node
1. Choose the HTTP method (POST is recommended for event data)
1. Copy the generated webhook URL

=== "Cloud"

    {{ product_name }} Cloud provides a public URL automatically:

    ```text
    {{ cloud_url }}/webhook/your-workflow-id
    ```

=== "Self-hosted"

    Configure your instance URL with the {{ env_vars.webhook_url }}
    environment variable:

    ```bash
    export {{ env_vars.webhook_url }}="https://your-domain.example.com"
    ```

    Your webhook URL follows this pattern:

    ```text
    https://your-domain.example.com:{{ default_port }}/webhook/your-workflow-id
    ```

## Configure authentication

!!! warning "Secure your webhooks"
    Always enable authentication on production webhook endpoints.
    Unauthenticated webhooks accept requests from any source.
Add authentication in the webhook node settings:

| Auth method | Use case | Configuration |
|-------------|----------|---------------|
| Header Auth | API key validation | Set header name and expected value |
| Basic Auth | Username and password | Set credentials in node settings |
| JWT | Token-based auth | Configure secret and algorithm |

## Test webhook delivery

Send a test request to verify your webhook works:

=== "cURL"

    ```bash smoke
    curl -X POST https://your-domain.example.com:5678/webhook/test \
      -H "Content-Type: application/json" \
      -d '{"event": "test", "timestamp": "2026-03-07T12:00:00Z"}'
    ```

=== "JavaScript"

    ```javascript smoke
    const response = await fetch('https://your-domain.example.com:5678/webhook/test', {
      method: 'POST',
      headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({"event": "test", "timestamp": "2026-03-07T12:00:00Z"}),
    });
    const payload = await response.json();
    console.log(payload);
    ```

=== "Python"

    ```python smoke
    import requests

    response = requests.request(
        'POST',
        'https://your-domain.example.com:5678/webhook/test',
        headers={'Content-Type': 'application/json'},
    json='{"event": "test", "timestamp": "2026-03-07T12:00:00Z"}',
        timeout=30,
    )
    response.raise_for_status()
    print(response.json())
    ```

Expected response:

```json
{
  "status": "accepted",
  "executionId": "exec_abc123"
}
```

!!! tip "Use the test URL first"
    {{ product_name }} provides separate test and production webhook
    URLs. Use the test URL during development to inspect payloads
    without triggering downstream actions.
## Troubleshoot webhook triggers

### Webhook returns 404

Verify the workflow is active. Inactive workflows do not register
webhook endpoints. Activate the workflow and retry.

### Request body is empty

Check that you send the `Content-Type: application/json` header.
{{ product_name }} requires this header to parse JSON request bodies.

## Related resources

- [Webhook node reference](../reference/nodes/webhook.md)
- [Troubleshoot webhook issues](../troubleshooting/webhook-not-firing.md)

## Next steps

- [Documentation index](index.md)
