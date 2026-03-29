---
title: Auto-Doc Pipeline study guide
description: Learn the Auto-Doc Pipeline quickly with a simple architecture map, operating
  flow, plan mapping, and a detailed client FAQ.
content_type: reference
product: both
tags:
- Reference
- AI
last_reviewed: '2026-03-25'
original_author: Kroha
---


<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

# Auto-Doc Pipeline study guide

Auto-Doc Pipeline is a docs-first platform that also supports code-first and API-first delivery. It enables teams to generate, verify, and publish documentation, non-REST stubs, mock sandboxes, and contract tests in one smooth automation flow.

```bash
python3 scripts/run_multi_protocol_contract_flow.py \
  --runtime-config docsops/config/client_runtime.yml \
  --reports-dir reports
```

## One-minute mental model

1. Input: planning notes, contracts, codebase signals, and docs state.
1. Build: contracts, docs pages, server stubs, mock endpoints, and test assets.
1. Verify: quality gates, contract checks, smoke checks, and lifecycle checks.
1. Publish: review packet, optional approval, site build, and deployment.

## What this platform is optimized for

- Keep docs aligned with releases without manual rework.
- Support REST and non-REST APIs in one operational model.
- Let QA test endpoints from docs before full backend implementation.
- Keep enterprise-grade governance through policy packs and quality gates.

## Modes you should remember

| Mode | Primary source | Best use case |
| --- | --- | --- |
| `code-first` | Existing code/contracts | Mature product with frequent implementation change |
| `api-first` | Planning notes and contract design | New API products, contract-first delivery |
| `hybrid` | Both code and contract sources | Teams migrating from ad-hoc to governed docs ops |

## Smooth autopipeline flow (what runs automatically)

1. Run weekly baseline checks: gap detection, stale checks, drift/docs-contract checks, and KPI/SLA (as enabled).
1. Run REST API-first branch (if enabled): OpenAPI flow, sandbox resolution, overrides, regression gate, and REST test assets.
1. Run multi-protocol non-REST branch (if enabled): `run_multi_protocol_contract_flow.py` for GraphQL, gRPC, AsyncAPI, and WebSocket.
1. Auto-generate non-REST server stubs with business-logic placeholders.
1. Resolve runtime endpoints for self-verification and docs testers; in `external` mode with `external_mock.enabled=true`, auto-prepare Postman mock.
1. Run RAG/knowledge tasks: modules extraction, module validation, retrieval index, JSON-LD graph, and retrieval evals.
1. Run terminology governance: sync glossary markers into `glossary.yml`.
1. Run multi-language examples flow: generate tabs, validate tabs, and run smoke checks.
1. Run intent assembly and `custom_tasks.weekly`, then write consolidated reports.

## Non-REST capability pack (GraphQL, gRPC, AsyncAPI, WebSocket)

- Contract generation and validation run per protocol.
- Server stubs are generated under `generated/api-stubs/<protocol>/`.
- Mock sandbox endpoints are resolved before live self-verification.
- Interactive docs testers use resolved sandbox URLs.
- Contract tests are generated and merged with existing customized cases.

## Plan-level distribution (quick map)

| Capability | Basic | Pro | Enterprise |
| --- | --- | --- | --- |
| Core docs quality gates | Yes | Yes | Yes |
| REST API-first automation | No | Optional | Full |
| Non-REST autopipeline + stubs + Postman mock | No | No | Yes |
| Contract test assets + smart merge | No | Yes | Yes |
| Knowledge/RAG maintenance | No | Yes | Yes |
| Strict multi-protocol publish gating | No | No | Yes |

## Your setup steps for each client repository

Use this checklist when you onboard a new client repo.

### Step 1: collect required inputs from the client

1. Repository URL and default branch.
1. Docs root path (for example `docs/`).
1. Runtime mode to start with: `code-first`, `api-first`, or `hybrid`.
1. Plan scope (Basic, Pro, Enterprise) and modules to enable.
1. API scope: REST-only or multi-protocol (GraphQL/gRPC/AsyncAPI/WebSocket).

### Step 2: prepare profile and bundle

1. Generate or update client profile in `profiles/clients/generated/`.
1. Build the client bundle in `generated/client_bundles/<client_id>/`.
1. Verify bundle contains needed scripts and config for selected plan/modules.

### Step 3: install in client repo

1. Copy bundle as `docsops/` into the client repository.
1. Create `/.env.docsops.local` from generated template.
1. Fill required secrets and integration keys (if used).
1. Confirm git auth works for the scheduler user (`git pull` must succeed).

### Step 4: configure runtime for this client

1. Set `runtime.docs_flow.mode` (`code-first`, `api-first`, `hybrid`).
1. Enable/disable modules per purchased plan.
1. For non-REST, configure protocol blocks in runtime config.
1. For external mock mode, set `mock_base_url` and enable `external_mock` when needed.
1. For Postman auto-prepare, add required Postman env vars and workspace settings.

### Step 5: run first verification cycle

1. Run weekly flow once manually:
   `python3 docsops/scripts/run_weekly_gap_batch.py`.
1. Confirm `reports/consolidated_report.json` is generated and fresh.
1. Check multi-protocol and test-asset reports if enabled.
1. Confirm no blocking gate failures before turning on scheduler.

### Step 6: enable automation

1. Install weekly scheduler (Linux cron or Windows task).
1. Keep `git_sync.enabled=true` unless client requests otherwise.
1. Optionally enable PR auto-fix workflow.
1. Optional: enable strict publish gates for enterprise clients.

### Step 7: handoff and operating cadence

1. Share report reading routine with client reviewers.
1. Keep human step focused on review/approval, not routine doc plumbing.
1. Revisit plan scope as usage grows (Pro -> Enterprise when needed).

## Core artifacts to know by memory

- `reports/consolidated_report.json`: top-level operational report.
- `reports/multi_protocol_contract_report.json`: protocol execution summary.
- `reports/api-test-assets/api_test_cases.json`: generated contract test set.
- `reports/api-test-assets/merge_report.json`: smart-merge decisions and `needs_review_ids`.
- `generated/api-stubs/<protocol>/handlers.py`: generated server stubs.

## Detailed FAQ for potential clients

### 1) What business problem does this solve first?

It removes the release bottleneck caused by stale docs, broken API examples, and manual test asset maintenance.

### 2) Is this only an API-first product?

No. The platform is docs-first and supports `code-first`, `api-first`, and `hybrid` operations in the same runtime.

### 3) Which API protocols are supported?

REST, GraphQL, gRPC, AsyncAPI, and WebSocket.

### 4) What is generated automatically for non-REST APIs?

Contracts, protocol references, server stubs with business placeholders, mock endpoint wiring, and contract test assets.

### 5) Can we test endpoints before backend implementation is complete?

Yes. The mock sandbox flow allows early endpoint testing from documentation and contract definitions.

### 6) Is Postman mandatory for mocks?

No. External mode is provider-agnostic. Postman is the built-in first-class path for auto-prepare.

### 7) How does smart merge protect manual test work?

Manual and customized cases are preserved across generation cycles; changed signatures are flagged for targeted review.

### 8) Does this replace technical writers?

No. It removes repetitive work and leaves writers with high-value review, structure, and clarity decisions.

### 9) What do developers gain directly?

Faster contract feedback, stub scaffolding, earlier integration checks, and fewer release surprises.

### 10) What do QA teams gain directly?

Auto-generated protocol-aware test packs, earlier mock-first verification, and reduced test case drift.

### 11) How do we control quality standards?

Through policy packs, strict gates, and threshold settings in runtime configuration.

### 12) Does this support enterprise governance?

Yes. It provides auditable reports, gate outcomes, and policy-driven publish control.

### 13) How long does rollout usually take?

Pilot setup is typically quick because runtime and bundle templates are pre-structured.

### 14) How much manual work remains after rollout?

Usually review and approval work remains, not repetitive authoring and cross-file synchronization.

### 15) Can we run this inside existing CI/CD?

Yes. The flow is script-driven and supports local scheduler plus CI automation patterns.

### 16) What data should clients prepare?

Repo access, docs root, runtime config decisions, plan scope, and optional external integrations.

### 17) How is this different from a static docs generator?

It is a controlled operations pipeline, not only a renderer. It validates, remediates, merges, and governs.

### 18) What happens when a gate fails?

The pipeline emits explicit failure reports and can run remediation cycles before publish.

### 19) Can teams adopt this gradually?

Yes. Teams can start with quality gates and docs lifecycle, then enable protocol and RAG modules.

### 20) Why is this compelling commercially?

It compresses repetitive documentation and API verification work into a governed flow with measurable outputs.

## Next steps

- [Documentation index](index.md)
