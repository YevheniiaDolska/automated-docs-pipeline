---
title: "VeriDoc/VeriOps multi-protocol sales deck"
description: "Sales positioning deck covering the unified docs-ops pipeline for REST, GraphQL, gRPC, AsyncAPI, and WebSocket protocols."
content_type: reference
product: both
tags:
  - Sales
  - Multi-Protocol
  - Positioning
---

# VeriDoc/VeriOps multi-protocol sales deck

## Slide 1: Positioning

VeriDoc/VeriOps is one docs-ops pipeline for:

- REST (OpenAPI)
- GraphQL (SDL/introspection)
- gRPC (Proto/descriptor)
- AsyncAPI (event-driven)
- WebSocket (channel/message)

## Slide 2: Problem

Most docs-ops tools are REST-only.
GraphQL/gRPC/event-driven docs are often manual and inconsistent.

## Slide 3: What We Automate

Unified flow:

`ingest -> lint -> regression -> docs generation -> quality gates -> test assets -> upload -> publish`

## Slide 4: Why It Wins

- One pipeline, five API architectures.
- Protocol-aware wizard and bundles per client stack.
- Smart merge + `needs_review` queue for generated test assets.
- Enterprise strict mode with blocking gates.

## Slide 5: Operator UX (VeriOps)

Single command run:

```bash
python3 scripts/run_autopipeline.py --docsops-root docsops --reports-dir reports
```

Output:

- full reports
- local LLM review packet
- only final decision/review remains manual

## Slide 6: SaaS UX (VeriDoc)

Fully automated flow:

```bash
python3 scripts/run_autopipeline.py --docsops-root docsops --reports-dir reports --mode veridoc --skip-local-llm-packet
```

No manual operations required; optional post-publish review only.

## Slide 7: Commercial Story

- Pilot: fast proof in one repo.
- Rollout: protocol-aware production implementation.
- Retainer: SLA + continuous governance.

## Slide 8: Phase 2

Enterprise legacy module roadmap:

- SOAP/WSDL
- advanced modernization migration aids

## Next steps

- [Documentation index](../index.md)
