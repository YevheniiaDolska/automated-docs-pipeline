---
title: "Configure Ask AI module"
description: "Enable or disable Ask AI, set provider and billing mode, and verify configuration in five steps for beginner operators."
content_type: how-to
product: both
tags:
  - How-To
  - AI
  - Cloud
---

# Configure Ask AI module

Use this guide to enable or disable Ask AI in the pipeline and set provider plus billing mode without editing multiple files manually.

```bash
npm run askai:status
npm run askai:enable
npm run askai:configure -- --provider openai --billing-mode user-subscription --model gpt-4.1-mini
```

## Before you start

You need:

- A working project setup (`npm install` completed)
- Access to `config/ask-ai.yml`
- A decision about billing mode:
  - `disabled`
  - `bring-your-own-key`
  - `user-subscription`

## Step 1: Check current status

Run:

```bash
npm run askai:status
```

This prints the active Ask AI configuration from `config/ask-ai.yml`.

## Step 2: Enable or disable Ask AI

Enable:

```bash
npm run askai:enable
```

Disable:

```bash
npm run askai:disable
```

Use disabled mode when a client does not want AI Q&A in their deployment.

## Step 3: Set provider and billing mode

Example for managed usage:

```bash
npm run askai:configure -- --provider openai --billing-mode user-subscription --model gpt-4.1-mini
```

Example for customer-provided key:

```bash
npm run askai:configure -- --provider openai --billing-mode bring-your-own-key
```

## Step 4: Set access and safety limits

Example:

```bash
npm run askai:configure -- \
  --allowed-roles admin,support \
  --rate-limit-per-user-per-minute 20 \
  --retention-days 30 \
  --audit-logging
```

This keeps Ask AI restricted to approved roles with audit logging enabled.

## Step 5: Validate and commit

Run:

```bash
npm run lint
npm run askai:status
```

Confirm:

- `enabled` matches client request
- `billing_mode` matches contract
- `provider` and `model` match the planned setup

## Troubleshooting

### Error: unsupported provider or billing mode

Cause: the value is outside allowed options.

Fix:

```bash
npm run askai:configure -- --help
```

Use only:

- Provider: `openai`, `anthropic`, `azure-openai`, `custom`
- Billing: `disabled`, `bring-your-own-key`, `user-subscription`

### Configuration changed but team does not see it

Cause: local branch mismatch or uncommitted config.

Fix:

```bash
git status
git add config/ask-ai.yml reports/ask-ai-config.json
git commit -m "docs-ops: update Ask AI configuration"
```

## Next steps

- [Quick start](../getting-started/quickstart.md)
- [Assemble intent experiences](./assemble-intent-experiences.md)
- [Intelligent knowledge system architecture](../concepts/intelligent-knowledge-system.md)
