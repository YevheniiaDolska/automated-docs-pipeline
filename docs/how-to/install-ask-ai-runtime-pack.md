---
title: "Install Ask AI runtime pack"
description: "Install the optional Ask AI runtime pack with API endpoint, widget, auth checks, and billing hooks in a few commands."
content_type: how-to
product: both
tags:
  - How-To
  - AI
  - Cloud
---

# Install Ask AI runtime pack

Use this guide when a client asks for Ask AI runtime features such as a live endpoint, an embeddable widget, and billing webhook hooks.

```bash
npm run askai:runtime:install
npm run askai:status
```

## Before you start

You need:

- Pipeline repository installed in the client project
- `config/ask-ai.yml` present
- Python 3.10 or newer

## Step 1: Install the runtime pack

Run:

```bash
npm run askai:runtime:install
```

This creates `ask-ai-runtime/` with:

- FastAPI server (`app/main.py`)
- auth guards (`app/auth.py`)
- billing hooks (`app/billing_hooks.py`)
- retrieval helpers (`app/retrieval.py`)
- widget script (`public/ask-ai-widget.js`)
- `.env.example` and runtime `README.md`

## Step 2: Configure Ask AI module

Enable Ask AI and select billing mode:

```bash
npm run askai:enable
npm run askai:configure -- --provider openai --billing-mode user-subscription --model gpt-4.1-mini
```

## Step 3: Configure runtime environment

```bash
cd ask-ai-runtime
cp .env.example .env
```

Fill these values in `.env`:

- `ASK_AI_API_KEY`
- `ASK_AI_PROVIDER_API_KEY`
- `ASK_AI_WEBHOOK_SECRET`

## Step 4: Start runtime server

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8090
```

Health check:

```bash
curl http://localhost:8090/healthz
```

## Step 5: Embed the widget

Add this snippet to the docs site page template or custom HTML block:

```html
<script
  src="/ask-ai/public/ask-ai-widget.js"
  data-ask-ai-endpoint="https://docs.example.com/ask-ai/api/v1/ask"
  data-ask-ai-api-key="YOUR_PUBLIC_OR_PROXY_KEY"
  data-user-id="USER_123"
  data-user-role="support"
  data-plan="pro"
  data-enabled="true"></script>
```

## Troubleshooting

### Runtime pack install fails because destination exists

Use force mode:

```bash
npm run askai:runtime:install:force
```

### Ask endpoint returns 401

Check `X-Ask-AI-Key` header and `ASK_AI_API_KEY` value.

### Ask endpoint returns 402

The current user plan is not entitled by billing mode logic. Confirm `ASK_AI_BILLING_MODE` and user plan header.

## Next steps

- [Configure Ask AI module](configure-ask-ai-module.md)
- [Assemble intent experiences](assemble-intent-experiences.md)
