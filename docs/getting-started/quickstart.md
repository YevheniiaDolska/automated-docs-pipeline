---
title: "Build your first workflow in 5 minutes"
description: "Create a webhook-triggered workflow that receives HTTP requests and sends Slack notifications. No coding required."
content_type: tutorial
product: both
tags:

 - Tutorial
 - Webhook
 - Cloud
 - Self-hosted

---

## Build your first workflow in 5 minutes

A workflow is a series of connected nodes that process data automatically. In this tutorial you create a workflow that receives an HTTP request via a Webhook node and sends a notification to Slack.

## Prerequisites

- An instance (Cloud or self-hosted). See [installation options](../installation.md).
- A Slack workspace where you can add apps.

## Step 1: Create a new workflow

=== "Cloud"

- Log in to your Cloud instance.
- Select **New Workflow** from the top-right menu.
- The canvas opens with an empty workflow.

=== "Self-hosted"

- Open your instance at `<http://localhost:5678`.>
- Select **New Workflow**.
- The canvas opens with an empty workflow.

## Step 2: Add a Webhook trigger node

1. Select the **+** button on the canvas.
1. Search for **Webhook** and select it.
1. Set **HTTP Method** to `POST`.
1. Copy the **Test URL** — you will need it in Step 5.

!!! info "Test URL vs Production URL"
 The Test URL is active only while the workflow editor is open. The Production URL activates after you toggle the workflow to **Active**.

## Step 3: Add a Slack node

1. Select the **+** button after the Webhook node.
1. Search for **Slack** and select it.
1. Set **Operation** to **Send a Message**.
1. Select your Slack credential or create one (requires a Slack Bot Token with `chat:write` scope).
1. Set **Channel** to your target channel name or ID.
1. Set **Text** to an expression:

```json
New webhook received: {% raw %}{{ $json.body.message }}{% endraw %}
```

## Step 4: Test the workflow

1. Select **Test Workflow** in the top bar.
1. In a terminal, send a test request:

```bash
curl -X POST YOUR_TEST_URL \
 -H "Content-Type: application/json" \
 -d '{"message": "Hello from my first workflow!"}'
```

1. Check your Slack channel — the message appears within 2 seconds.

## Step 5: Activate the workflow

1. Toggle the workflow to **Active** in the top-right corner.
1. Replace the Test URL with the **Production URL** in your application.

The workflow now runs automatically for every incoming request, without the editor open.

## Next steps

- [Configure Webhook authentication](../how-to/configure-webhook-trigger.md) to secure your endpoint
- [Understand the execution model](../concepts/workflow-execution-model.md) to learn how workflows process data
- [Webhook node reference](../reference/nodes/webhook.md) for all available parameters
