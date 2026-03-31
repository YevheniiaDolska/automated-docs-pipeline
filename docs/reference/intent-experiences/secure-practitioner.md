---
title: "Intent experience: secure for practitioner"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

<!-- markdownlint-disable MD001 MD007 MD024 MD025 MD031 -->

# Intent experience: secure for practitioner

This page is assembled for the `secure` intent and the `practitioner` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent secure --audience practitioner --channel docs
```

## Included modules

### Configure webhook triggers

Set up and configure webhook trigger nodes to start workflows from incoming HTTP requests with authentication.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Configure webhook triggers: Configure webhook triggers

The {{ product_name }} webhook trigger node starts workflows when it
receives HTTP requests. It supports GET, POST, PUT, PATCH, and DELETE
methods with built-in authentication options including Basic Auth,
Header Auth, and JWT validation.

#### Configure webhook triggers: Before you start

You need:

- {{ product_name }} {{ current_version }} or later
- Access to create workflows
- A publicly accessible URL (or a tunnel for local development)

#### Configure webhook triggers: Create a webhook trigger

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

### Configure webhook triggers (Part 2)

Set up and configure webhook trigger nodes to start workflows from incoming HTTP requests with authentication.

#### Configure webhook triggers (Part 2): Configure authentication

!!! warning "Secure your webhooks"
    Always enable authentication on production webhook endpoints.
    Unauthenticated webhooks accept requests from any source.

Add authentication in the webhook node settings:

| Auth method | Use case | Configuration |
|-------------|----------|---------------|
| Header Auth | API key validation | Set header name and expected value |
| Basic Auth | Username and password | Set credentials in node settings |
| JWT | Token-based auth | Configure secret and algorithm |

### Install Ask AI runtime pack

Install the optional Ask AI runtime pack with API endpoint, widget, auth checks, and billing hooks in a few commands.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Install Ask AI runtime pack: Install Ask AI runtime pack

Use this guide when a client asks for Ask AI runtime features such as a live endpoint, an embeddable widget, and billing webhook hooks.

```bash

npm run askai:runtime:install
npm run askai:status

```

#### Install Ask AI runtime pack: Before you start

You need:

- Pipeline repository installed in the client project
- `config/ask-ai.yml` present
- Python 3.10 or newer

#### Install Ask AI runtime pack: Step 1: Install the runtime pack

Run:

```bash

npm run askai:runtime:install

```

This creates `ask-ai-runtime/` with:

- FastAPI server (`app/main.py`) with advanced retrieval config
- auth guards (`app/auth.py`)
- billing hooks (`app/billing_hooks.py`)
- retrieval helpers (`app/retrieval.py`) with hybrid search, HyDE, reranking, embedding cache, and chunk deduplication
- widget script (`public/ask-ai-widget.js`)
- `.env.example` and runtime `README.md`

Runtime dependencies include `faiss-cpu`, `numpy`, `sentence-transformers` (for cross-encoder reranking), and `tiktoken` (for token-aware chunking).

#### Install Ask AI runtime pack: Step 2: Configure Ask AI module

Enable Ask AI and select billing mode:

```bash

npm run askai:enable
npm run askai:configure -- --provider openai --billing-mode user-subscription --model gpt-4.1-mini

```

### Migrate documentation from Confluence (Part 7)

Import Confluence pages into the documentation pipeline with automatic quality enhancement, SEO optimization, and knowledge extraction.

#### Migrate documentation from Confluence (Part 7): Review migration reports

The pipeline generates two report files in the reports directory
(default: `reports/`):

- `confluence_migration_report.json` -- machine-readable report with page
  counts, check results, and status
- `confluence_migration_report.md` -- human-readable report with migration
  summary, automatic fixes applied, and check results

Specify a custom reports directory with `--reports-dir`:

```bash

python3 scripts/run_confluence_migration.py \
  --export-zip /path/to/confluence-export.zip \
  --reports-dir /path/to/reports

```

#### Migrate documentation from Confluence (Part 7): Troubleshoot common issues

##### Migrate documentation from Confluence (Part 7): Authentication fails with 401 error

**Cause:** Invalid or expired API token.

**Fix:** Generate a new token following the steps in
[Create an API token](#step-1-create-an-api-token). For Cloud, verify you use
your email address with `--confluence-username`, not your display name.

##### Migrate documentation from Confluence (Part 7): Rate limiting (429 responses)

**Cause:** Confluence rate limits API requests.

**Fix:** The pipeline automatically retries with exponential backoff (3
retries). For large spaces with more than 1,000 pages, the pipeline
paginates requests automatically. If rate limiting persists, wait 60 seconds
and retry.

### Operator Runbook (Retainer Operations) (Part 5)

Step-by-step instructions for weekly report review, client questions, new repo setup, and profile tuning.

##### Operator Runbook (Retainer Operations) (Part 5): Step 1.3: Review action items by priority

Scroll to `action_items` array. Items are pre-sorted by priority:

- **Tier 1 (high priority):** items with `source_report: "drift"` or `source_report: "sla"` -- these indicate broken API docs or SLA violations. Inform the client immediately.
- **Tier 2 (medium priority):** items with categories like `stale_doc`, `signature_change`, `new_function` -- these are code-driven gaps. Include in next documentation sprint.
- **Tier 3 (low priority):** community/search-driven gaps. Schedule when capacity allows.

##### Operator Runbook (Retainer Operations) (Part 5): Step 1.4: Send the weekly summary to the client

Write a brief summary (3-5 sentences) covering:

1. Quality score and trend (up/down/stable vs last week).
1. Any drift or SLA issues that need attention.
1. Number of action items by tier.
1. Recommended next steps (if any).

**Example email:**

> Weekly VeriOps Report -- ACME Inc. (March 21, 2026)
>
> Quality score: 82 (up from 76 last week). No API drift detected.
> SLA status: OK (all thresholds met).
> Action items: 3 high priority (stale auth docs), 5 medium, 4 low.
> Recommendation: Update authentication reference docs this week.

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

### Set up a real-time webhook processing pipeline

Configure end-to-end webhook ingestion with HMAC verification, async queue processing, and delivery guarantees in under 15 minutes.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Set up a real-time webhook processing pipeline: Set up a real-time webhook processing pipeline

{{ product_name }} webhook processing pipeline enables real-time event ingestion with cryptographic signature verification, async queue processing, and automatic retry logic. This guide walks you through setting up a production-ready webhook receiver with HMAC-SHA256 authentication, BullMQ event queuing, and delivery guarantees supporting up to {{ rate_limit_requests_per_minute }} events per minute.

#### Set up a real-time webhook processing pipeline: Prerequisites for webhook pipeline setup

Before starting, ensure you have:

- {{ product_name }} version {{ current_version }} or later
- Admin access to the {{ product_name }} dashboard at {{ cloud_url }}
- Node.js 18 or later and Python 3.10 or later installed
- Redis 7.0 or later running for queue storage
- 15 minutes for initial setup

Verify your environment:

```bash

node --version    # v18.0.0 or later
python3 --version # 3.10 or later
redis-cli ping    # PONG

```

!!! info "Already have a webhook endpoint running?"
    Skip to [configure HMAC signature verification](#verify-hmac-sha256-signatures) for adding cryptographic authentication to an existing receiver.

### Configure HMAC authentication for inbound webhooks

Covers secure webhook authentication setup for docs, assistant responses, in-product hints, and automation workflows with one reusable module.

Use HMAC validation to reject spoofed webhook requests before your workflow executes. Set the shared secret in {{ env_vars.webhook_url }} settings, then verify the `X-Signature` header with SHA-256. Reject requests older than 300 seconds, and return HTTP 401 for invalid signatures.

```bash

curl -X POST "http://localhost:{{ default_webhook_port }}/webhook/order-events" \\
  -H "Content-Type: application/json" \\
  -H "X-Signature: sha256=YOUR_CALCULATED_SIGNATURE" \\
  -d '{"order_id":"ord_9482","event":"order_paid","amount":129.99}'

```

Keep replay protection enabled, rotate the secret every 90 days, and monitor 401 spikes for abuse detection.

## Next steps

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`
