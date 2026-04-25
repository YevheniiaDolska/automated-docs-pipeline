# VeriOps (Auto-Doc Pipeline)

VeriOps is an automated documentation operations pipeline for technical products.

It supports docs-first, code-first, and API-first workflows, plus optional retrieval-time RAG.

## Current commercial model

- Pilot: `$5,000` for 21 days.
- Full implementation: `$15,000` one-time.
- Optional RAG add-on: `$10,000` one-time.
- Retainers: `$1,500`, `$3,000`, `$6,000` monthly.

## Plan boundaries

- Community/degraded mode: free lint defaults only.
- Full implementation: complete autopipeline except retrieval-time RAG.
- Full+RAG: full stack including retrieval-time retrieval and Ask AI runtime enhancements.

## Core capabilities

1. Automatic docs generation and updates from real repo signals.
1. API-first generation for REST, GraphQL, gRPC, AsyncAPI, and WebSocket.
1. Quality gates and weekly operations reports.
1. Knowledge preparation pipeline for RAG-ready content.
1. Optional runtime Ask AI layer with citations, guardrails, and feedback logging.

## RAG architecture summary

1. Normalize and validate docs.
1. Extract knowledge modules with metadata.
1. Run stale check and contradiction check.
1. Exclude critical conflicting modules from retrieval index.
1. Build retrieval index and knowledge graph.
1. Run retrieval eval gates (precision, recall, hallucination).
1. Apply runtime guardrails (low confidence and contradiction warnings).
1. Capture usage and feedback loop signals.
1. Use hybrid retrieval modes, including vector and structure-aware routing where configured.

## Quick start

```bash
python3 -m pip install -r requirements.txt
npm install
python3 scripts/onboard_client.py --mode install-local
python3 docsops/scripts/setup_client_env_wizard.py
python3 scripts/run_autopipeline.py --docsops-root docsops --reports-dir reports --auto-generate
```

## Canonical docs set

1. `README.md` - product and scope overview.
1. `SETUP_GUIDE.md` - installation and provisioning.
1. `USER_GUIDE.md` - day-to-day operation.
1. `GUIDE.md` - full documentation map.

## Operations references

- `docs/operations/CANONICAL_FLOW.md`
- `docs/operations/UNIFIED_CLIENT_CONFIG.md`
- `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md`
- `docs/operations/PLAN_TIERS.md`
- `docs/operations/OPERATOR_RUNBOOK.md`

## Canonical mirror docs

- `README_SETUP.md` (canonical) -> `docsops/README_SETUP.md` (mirror)
- `POLICY_PACKS.md` (canonical) -> `docsops/POLICY_PACKS.md` (mirror)

Sync command:

```bash
python3 scripts/sync_docs_mirrors.py
```
