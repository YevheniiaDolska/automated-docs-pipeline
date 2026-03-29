---
title: Multi-Protocol Wizard Guide
description: Wizard UX for protocol-aware provisioning in VeriDoc and VeriOps.
content_type: how-to
product: both
last_reviewed: '2026-03-24'
tags:
- Wizard
- Provisioning
- Operations
original_author: Kroha
---


<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

# Multi-Protocol Wizard Guide

## Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.

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

Generated runtime also enables:

1. protocol server stub generation (`generate_server_stubs`, `stubs_output`)
1. live/mock endpoint verification gates (`self_verify_require_endpoint`, `publish_requires_live_green`)
1. external Postman mock auto-prepare when `runtime.api_first.external_mock.enabled=true`

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

Licensing note: Multi-protocol support (GraphQL, gRPC, AsyncAPI, WebSocket) requires an Enterprise license. The wizard generates the appropriate `licensing.plan` in the profile. See `docs/operations/PLAN_TIERS.md` for the full feature matrix.

## Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

## Next steps

- [Operator Runbook](OPERATOR_RUNBOOK.md) -- step-by-step retainer procedures
- [Documentation index](../index.md)

## Implementation status (2026-03-25)

This document is aligned to the current production implementation baseline.

Current baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` flows.
1. REST and non-REST protocols are supported in one automation model: REST, GraphQL, gRPC, AsyncAPI, and WebSocket.
1. Non-REST automation includes server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated into the smooth autopipeline, including Postman-supported auto-prepare mode.
1. Contract test assets are generated automatically and merged with smart-merge rules so manual/customized cases are preserved.
1. Knowledge/RAG tasks run as part of automation when enabled (module extraction, validation, retrieval index, graph, evals).
1. Plan gating is enforced by configuration and policy packs; advanced non-REST automation is reserved for higher plans.

Canonical execution order reference:

- `docs/operations/CANONICAL_FLOW.md`
- `docs/operations/UNIFIED_CLIENT_CONFIG.md`
- `README.md`

Commercial note:

- Where commercial packaging is discussed, recurring service terms (retainer/licensing) are part of the active go-to-market model.
