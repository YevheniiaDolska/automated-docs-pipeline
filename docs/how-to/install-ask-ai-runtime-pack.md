---
title: Install Ask AI runtime pack
description: Install the optional Ask AI runtime pack with API endpoint, widget, auth
  checks, and billing hooks in a few commands.
content_type: how-to
product: both
tags:
- How-To
- AI
- Cloud
app_component: ai-agent
last_reviewed: '2026-07-04'
original_author: Developer
---

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veri-doc.app/)
<!-- VERIDOC_POWERED_BADGE:END -->

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

- FastAPI server (`app/main.py`) with advanced retrieval config
- auth guards (`app/auth.py`)
- billing hooks (`app/billing_hooks.py`)
- retrieval helpers (`app/retrieval.py`) with hybrid search, HyDE, reranking, embedding cache, and chunk deduplication
- widget script (`public/ask-ai-widget.js`)
- `.env.example` and runtime `README.md`

Runtime dependencies include `faiss-cpu`, `numpy`, `sentence-transformers` (for cross-encoder reranking), and `tiktoken` (for token-aware chunking).

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

The following advanced retrieval features are enabled by default and require no additional configuration:

| Feature | Env var override | Default |
| --- | --- | --- |
| Hybrid search (RRF) | `ASK_AI_HYBRID_ENABLED` | `true` |
| HyDE query expansion | `ASK_AI_HYDE_ENABLED` | `true` |
| Cross-encoder reranking | `ASK_AI_RERANK_ENABLED` | `true` |
| Embedding cache | `ASK_AI_EMBED_CACHE_ENABLED` | `true` |

## Step 4: Start runtime server

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8090
```

Health check:

=== "cURL"

    ```bash smoke
    curl http://localhost:8090/healthz
    ```

=== "JavaScript"

    ```javascript smoke
    const response = await fetch('http://localhost:8090/healthz', {
      method: 'GET',
      headers: {
},
    });
    const payload = await response.json();
    console.log(payload);
    ```

=== "Python"

    ```python smoke
    import requests

    response = requests.request(
        'GET',
        'http://localhost:8090/healthz',
        headers={},
        timeout=30,
    )
    response.raise_for_status()
    print(response.json())
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
  data-theme="dark"
  data-title="Ask AI"
  data-stream="true"
  data-enabled="true"></script>
```

The widget streams answers token by token, keeps conversation history for follow-up questions, renders inline citations, and shows thumbs up and thumbs down controls. Set `data-theme="light"` for a light panel and `data-stream="false"` to use the buffered endpoint.

## Stream answers as they generate

The runtime streams answers token by token over the `POST /api/v1/ask/stream` endpoint. The widget renders each token as it arrives, so readers watch the answer form in real time instead of waiting for the full reply. Send the same request body as the standard endpoint:

```bash
curl -N -X POST https://docs.example.com/ask-ai/api/v1/ask/stream \
  -H "Content-Type: application/json" \
  -H "X-Ask-AI-Key: YOUR_PUBLIC_OR_PROXY_KEY" \
  -d '{"question": "How do I rotate API keys?", "history": []}'
```

The stream sends one event per token, then a final event with the citations and question identifier:

```text
data: {"type": "token", "text": "Rotate "}

data: {"type": "done", "citations": [...], "question_id": "...", "grounded": true}
```

## Keep conversation context for follow-up questions

Send prior turns in the `history` field so follow-up questions read in context. Each turn is an object with a `role` of `user` or `assistant` and a `content` string. The `ASK_AI_HISTORY_MAX_TURNS` environment variable sets how many recent turns the server keeps, with a default of six. The widget stores the conversation and sends it with each question, so a reader can ask a follow-up such as "How does that work in self-hosted mode?" and receive a contextual answer.

## Ground answers in documentation and refuse when uncertain

The assistant answers only from the retrieved documentation sources and cites them inline with bracketed numbers such as `[1]`. The response returns a `citations` list that contains only the sources the answer references, plus a `grounded` flag. When retrieval returns no sources, or the sources do not cover the question, the runtime returns an honest refusal with `grounded` set to `false` and an empty `citations` list. The runtime records each refusal in the usage log, where it surfaces as a documentation-gap candidate in the analytics report.

## Collect reader feedback

Each answer includes thumbs up and thumbs down controls. The widget posts the rating to the `POST /api/v1/feedback` endpoint with the `question_id` from the answer. Ratings feed the usage analytics and help rank which pages to improve first.

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

### Answer reports that it cannot find the information

The runtime refuses to answer when retrieval returns no relevant sources, or when the sources do not cover the question. This behavior prevents fabricated answers. Rebuild the retrieval index so new documentation becomes searchable:

```bash
python3 scripts/generate_knowledge_retrieval_index.py
```

The `/healthz` endpoint reports the status of all advanced retrieval features:

```json
{
  "ok": true,
  "enabled": true,
  "provider": "openai",
  "billing_mode": "disabled",
  "semantic_retrieval": true,
  "reranking": true,
  "hybrid_search": true,
  "hyde": true,
  "embedding_cache": true
}
```

## Next steps

- [Configure Ask AI module](configure-ask-ai-module.md)
- [Assemble intent experiences](assemble-intent-experiences.md)
- [Intelligent knowledge system architecture](../concepts/intelligent-knowledge-system.md)
