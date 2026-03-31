---
title: "Intent experience: integrate for practitioner"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

<!-- markdownlint-disable MD001 MD007 MD024 MD025 MD031 -->

# Intent experience: integrate for practitioner

This page is assembled for the `integrate` intent and the `practitioner` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent integrate --audience practitioner --channel docs
```

## Included modules

### Multi-Protocol Wizard Guide (Part 2)

Wizard UX for protocol-aware provisioning in VeriDoc and VeriOps.

#### Multi-Protocol Wizard Guide (Part 2): Current product definition (2026-03-25)

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

### Multi-Protocol Wizard Guide (Part 6)

Wizard UX for protocol-aware provisioning in VeriDoc and VeriOps.

#### Multi-Protocol Wizard Guide (Part 6): Implementation status (2026-03-25)

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

### Operator Runbook (Retainer Operations)

Step-by-step instructions for weekly report review, client questions, new repo setup, and profile tuning.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Operator Runbook (Retainer Operations): Operator Runbook (Retainer Operations)

#### Operator Runbook (Retainer Operations): Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.

This runbook covers every retainer task an operator performs. Each procedure has exact steps, expected time, and what to look for. No programming knowledge is required for routine tasks.

### Operator Runbook (Retainer Operations) (Part 11)

Step-by-step instructions for weekly report review, client questions, new repo setup, and profile tuning.

| Question | What to enter | Notes |
| --- | --- | --- |
| Profile source | "generate from preset" or path to existing `.client.yml` | Choose "generate" for new clients |
| Preset | `small` / `startup` / `enterprise` / `pilot-evidence` | Match the client plan tier |
| Company name | Client company name | Used in reports and PDF |
| Client ID | Lowercase slug (auto-suggested from company name) | Used in filenames and license |
| Contact email | Client docs owner email | Informational |
| License plan | `pilot` / `professional` / `enterprise` | Must match the sales agreement |
| License validity | Number of days (default: 365) | Typically 365 for annual contracts |
| Client repo path | Full path to the client repository | Must exist on disk |
| Docs path | Path to docs folder in client repo (default: `docs`) | |
| API path | Path to API specs (default: `api`) | |
| SDK path | Path to SDK code (default: `sdk`) | |
| Docs flow mode | `code-first` / `api-first` / `hybrid` | `code-first` if code exists, `api-first` if designing API from scratch |
| Vale style guide | `google` / `microsoft` / `hybrid` | Google is the default |
| Output targets | `mkdocs`, `readme`, `github`, etc. | Comma-separated |
| PR auto-fix | Yes/No (default: No) | Enable if client wants automatic PR doc updates |
| API sandbox backend | `docker` / `prism` / `external` | Only asked for api-first/hybrid mode |
| Test asset upload | Yes/No | TestRail/Zephyr upload |
| Algolia integration | Yes/No | Search index |
| Ask AI integration | Yes/No | AI assistant |
| Intent weekly build | Yes/No | Intent experience pages |
| Finalize gate confirmation | Yes/No | Interactive commit confirmation |
| Advanced module toggles | Yes/No per module | If enabled, configures each module individually |
| Scheduler | `none` / `linux` / `windows` | Install weekly cron/task |

### Operator Runbook (Retainer Operations) (Part 16)

Step-by-step instructions for weekly report review, client questions, new repo setup, and profile tuning.

##### Operator Runbook (Retainer Operations) (Part 16): What the wizard configures vs what you edit manually

The interactive wizard (`python3 scripts/provision_client_repo.py --interactive --generate-profile`) configures all of these settings during initial setup:

- Preset selection (sets the baseline strictness)
- Policy pack (`minimal`, `api-first`, `monorepo`, `multi-product`, `plg`)
- Style guide (`google`, `microsoft`, `hybrid`)
- Protocol-specific thresholds (per-protocol autofix cycles, semantic checks)
- Module toggles (17 feature switches)
- SLA thresholds (via `policy_overrides`)
- All integration settings

For changes after initial setup, you have two options:

###### Operator Runbook (Retainer Operations) (Part 16): Option A: Re-run the wizard

```bash

python3 scripts/provision_client_repo.py --interactive --generate-profile

```

This regenerates the profile from scratch. Choose the new preset and adjust settings.

###### Operator Runbook (Retainer Operations) (Part 16): Option B: Edit the profile manually

Edit `profiles/clients/<client-id>.client.yml` directly.

### Operator Runbook (Retainer Operations) (Part 24)

Step-by-step instructions for weekly report review, client questions, new repo setup, and profile tuning.

#### Operator Runbook (Retainer Operations) (Part 24): Implementation status (2026-03-25)

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

### Set up a real-time webhook processing pipeline (Part 14)

Configure end-to-end webhook ingestion with HMAC verification, async queue processing, and delivery guarantees in under 15 minutes.

#### Set up a real-time webhook processing pipeline (Part 14): Explore the webhook pipeline architecture

The production webhook pipeline spans 13 components across 5 layers:

- **Clients layer:** Mobile App (2.1M users), Web Dashboard (450K DAU), and Partner API (85 integrations) generate webhook events via REST and WebSocket connections.
- **Edge layer:** CloudFlare CDN (99.99% uptime, TLS 1.3, DDoS protection) terminates connections. The Rate Limiter enforces 60 req/min per API key using a Redis-backed token bucket algorithm.
- **Verification layer:** The API Gateway routes 12K req/sec to the HMAC Validator, which completes HMAC-SHA256 signature checks in under 2 ms with timing-safe comparison and replay protection.
- **Processing layer:** The Event Router classifies payloads into 8 event types and dispatches them to the Redis-backed BullMQ Queue (at-least-once delivery, 10 concurrent workers). The Retry Engine handles exponential backoff (1 s, 2 s, 4 s, 8 s, 16 s) across 5 attempts.
- **Storage layer:** PostgreSQL handles 2 replicas, 8.5K qps with PgBouncer connection pooling and persists results. The Event Log provides 30-day retention with full-text search. Grafana Monitoring delivers real-time alerts via PagerDuty and Prometheus when error rates exceed 1%.
  PostgreSQL baseline metric: 2 replicas, 8.5K qps.

### Smart Merge and Manual Review

How needs_review works for protocol test assets and where operators review flagged cases.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Smart Merge and Manual Review: Smart Merge and Manual Review

#### Smart Merge and Manual Review: Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.

### Smart Merge and Manual Review (Part 4)

How needs_review works for protocol test assets and where operators review flagged cases.

#### Smart Merge and Manual Review (Part 4): Implementation status (2026-03-25)

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

### Configure HMAC authentication for inbound webhooks

Covers secure webhook authentication setup for docs, assistant responses, in-product hints, and automation workflows with one reusable module.

Use HMAC validation to reject spoofed webhook requests before your workflow executes. Set the shared secret in {{ env_vars.webhook_url }} settings, then verify the `X-Signature` header with SHA-256. Reject requests older than 300 seconds, and return HTTP 401 for invalid signatures.

```bash

curl -X POST "http://localhost:{{ default_webhook_port }}/webhook/order-events" \\
  -H "Content-Type: application/json" \\
  -H "X-Signature: sha256=YOUR_CALCULATED_SIGNATURE" \\
  -d '{"order_id":"ord_9482","event":"order_paid","amount":129.99}'

```

Keep replay protection enabled, rotate the secret every 90 days, and monitor 401 spikes for abuse detection.

## Next steps

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`
