---
title: Configure Ask AI module
description: Enable or disable Ask AI, set provider and billing mode, and verify configuration
  in five steps for beginner operators.
content_type: how-to
product: both
tags:
- How-To
- AI
- Cloud
app_component: ai-agent
last_reviewed: '2026-03-20'
original_author: Developer
---

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->


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

## Step 4: Configure advanced retrieval features

All six advanced retrieval features are enabled by default. Override individual features with environment variables or by editing `config/ask-ai.yml` directly:

```bash
npm run askai:configure -- \
  --hybrid-search \
  --hyde \
  --reranking \
  --embedding-cache
```

| Feature | Config key | Env var | Default |
| --- | --- | --- | --- |
| Token-aware chunking | `chunking.enabled` | -- (build-time only) | `true` |
| Hybrid search (RRF) | `hybrid_search.enabled` | `ASK_AI_HYBRID_ENABLED` | `true` |
| HyDE query expansion | `hyde.enabled` | `ASK_AI_HYDE_ENABLED` | `true` |
| Cross-encoder reranking | `reranking.enabled` | `ASK_AI_RERANK_ENABLED` | `true` |
| Embedding cache | `embedding_cache.enabled` | `ASK_AI_EMBED_CACHE_ENABLED` | `true` |

Advanced tuning parameters:

| Parameter | Env var | Default | Description |
| --- | --- | --- | --- |
| Rerank model | `ASK_AI_RERANK_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Cross-encoder model |
| Rerank candidates | `ASK_AI_RERANK_CANDIDATES` | `20` | Candidates fetched before reranking |
| RRF k | `ASK_AI_RRF_K` | `60` | Reciprocal Rank Fusion parameter |
| HyDE model | `ASK_AI_HYDE_MODEL` | `gpt-4.1-mini` | Model for hypothetical document generation |
| Cache TTL | `ASK_AI_EMBED_CACHE_TTL` | `3600` | Cache time-to-live in seconds |
| Cache max size | `ASK_AI_EMBED_CACHE_MAX_SIZE` | `512` | Maximum cached embeddings |
| Chunk max tokens | `chunking.max_tokens` | `750` | Maximum tokens per chunk |
| Chunk overlap | `chunking.overlap_tokens` | `100` | Overlap tokens between chunks |

## Step 5: Set access and safety limits

Example:

```bash
npm run askai:configure -- \
  --allowed-roles admin,support \
  --rate-limit-per-user-per-minute 20 \
  --retention-days 30 \
  --audit-logging
```

This keeps Ask AI restricted to approved roles with audit logging enabled.

## Step 6: Validate and commit

Run:

```bash
npm run lint
npm run askai:status
```

Confirm:

- `enabled` matches client request
- `billing_mode` matches contract
- `provider` and `model` match the planned setup
- `knowledge_index_path`, `knowledge_graph_path`, and `retrieval_eval_report_path` point to current RAG artifacts
- `faiss_index_path` and `faiss_metadata_path` point to FAISS embedding assets
- advanced retrieval features (hybrid search, HyDE, reranking, embedding cache) are enabled
- weekly pipeline refresh keeps RAG artifacts up to date before assistant runs

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
