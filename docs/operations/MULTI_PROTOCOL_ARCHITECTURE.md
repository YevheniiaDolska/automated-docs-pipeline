---
title: "Multi-Protocol Architecture"
description: "Unified docs-ops pipeline for REST, GraphQL, gRPC, AsyncAPI, and WebSocket."
content_type: reference
product: both
last_reviewed: "2026-03-19"
tags:
  - Architecture
  - API
  - Operations
---

# VeriDoc/VeriOps Multi-Protocol Architecture

Positioning statement:

`VeriDoc/VeriOps: one docs-ops pipeline for REST, GraphQL, gRPC, AsyncAPI, and WebSocket.`

## Supported protocols (core-5)

1. REST (OpenAPI)
1. GraphQL (SDL/introspection)
1. gRPC (Proto/descriptor)
1. AsyncAPI (event-driven specs)
1. WebSocket (channel/message contracts)

## Unified stage flow

`ingest -> lint -> regression -> docs generation -> quality gates -> test assets -> upload -> publish`

Implementation entrypoint:

```bash
python3 scripts/run_multi_protocol_contract_flow.py \
  --runtime-config docsops/config/client_runtime.yml \
  --reports-dir reports
```

## Engine and adapters

- `scripts/multi_protocol_engine.py` - stage adapter orchestration.
- `scripts/run_multi_protocol_contract_flow.py` - flow runner + report output.
- `scripts/api_protocols.py` - protocol normalization, aliases, defaults.

## Protocol-specific validators

- REST: `scripts/validate_openapi_contract.py`
- GraphQL: `scripts/validate_graphql_contract.py` (root/schema checks, duplicate types/fields, root-type references)
- gRPC: `scripts/validate_proto_contract.py` (syntax checks, duplicate declarations/rpcs, proto3 `required` guard)
- AsyncAPI: `scripts/validate_asyncapi_contract.py` (channel operations + message payload semantics)
- WebSocket: `scripts/validate_websocket_contract.py` (channel/event presence + payload/schema semantics)
- Deep protocol lint stack (7+ checks): `scripts/run_protocol_lint_stack.py`

## Regression

- Generic snapshot gate: `scripts/check_protocol_regression.py`
- Per-protocol snapshot path is runtime-configurable.

## Docs + publish

- Generate protocol docs: `scripts/generate_protocol_docs.py`
- Publish protocol assets: `scripts/publish_protocol_assets.py`
- Generated protocol docs include interactive testers:
  - GraphQL query execution (mock/real endpoint)
  - gRPC via HTTP gateway adapter
  - AsyncAPI ws/http publish checks
  - WebSocket live connect/send checks

## Test assets and smart-merge

- Generator: `scripts/generate_protocol_test_assets.py`
- Upload: `scripts/upload_api_test_assets.py`
- Coverage gate: `scripts/validate_protocol_test_coverage.py`
- Runtime self-verify (mock/real endpoint): `scripts/run_protocol_self_verify.py`
- Protocol docs quality + lifecycle suite: `scripts/run_protocol_docs_quality_suite.py`
  - applies docs normalization, metadata optimization, multilang/smoke checks
  - updates glossary markers
  - refreshes RAG assets (knowledge modules, retrieval index, knowledge graph, retrieval evals)
- Smart-merge preserves manual/customized cases and sets `needs_review` on drift/stale entities.
- Non-REST generator emits richer artifacts: cases JSON, TestRail CSV, Zephyr JSON, `test_matrix.json`, `fuzz_scenarios.json`.

## Advanced RAG retrieval pipeline

The multi-protocol quality suite (`run_protocol_docs_quality_suite.py`) refreshes RAG assets including FAISS embeddings. Six advanced retrieval features are available:

| Feature | Module | Description |
| --- | --- | --- |
| Token-aware chunking | `scripts/chunker.py` | Splits modules into 750-token chunks with 100-token overlap (`cl100k_base`) |
| FAISS embeddings | `scripts/generate_embeddings.py --chunk` | Embeds chunks with `text-embedding-3-small`, builds FAISS index |
| Hybrid search (RRF) | `runtime/.../retrieval.py` | Fuses semantic and token-overlap rankings (k=60) |
| HyDE query expansion | `runtime/.../retrieval.py` | Generates hypothetical passage via `gpt-4.1-mini` before embedding |
| Cross-encoder reranking | `scripts/vector_store.py`, `runtime/.../retrieval.py` | Rescores top 20 candidates with `ms-marco-MiniLM-L-6-v2` |
| Embedding cache | `runtime/.../retrieval.py` | In-memory LRU cache (TTL: 3,600 seconds, max: 512) |
| Multi-mode evaluation | `scripts/run_retrieval_evals.py --mode all` | Compares token, semantic, hybrid, and hybrid+rerank modes |

### RAG prep behavior on pipeline run

1. Extract knowledge modules from docs
1. Validate modules and rebuild retrieval index
1. Generate FAISS embeddings with optional chunking (`--chunk`)
1. Run retrieval evals (single-mode or multi-mode comparison)
1. Output comparison report to `reports/retrieval_comparison.json`

### Configuration

All features are enabled by default in `config/ask-ai.yml`. Runtime overrides via environment variables: `ASK_AI_HYBRID_ENABLED`, `ASK_AI_HYDE_ENABLED`, `ASK_AI_RERANK_ENABLED`, `ASK_AI_EMBED_CACHE_ENABLED`.

### Eval dataset

A curated 50-query eval dataset is maintained at `config/retrieval_eval_dataset.yml`. It covers queries across all five protocols (REST, GraphQL, gRPC, AsyncAPI, WebSocket).

## Template and snippet parity

- Protocol-specific templates are part of the default library:
  - `templates/protocols/graphql-reference.md`
  - `templates/protocols/grpc-reference.md`
  - `templates/protocols/asyncapi-reference.md`
  - `templates/protocols/websocket-reference.md`
- Reusable blocks are centralized in `templates/protocols/api-protocol-snippets.md`.
- LLM generation uses these assets to keep structure, terminology, and formatting consistent with REST-grade docs.

## Next steps

- [Documentation index](../index.md)
