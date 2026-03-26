---
title: Smart Merge and Manual Review
description: How needs_review works for protocol test assets and where operators review
  flagged cases.
content_type: how-to
product: both
last_reviewed: '2026-03-19'
tags:
- Testing
- Operations
- API
original_author: Kroha
---

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

# Smart Merge and Manual Review

## Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.

## Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

## Where smart-merge runs

- `scripts/generate_protocol_test_assets.py`
- `reports/api-test-assets/api_test_cases.json`

## Merge rules

1. `origin=manual` cases are always preserved.
1. `customized=true` auto cases are preserved.
1. If contract signature changed, customized cases get `needs_review=true`.
1. Removed contract entities keep customized/manual cases with `needs_review=true` and `review_reason=contract_entity_removed`.
1. Non-customized auto cases are regenerated.

## Where reviewer sees required edits

Review queue is in generated JSON:

- `needs_review_count`
- `needs_review_ids`
- per-case `needs_review`, `review_reason`, `last_generated_signature`

Suggested operator flow:

1. Open `reports/api-test-assets/api_test_cases.json`.
1. Filter by `needs_review=true`.
1. Update cases and set `customized=true` for intentional overrides.
1. Re-run protocol test-asset generation.

## Next steps

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
