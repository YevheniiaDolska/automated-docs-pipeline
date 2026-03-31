---
title: "Intent experience: configure for beginner"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

<!-- markdownlint-disable MD001 MD007 MD024 MD025 MD031 -->

# Intent experience: configure for beginner

This page is assembled for the `configure` intent and the `beginner` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent configure --audience beginner --channel docs
```

## Included modules

### Build your first workflow in 5 minutes

Create a webhook-triggered workflow that receives HTTP requests and sends Slack notifications. No coding required.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

#### Build your first workflow in 5 minutes: Build your first workflow in 5 minutes

A workflow is a series of connected nodes that process data automatically. In this tutorial you create a workflow that receives an HTTP request via a Webhook node and sends a notification to Slack.

#### Build your first workflow in 5 minutes: Prerequisites

- An instance (Cloud or self-hosted). See the [getting started overview](index.md).
- A Slack workspace where you can add apps.

#### Build your first workflow in 5 minutes: Step 1: Create a new workflow

=== "Cloud"

- Log in to your Cloud instance.
- Select **New Workflow** from the top-right menu.
- The canvas opens with an empty workflow.

=== "Self-hosted"

- Open your instance at `http://localhost:5678`.
- Select **New Workflow**.
- The canvas opens with an empty workflow.

#### Build your first workflow in 5 minutes: Step 2: Add a Webhook trigger node

1. Select the **+** button on the canvas.
1. Search for **Webhook** and select it.
1. Set **HTTP Method** to `POST`.
1. Copy the **Test URL**—you will need it in Step 5.

!!! info "Test URL vs Production URL"
 The Test URL is active only while the workflow editor is open. The Production URL activates after you toggle the workflow to **Active**.

### Build your first workflow in 5 minutes (Part 2)

Create a webhook-triggered workflow that receives HTTP requests and sends Slack notifications. No coding required.

#### Build your first workflow in 5 minutes (Part 2): Step 3: Add a Slack node

1. Select the **+** button after the Webhook node.
1. Search for **Slack** and select it.
1. Set **Operation** to **Send a Message**.
1. Select your Slack credential or create one (requires a Slack Bot Token with `chat:write` scope).
1. Set **Channel** to your target channel name or ID.
1. Set **Text** to an expression:

```text

New webhook received: {% raw %}{{ $json.body.message }}{% endraw %}

```

#### Build your first workflow in 5 minutes (Part 2): Step 4: Test the workflow

1. Select **Test Workflow** in the top bar.
1. In a terminal, send a test request:

```bash

curl -X POST YOUR_TEST_URL \
 -H "Content-Type: application/json" \
 -d '{"message": "Hello from my first workflow!"}'

```

1. Check your Slack channel—the message appears within 2 seconds.

#### Build your first workflow in 5 minutes (Part 2): Step 5: Activate the workflow

1. Toggle the workflow to **Active** in the top-right corner.
1. Replace the Test URL with the **Production URL** in your application.

The workflow now runs automatically for every incoming request, without the editor open.

#### Build your first workflow in 5 minutes (Part 2): Next steps

- [Configure Webhook authentication](../how-to/configure-webhook-trigger.md) to secure your endpoint
- [Understand the execution model](../concepts/workflow-execution-model.md) to learn how workflows process data
- [Webhook node reference](../reference/nodes/webhook.md) for all available parameters

## Next steps

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`
