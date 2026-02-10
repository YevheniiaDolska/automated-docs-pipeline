---
title: "Build your first n8n workflow in 5 minutes"
description: "Create a webhook-triggered workflow that receives HTTP requests and sends Slack notifications using n8n. No coding required."
content_type: tutorial
product: both
n8n_component: webhook
tags:
  - Tutorial
  - Webhook
  - Cloud
  - Self-hosted
---

# Build your first n8n workflow in 5 minutes

An n8n workflow is a series of connected nodes that process data automatically. In this tutorial you create a workflow that receives an HTTP request via a Webhook node and sends a notification to Slack.

## Prerequisites

- An n8n instance (Cloud or self-hosted). See [installation options](https://docs.n8n.io/hosting/).
- A Slack workspace where you can add apps.

## Step 1: Create a new workflow

=== "n8n Cloud"

    1. Log in to your n8n Cloud instance.
    2. Select **New Workflow** from the top-right menu.
    3. The canvas opens with an empty workflow.

=== "Self-hosted"

    1. Open your n8n instance at `http://localhost:5678`.
    2. Select **New Workflow**.
    3. The canvas opens with an empty workflow.

## Step 2: Add a Webhook trigger node

1. Select the **+** button on the canvas.
2. Search for **Webhook** and select it.
3. Set **HTTP Method** to `POST`.
4. Copy the **Test URL** — you will need it in Step 5.

!!! info "Test URL vs Production URL"
    The Test URL is active only while the workflow editor is open. The Production URL activates after you toggle the workflow to **Active**.

## Step 3: Add a Slack node

1. Select the **+** button after the Webhook node.
2. Search for **Slack** and select it.
3. Set **Operation** to **Send a Message**.
4. Select your Slack credential or create one (requires a Slack Bot Token with `chat:write` scope).
5. Set **Channel** to your target channel name or ID.
6. Set **Text** to an expression:

```
New webhook received: {{ $json.body.message }}
```

## Step 4: Test the workflow

1. Select **Test Workflow** in the top bar.
2. In a terminal, send a test request:

```bash
curl -X POST YOUR_TEST_URL \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from my first workflow!"}'
```

3. Check your Slack channel — the message appears within 2 seconds.

## Step 5: Activate the workflow

1. Toggle the workflow to **Active** in the top-right corner.
2. Replace the Test URL with the **Production URL** in your application.

The workflow now runs automatically for every incoming request, without the editor open.

## Next steps

- [Configure Webhook authentication](../how-to/configure-webhook-trigger.md) to secure your endpoint
- [Understand the execution model](../concepts/workflow-execution-model.md) to learn how n8n processes data
- [Webhook node reference](../reference/nodes/webhook.md) for all available parameters
