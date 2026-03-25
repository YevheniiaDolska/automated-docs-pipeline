---
title: "US Commercial One-Pager"
description: "Service offer for VeriOps: pilot, rollout, and retainer terms for US clients."
content_type: reference
product: both
last_reviewed: "2026-03-15"
tags:
  - Sales
  - Commercial
  - Operations
---

# VeriOps

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

## US Commercial One-Pager (Pilot -> Rollout -> Retainer)

### 1) What this is

VeriOps is a documentation operations system for product teams.
It reduces manual documentation work, adds quality gates, and keeps docs aligned
with code, APIs, and release changes.

### 2) Offer structure

### Implementation modes (applies to Pilot and Full Rollout)

- Default: **Bundle Delivery + Guided Install** (client installs in their environment; vendor guides and verifies).
- Add-on: **White-Glove Install** (vendor installs directly with temporary access approved by client security).

#### A. Pilot (Entry) - USD 5,000, 10-14 calendar days

Purpose: prove value fast in one real repository.

Included:

- discovery and current-state audit (docs flow + gaps + risk map),
- prepare and deliver client bundle for one repository,
- guided client-side installation and verification session,
- enable core quality gates (normalize, snippets, smoke),
- apply one policy pack + one client profile,
- run one weekly automation demo cycle,
- deliver one baseline KPI/summary report,
- 60-minute handoff session.

Not included:

- org-wide rollout across multiple repositories,
- custom module development,
- full API-first enterprise setup,
- 24/7 support.

Acceptance criteria:

- pipeline is installed by client team (or vendor if White-Glove add-on is selected) and runnable in client environment,
- at least one successful validation run,
- KPI/summary report generated,
- handoff runbook delivered and explained.

Payment:

- 50% upfront, 50% on delivery (alternative: 40/60),
- White-Glove add-on billed separately (fixed fee or time-and-materials).

#### B. Full Rollout - USD 12,000-25,000+, 3-6 weeks

Purpose: production-grade implementation and team enablement.

Included:

- advanced profile (drift + docs contract + KPI/SLA),
- API-first or hybrid flow (if needed),
- RAG/knowledge index + retrieval evals (if needed),
- CI/workflows + scheduler + policy overrides,
- team training (2-3 sessions),
- stabilization and final acceptance run.

Acceptance criteria:

- agreed gate checklist is green,
- weekly automation runs on schedule,
- client team can operate the cycle without vendor dependency.

Payment:

- 40% kickoff, 40% mid-point, 20% final sign-off,
- White-Glove install can be added as a separate line item if direct environment access is required.

#### C. Monthly Retainer (SLA)

Purpose: continuous support, optimization, and risk control.

Packages:

- Lite: USD 1,500/month (up to 4 hours, response within 48 h, monthly quality review),
- Growth: USD 3,000/month (up to 10 hours, response within 24 h, two optimization iterations/month),
- Critical: USD 6,000/month (up to 20 hours, same-day response, priority fixes, weekly KPI sync).

SLA boundaries:

- response time and resolution time are tracked separately,
- business hours and channels are explicitly defined in contract,
- overage beyond included hours billed at agreed hourly rate.

### 3) Optional deal path (recommended)

Pilot -> Full Rollout -> Retainer.

This gives the client low entry risk and clear expansion logic after proven outcomes.

### 4) Commercial notes

- This is a service engagement, not software ownership transfer.
- Toolchain remains proprietary; client receives implementation, integration, and SLA-defined outcomes.
- Final scope, timeline, and deliverables are confirmed in SOW before start.

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
