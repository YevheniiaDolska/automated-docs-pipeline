---
title: Intelligent knowledge system architecture
description: Explains how the pipeline models reusable knowledge modules for AI retrieval,
  dynamic assembly, and multi-channel documentation delivery.
content_type: concept
product: both
tags:
- Concept
- AI
- Reference
last_reviewed: '2026-03-20'
original_author: Developer
---

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->


# Intelligent knowledge system architecture

The intelligent knowledge system is a structured layer that stores reusable modules, metadata, and intent mappings so humans and AI can retrieve the same trusted product knowledge.

The pipeline keeps authored modules in `knowledge_modules/*.yml`, validates them, and assembles clean output documents and channel bundles. This preserves normal documentation readability while enabling AI-native retrieval and reuse.

## Core components

1. `Knowledge modules`: atomic YAML units with intent, audience, channel, dependency, and owner metadata.
1. `Intent assembler`: creates audience-specific docs pages and channel bundles from active modules.
1. `Retrieval index`: exports module-level records to `docs/assets/knowledge-retrieval-index.json`.
1. `JSON-LD graph`: exports module relationships to `docs/assets/knowledge-graph.jsonld`.
1. `Retrieval evals`: calculates Precision/Recall/Hallucination-rate in `reports/retrieval_evals_report.json`.
1. `Quality gates`: checks schema, dependency integrity, cycle safety, and content completeness.

## Why this improves documentation quality

Traditional pages duplicate content across docs, in-product guidance, and assistant prompts. Modules let you author once and distribute consistently.

- You reduce contradictory guidance because one module powers multiple channels.
- You improve AI response quality because retrieval uses intent and audience metadata.
- You cut update time because a verified module updates all downstream experiences.

## Data model

Each module defines:

- `id`, `title`, `summary`, and `owner`
- `intents`, such as `configure`, `secure`, or `troubleshoot`
- `audiences`, such as `operator` or `support`
- `channels`, such as `docs`, `assistant`, or `automation`
- `dependencies` for module composition order
- `content` blocks for each channel output

## Operational lifecycle

The knowledge lifecycle has six phases:

1. Schema and integrity validation (`npm run lint:knowledge`).
1. Intent assembly for channel outputs (`npm run build:intent`).
1. Retrieval index generation (`npm run build:knowledge-index`).
1. Graph generation for relationship context (`npm run build:knowledge-graph`).
1. Retrieval quality evaluation (`npm run eval:retrieval`).
1. Release gate consolidation (`npm run validate:knowledge`).

## RAG integration contract

Ask AI reads the same artifacts that the weekly knowledge pipeline refreshes.

- `docs/assets/knowledge-retrieval-index.json` is the primary retrieval index.
- `docs/assets/retrieval.faiss` is the FAISS vector index with `text-embedding-3-small` embeddings.
- `docs/assets/retrieval-metadata.json` is the metadata sidecar for the FAISS index.
- `docs/assets/knowledge-graph.jsonld` adds relationship context for retrieval and reasoning.
- `reports/retrieval_evals_report.json` provides retrieval quality gates (Precision, Recall, Hallucination-rate).

This shared contract keeps documentation generation, knowledge base updates, and RAG runtime aligned.

## Advanced retrieval pipeline

The RAG runtime uses six features that work together to maximize retrieval precision and recall:

1. **Token-aware chunking** splits long modules into 750-token chunks with 100-token overlap using the `cl100k_base` tokenizer. Short modules remain as single chunks. The embedding pipeline (`scripts/generate_embeddings.py --chunk`) embeds each chunk independently and stores chunk metadata (`chunk_id`, `parent_id`, `chunk_index`) in the FAISS sidecar.

1. **Hybrid search (RRF)** combines FAISS cosine similarity with token-overlap scoring. Reciprocal Rank Fusion (k=60) merges both rankings into a single list. This approach captures queries that mix specific terminology (tokens) with conceptual intent (embeddings).

1. **HyDE query expansion** generates a hypothetical documentation passage using `gpt-4.1-mini` before embedding the query. The generated passage captures domain vocabulary that the raw question may lack. The pipeline embeds the hypothetical document instead of the raw query text.

1. **Cross-encoder reranking** scores the top 20 candidates using `cross-encoder/ms-marco-MiniLM-L-6-v2`. The reranker evaluates (query, document) pairs and reorders results by relevance. This step reduces false positives before the final context window.

1. **Embedding cache** stores query embeddings in an in-memory LRU cache (TTL: 3,600 seconds, max: 512 entries). Repeated queries skip the OpenAI embedding API call.

1. **Multi-mode evaluation** compares token, semantic, hybrid, and hybrid+rerank search modes against a curated 50-query dataset (`config/retrieval_eval_dataset.yml`). Run `python3 scripts/run_retrieval_evals.py --mode all` to generate a comparison report.

### Retrieval orchestration flow

The retrieval flow starts with a question, chooses hybrid search when FAISS and hybrid mode are available, falls back to semantic or token overlap when needed, deduplicates by `parent_id`, optionally reranks with the cross-encoder, and returns top context modules.

### Configuration

All features are enabled by default in `config/ask-ai.yml`:

| Feature | Config key | Default |
| --- | --- | --- |
| Chunking | `chunking.enabled` | `true` |
| Hybrid search | `hybrid_search.enabled` | `true` |
| HyDE | `hyde.enabled` | `true` |
| Reranking | `reranking.enabled` | `true` |
| Embedding cache | `embedding_cache.enabled` | `true` |

Environment variable overrides: `ASK_AI_HYBRID_ENABLED`, `ASK_AI_HYDE_ENABLED`, `ASK_AI_RERANK_ENABLED`, `ASK_AI_EMBED_CACHE_ENABLED`.

## Security and governance

Use owner fields and verification dates to enforce accountability.

- Assign one owner per module.
- Verify security-sensitive modules every 30 days.
- Deprecate stale modules by changing `status` to `deprecated`.

## Next steps

- [Assemble intent experiences](../how-to/assemble-intent-experiences.md)
- [Intent experiences reference](../reference/intent-experiences/index.md)
- [Workflow execution model](workflow-execution-model.md)
