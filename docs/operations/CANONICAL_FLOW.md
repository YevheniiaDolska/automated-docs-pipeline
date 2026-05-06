---
title: "Canonical flow (sales + delivery)"
description: "Current canonical flow for selling, onboarding, operating, and publishing with VeriOps."
content_type: reference
product: both
last_reviewed: "2026-04-26"
tags:
  - Operations
  - Client Onboarding
  - Delivery
---

# Canonical flow (sales + delivery)

This is the current source of truth for how VeriOps is sold and operated.

## Scope summary

1. Docs-first is the default operating surface.
1. Code-first and API-first are integrated branches of the same autopipeline.
1. Multi-protocol API support includes REST, GraphQL, gRPC, AsyncAPI, and WebSocket.
1. Full implementation includes all advanced capabilities except retrieval-time RAG.
1. Full+RAG adds retrieval-time Ask AI runtime over prepared knowledge.

## Commercial model (current)

- Pilot: `$5,000` for 21 calendar days.
- Full implementation: `$15,000` one-time.
- RAG add-on: `$10,000` one-time.
- Pilot credit policy: after a paid pilot, `$5,000` is credited toward full implementation.
  - Full after pilot: `$10,000`.
  - Full+RAG after pilot: `$20,000` total.
- Retainers: `$1,500`, `$3,000`, `$6,000` monthly.

## Plan boundaries

1. Community/degraded mode: free lint defaults only.
1. Full implementation: full docs/API operations plus RAG preparation, without retrieval-time RAG.
1. Full+RAG: full stack including retrieval-time Ask AI runtime.

## Delivery modes

- Cloud.
- Hybrid.
- Strict-local (air-gapped).

In strict-local mode, local runtime path is supported (Ollama/Qwen), and external integrations can stay disabled.

## Step-by-step canonical flow

## Step 1: qualify and package

1. Confirm client operating mode (cloud, hybrid, strict-local).
1. Confirm scope (pilot, full, full+rag).
1. Confirm prerequisites and credential ownership.

## Step 2: onboard client

Preferred entry points:

```bash
python3 scripts/onboard_client.py --mode bundle-only
# or
python3 scripts/onboard_client.py --mode install-local
```

For same-machine provisioning:

```bash
python3 scripts/provision_client_repo.py --client <profile> --client-repo <path> --docsops-dir docsops --install-scheduler linux
```

## Step 3: run setup wizard in client repository

```bash
python3 docsops/scripts/setup_client_env_wizard.py
```

Wizard responsibilities:

1. Create/update `.env.docsops.local`.
1. Explain missing prerequisites.
1. Apply strict-local fallbacks when needed.
1. Bootstrap local Ollama runtime when selected by mode/profile.

## Step 4: run autopipeline

```bash
python3 scripts/run_autopipeline.py --docsops-root docsops --reports-dir reports --auto-generate
```

Weekly scheduler runs equivalent flow via `docsops/scripts/run_weekly_gap_batch.py`.

## Step 5: autopipeline execution layers

1. Gap, stale, drift, KPI/SLA, lifecycle, and quality checks.
1. Docs generation/update using templates and policy constraints.
1. API-first flow when enabled, including multi-protocol chain.
1. Knowledge preparation layer for RAG.
1. Consolidated report generation.

## Step 6: RAG preparation and runtime gates

Preparation layer (full and full+rag):

1. Do not feed raw documentation directly to AI retrieval.
1. Run knowledge preparation first: normalize and structure documentation.
1. Split documents into semantic chunks and create knowledge modules.
1. Attach module metadata for intent, audience, source/provenance, and verification timestamp.
1. Run mandatory pre-index quality gates for freshness, example correctness, coverage gaps, terminology consistency, and structural consistency.
1. Run stale-check and contradiction-check as separate controls.
1. Exclude critical conflicting modules from retrieval index automatically.
1. Build retrieval assets only after quality hardening:
   - retrieval index (`docs/assets/knowledge-retrieval-index.json`)
   - knowledge graph (`docs/assets/knowledge-graph.jsonld`)
1. For code-first repositories, build AST/code-aware index and code dependency graph:
   - `docs/assets/code-knowledge-index.json`
   - `docs/assets/code-dependency-graph.json`
   - `reports/code_knowledge_report.json`
1. Run retrieval evaluation gate before production use:
   - precision
   - recall
   - hallucination rate

Runtime layer (full+rag only):

1. Ask AI runtime uses retrieval-time RAG context only (no free-form guessing).
1. If confidence is low, runtime uses safe fallback (`low-confidence guardrail`).
1. If cited modules are in contradiction-risk set, runtime returns explicit contradiction warnings.
1. Usage and feedback loop is always logged:
   - user query
   - latency
   - cited modules
   - helpful/not-helpful feedback
1. Retrieval mode auto-routing is active (`auto|hybrid|vectorless|semantic|token`) based on query and corpus characteristics.
1. Vectorless structural retrieval is available for long, strongly structured docs.
1. Query decomposition and evidence fusion are used for complex multi-hop questions.
1. Entity-first retrieval prioritizes exact entities (for example endpoint, version, feature flag) before final ranking.
1. Graph re-rank layer reorders candidates using module relationships (`dependencies`, `tags`, `topic` links).

Why this is competitively strong:

1. Most RAG stacks optimize retrieval over whatever corpus they receive, but do not harden knowledge quality before indexing.
1. This pipeline applies pre-index quality hardening, which reduces high-confidence wrong answers.
1. It has built-in stop-controls: stale-check, contradiction-check, retrieval eval gate, and low-confidence guardrail.
1. Code intelligence extraction has fail-open safety in runtime config (`code_intelligence.fail_open=true`) to avoid blocking whole pipeline on parser edge-cases.
1. It supports regulated operation modes (`strict-local`, `on-prem`, and air-gapped variants).
1. It is a docs operations system plus controlled RAG runtime, not only a chat layer.
1. Combined vectorless + hybrid + entity-first + graph rerank improves both precise structural lookup and broad semantic retrieval:
   - vectorless path improves precision on long, structured docs,
   - decomposition + evidence fusion improves recall on multi-hop questions,
   - entity-first reduces false matches for exact technical entities,
   - graph rerank promotes logically connected modules for higher final answer coherence.

## Step 7: review, finalize, publish

1. Team reviews diffs and report outputs.
1. Finalize gate reruns lint/validation loop.
1. Review branch flow can push updates automatically.
1. Site build/publish is executed by configured target and CI/CD policy.

## About git synchronization

`git_sync` can run before weekly checks (`fetch`/`pull`) for unattended environments.

It is configured in runtime config and can be disabled for strict governance environments.

## Licensing and hardening

1. Local signed JWT validation is enforced.
1. Premium capabilities require entitlement/capability pack.
1. Anti-tamper and hardening controls apply in production profile.
1. Missing/invalid entitlements trigger degraded behavior instead of silent bypass.

## Standard artifacts

Core outputs include:

- `reports/consolidated_report.json`
- `reports/docsops_status.json`
- `docs/assets/knowledge-retrieval-index.json`
- `docs/assets/knowledge-graph.jsonld`
- `reports/retrieval_eval_report.json`
- `reports/rag_contradictions_report.json`

## Canonical references

- `docs/operations/UNIFIED_CLIENT_CONFIG.md`
- `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md`
- `docs/operations/PLAN_TIERS.md`
- `docs/operations/OPERATOR_RUNBOOK.md`
- `production-gate.md`
