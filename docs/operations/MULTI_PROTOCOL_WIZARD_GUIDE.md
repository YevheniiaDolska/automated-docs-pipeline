---
title: "Multi-Protocol Wizard Guide"
description: "Wizard UX for protocol-aware provisioning in VeriDoc and VeriOps."
content_type: how-to
product: both
last_reviewed: "2026-03-19"
tags:
  - Wizard
  - Provisioning
  - Operations
---

# Multi-Protocol Wizard Guide

Run:

```bash
python3 scripts/provision_client_repo.py --interactive --generate-profile
```

Unified autopipeline run (single command, no standalone chain):

```bash
python3 scripts/run_autopipeline.py --docsops-root docsops --reports-dir reports
```

Wizard includes:

1. `What's your API architecture?`
1. Multi-select protocols: `REST`, `GraphQL`, `gRPC`, `AsyncAPI`, `WebSocket`.
1. Per selected protocol:

    - source-of-truth inputs
    - mode (`api-first` / `code-first` / `hybrid`)

1. Strictness profile:

    - `standard`
    - `enterprise-strict`

1. Stack profile:

    - backend stack (`node/python/go/java/dotnet/mixed`)
    - API gateway (`none/kong/apigee/aws-api-gateway/nginx/envoy/custom`)

Generated runtime fields:

- `runtime.api_protocols`
- `runtime.api_protocol_settings`
- `runtime.api_governance.strictness`

Generated template/snippet library fields:

- `templates/protocols/graphql-reference.md`
- `templates/protocols/grpc-reference.md`
- `templates/protocols/asyncapi-reference.md`
- `templates/protocols/websocket-reference.md`
- `templates/protocols/api-protocol-snippets.md`

These are used as LLM generation anchors for consistent formatting and Stripe-style
quality across all protocol docs.

In `enterprise-strict`, multi-protocol flow exits non-zero on failed stage.

Operator model:

- pipeline runs automatically,
- client only reviews generated report packet with local LLM (`reports/LOCAL_LLM_REVIEW_PACKET.md`) and approves publish.

VeriDoc mode:

- fully automated run, no manual action required (optional post-publish review only).

RAG prep behavior:

- multi-protocol docs are normalized and enriched before indexing,
- knowledge modules are refreshed from generated docs,
- retrieval index and knowledge graph are rebuilt in the same pipeline,
- retrieval evals are executed and reported as evidence for quality controls.

## Next steps

- [Documentation index](../index.md)
