# VeriOps (Auto-Doc Pipeline)

VeriOps is a production documentation operations system for technical products.

It is not a drafting helper only. It is a full operational pipeline that:

1. Detects documentation work automatically.
1. Generates and updates documentation.
1. Validates quality and policy compliance.
1. Prepares and evaluates RAG knowledge layers.
1. Optionally serves retrieval-time Ask AI runtime.
1. Runs in cloud, hybrid, or strict-local environments.

## Current scope baseline (April 26, 2026)

This README describes the active implementation baseline as of April 26, 2026.

## Why this pipeline exists

Typical failure mode in documentation automation:

1. Teams generate docs quickly.
1. Quality drifts after releases.
1. API docs and implementation diverge.
1. AI retrieval answers from contradictory or stale sources.

VeriOps solves this by treating documentation as an operations system, not a one-time content task.

## Core product model

VeriOps has two layers:

1. DocsOps layer (always core): generation, validation, governance, reporting, operations.
1. RAG layer (optional retrieval runtime): question answering on top of prepared knowledge.

## Commercial packaging (current)

- Pilot: `$5,000`, 21 calendar days.
- Full implementation: `$15,000` one-time.
- RAG add-on (retrieval-time runtime): `$10,000` one-time.
- Pilot credit policy: if a client buys full implementation after a paid pilot, the pilot fee is credited.
  - Full after pilot: `$10,000` (`$15,000 - $5,000` credit).
  - Full+RAG after pilot: `$20,000` total (`$10,000` full after credit + `$10,000` RAG add-on).
- Retainer tiers: `$1,500`, `$3,000`, `$6,000` monthly.

Plan boundaries:

1. Community/degraded mode: free lint defaults only.
1. Full implementation: full DocsOps + RAG preparation, without retrieval-time Ask AI runtime.
1. Full+RAG: full DocsOps + full retrieval-time Ask AI runtime.

## High-level architecture

```text
Sources (free-form prompt/docs/code/api/planning notes)
  -> Detection + Prioritization
  -> Generation + Updates
  -> Quality + Policy Gates
  -> Knowledge Preparation (modules/index/graph/evals)
  -> Optional Ask AI runtime (retrieval-time RAG)
  -> Review/Branch/Build/Publish
```

## Community/degraded mode: exact runtime scope

When license degrades to `community`, weekly/autopipeline applies hard-disable in code.

Still works in community:

1. Markdown/content hygiene defaults (normalization + snippet checks).
1. Frontmatter and SEO/GEO validation (`fact_checks` path).
1. Example smoke checks (`self_checks`) for generated docs content.
1. Minimal weekly status outputs (`reports/consolidated_report.json` fallback, `reports/docsops_status.json`, `reports/READY_FOR_REVIEW.txt`).
1. Templates included in the delivered bundle/repository remain available for manual generation flow.

Automatically disabled in community:

1. Gap detection, drift/docs-contract checks, KPI/SLA.
1. Glossary sync and lifecycle management.
1. API-first flow and all protocol pipelines (REST/GraphQL/gRPC/AsyncAPI/WebSocket).
1. Knowledge extraction/index/graph/retrieval evals and retrieval-time Ask AI runtime.
1. Custom weekly tasks and premium integrations (for example Algolia upload, Ask AI billing runtime).

## End-to-end operating flow

1. Onboard client and install bundle/config.
1. Setup wizard prepares environment and mode-specific fallbacks.
1. Weekly runner executes docs operations pipeline.
1. Consolidated report is generated.
1. Local LLM assistant processes prioritized tasks.
1. Team reviews diffs and approves.
1. Finalize gate reruns checks.
1. Review branch flow can commit/push automatically.
1. Site build and publish run via configured targets.

Important:

- Flow is not only `git diff -> commit`.
- Build/publish are integrated operational steps and are enabled by default in the current runtime profile (still configurable by client runtime settings).

## Documentation modalities supported

1. Docs-first (default operating model).
1. Code-first documentation updates from repository signals.
1. API-first generation from planning notes/contracts.
1. Hybrid mode combining docs-first and API-first.

## Template-driven document coverage

The pipeline is template-first, not blank-prompt drafting.

Core Diataxis surfaces:

1. Tutorial
1. How-to
1. Concept
1. Reference
1. Troubleshooting

Additional production templates shipped in `templates/`:

1. API reference and endpoint docs.
1. Architecture, deployment, integration, authentication, and configuration guides.
1. Migration, upgrade, testing, error-handling, FAQ, glossary, and changelog pages.
1. Admin/security/best-practices/use-case/user-guide pages.
1. Protocol-specific references (GraphQL, gRPC, AsyncAPI, WebSocket).
1. Legal templates and interactive diagram template.

Template policy (from `AGENTS.md`):

1. If a matching template exists, generation starts from that template.
1. If no suitable template exists, a new template is created in `templates/` first by LLM policy flow.
1. The document is generated only after template creation, not as ad-hoc text.
1. `scripts/new_doc.py` is strict: if required template file is missing, it fails and asks to create template first.

Shared variables policy:

1. Common factual values are centralized in `docs/_variables.yml`.
1. Generated docs use shared variables instead of hardcoded constants.
1. Bundle packaging includes `docs/_variables.yml` so client-side generation stays consistent.

## Generation contract (why this is not simple AI drafting)

Every prompt-driven generation follows an operational chain, aligned with `AGENTS.md`:

1. Intent routing from plain-language prompt (no orchestration commands required).
1. Source-of-truth sync from client repository state (current codebase, contracts, and latest diffs), so generation reflects real implementation changes instead of static drafts.
1. Doc/protocol type inference and target path selection.
1. Template selection (or template creation first when missing).
1. Frontmatter creation with required metadata (`title`, `description`, `content_type`, tags, product scope).
1. Shared-variable substitution from `docs/_variables.yml`.
1. File placement to correct docs section by content type.
1. Navigation update instructions for site config (`mkdocs.yml`/provider equivalent).
1. Glossary marker sync (`sync_project_glossary.py`) to keep terminology consistent.
1. Protocol pipelines for API-first requests (REST or multi-protocol entrypoints), not ad-hoc contract drafting.
1. Endpoint/server code generation with business-logic stub placeholders from contracts and planning notes.
1. Contract test asset generation (protocol-aware cases, coverage artifacts, and TestRail/Zephyr-ready outputs when enabled).
1. Weekly/autopipeline execution for quality/regression stages.
1. Lint and quality gates (Vale, markdownlint, cspell, frontmatter, SEO/GEO, snippets/smoke).
1. Knowledge prep chain (`extract_knowledge_modules_from_docs.py` -> `validate_knowledge_modules.py` -> `generate_knowledge_retrieval_index.py`).
1. Consolidated reports and review handoff artifacts.

## Documentation formats and output targets

Supported source and output formats include:

1. Markdown docs (primary authoring and generation surface).
1. OpenAPI, GraphQL SDL, Proto, AsyncAPI, and WebSocket contract files.
1. Knowledge modules YAML (`knowledge_modules/*.yml`) for retrieval preparation.
1. JSON-LD knowledge graph artifacts.
1. API test assets for TestRail/Zephyr import (`.csv`, `.json`, plus coverage reports).
1. Report artifacts in JSON and Markdown, plus runtime telemetry in JSONL and selected HTML reports.
1. RAG artifacts: retrieval index JSON, contradiction/stale reports JSON, retrieval eval reports/datasets, and runtime usage/feedback logs.

Output targets are runtime-configurable. Current baseline is MkDocs with review-branch publish flow; API sandbox URL handling includes MkDocs and Docusaurus-compatible paths.

## API-first and multi-protocol implementation

Supported protocols:

1. REST (OpenAPI)
1. GraphQL
1. gRPC
1. AsyncAPI
1. WebSocket

Per protocol, pipeline supports:

1. Contract generation/update from planning notes.
1. Contract validation and regression checks.
1. Server stub generation with business-logic placeholders (enabled by default in current API-first runtime, configurable per protocol).
1. Runtime self-verification against sandbox/live endpoints.
1. Protocol test assets generation.
1. Smart merge for customized test assets.
1. Optional upload exports for TestRail/Zephyr.

API-first delivery value is not limited to docs pages:

1. The pipeline generates endpoint/server stub code with business-logic placeholders (`scripts/generate_protocol_server_stubs.py`).
1. The generated contract and stubs can be wired to mock sandbox modes (`docker`, `prism`, `external`) for real Try-it usage in docs.
1. Playground endpoint sync can keep documentation sandbox URL aligned with active mock base URL.
1. External mock auto-prepare (for example Postman) can provision/update a shared docs sandbox endpoint.

## Quality and governance gates

Pipeline quality stack includes:

1. Normalization.
1. Style lint (Vale).
1. Markdown lint.
1. Spelling.
1. Frontmatter validation.
1. SEO/GEO optimization checks.
1. Snippet lint and code example smoke checks.
1. Knowledge module validation.
1. Optional diagram and multilingual example checks.

Governance controls include:

1. Lifecycle management (active/deprecated/removed behavior).
1. Glossary sync and terminology consistency.
1. KPI/SLA gates.
1. Drift and docs contract checks.

## Module-level functionality map

Runtime modules (from active config model):

1. `gap_detection`
1. `drift_detection`
1. `docs_contract`
1. `kpi_sla`
1. `rag_optimization`
1. `code_intelligence`
1. `ontology_graph`
1. `retrieval_evals`
1. `terminology_management`
1. `multilang_examples`
1. `normalization`
1. `snippet_lint`
1. `diagram_validation`
1. `self_checks`
1. `fact_checks`
1. `lifecycle_management`
1. `knowledge_validation`
1. `i18n_sync`
1. `release_pack`

These toggles are controlled through client runtime config and plan entitlement.

## Capability coverage map (aligned with catalog)

`docs/operations/PIPELINE_CAPABILITIES_CATALOG.md` is the full command inventory.

This README maps those capabilities by operational category:

1. Build/generate: docs build, knowledge index/graph build, intent experience assembly, release pack generation.
1. Lint/quality: vale, markdownlint, cspell, frontmatter, geo/seo, snippets, multilingual examples, diagrams.
1. Validation: minimal/full validation chains, knowledge validation, protocol contract validators.
1. Gap detection and prioritization: code/community/search gap analysis, consolidated reporting.
1. KPI/SLA and governance: KPI wall, SLA evaluation, lifecycle checks, terminology sync.
1. API-first operations: REST and non-REST contract generation, regression checks, sandbox/self-verify, test asset generation/upload.
1. RAG prep and retrieval evaluation: module extraction/validation, retrieval index, knowledge graph, eval gates, contradiction/stale controls.
1. Ask AI runtime: runtime install/config, retrieval-time answering, guardrails, contradiction warnings, usage/feedback telemetry.
1. Localization and i18n: sync, translation, multilingual quality controls.
1. Audit/reporting utilities: public audit, scorecard, executive artifacts.
1. Onboarding/provisioning: bundle build, install-local provisioning, setup wizard, scheduler setup.
1. Security/licensing/hardening: license gate, anti-tamper policy, capability-pack enforcement, offline renewal support.

Important packaging rule:

1. Catalog includes full inventory (including demo/agent commands).
1. Default commercial autopipeline includes non-demo capabilities according to plan gates.
1. Full includes all non-demo capabilities except retrieval-time RAG runtime.
1. Full+RAG includes full non-demo surface including retrieval-time RAG runtime.

## RAG full implementation

VeriOps RAG is implemented in two independent but connected layers.

## Layer A: knowledge preparation (full and full+rag)

This layer prepares reliable retrieval data before any runtime answering.

1. Extract docs into knowledge modules with metadata.
1. Validate module schema/consistency.
1. Run stale-check (outdated content detection).
1. Run contradiction-check (conflicting content detection).
1. Exclude critical conflicting modules from retrieval index.
1. Build retrieval index.
1. Build knowledge graph (JSON-LD).
1. Build AST/code-aware index and code dependency graph for code-first evidence.
1. Run retrieval eval gate (precision/recall/hallucination thresholds).

Key outputs:

- `docs/assets/knowledge-retrieval-index.json`
- `docs/assets/knowledge-graph.jsonld`
- `docs/assets/code-knowledge-index.json`
- `docs/assets/code-dependency-graph.json`
- `reports/retrieval_evals_report.json`
- `reports/rag_contradictions_report.json`
- `reports/code_knowledge_report.json`

## Layer B: retrieval-time runtime (full+rag)

This layer answers questions using prepared knowledge with runtime safeguards.

1. Ask AI runtime API + widget.
1. Hybrid retrieval with rerank and cache options.
1. Auto retrieval routing (`auto`, `hybrid`, `vectorless`, `semantic`, `token`).
1. Vectorless structural retrieval for highly structured docs.
1. Query decomposition for multi-hop questions.
1. Entity-first retrieval prefilter.
1. Graph rerank using module links/metadata.
1. Low-confidence guardrail for safe fallback answers.
1. Runtime contradiction warnings if citations touch critical conflict set.
1. Usage telemetry and user feedback logging.

Runtime logs:

- `reports/ask_ai_usage.jsonl`
- `reports/ask_ai_feedback.jsonl`

## RAG-based test generation and test management exports

Beyond retrieval-time Q&A, the pipeline supports RAG-assisted test generation in project style:

1. Indexes existing test code patterns (pytest, unittest, Allure-step ecosystems) from client repository.
1. Retrieves similar tests/steps and generates new tests that follow local conventions.
1. Validates generated test syntax and structure before output.
1. Produces reusable test assets for API/protocol flows and supports import/export targets for TestRail and Zephyr.

Relevant scripts and artifacts:

1. `docsops/scripts/generate_tests_from_rag.py` (RAG-based test synthesis from existing tests).
1. `scripts/generate_protocol_test_assets.py` and `scripts/generate_api_test_assets.py` (contract/protocol test assets).
1. `scripts/upload_api_test_assets.py` (optional upload flow to TestRail/Zephyr).
1. Output examples: `reports/api-test-assets/testrail_test_cases.csv`, `reports/api-test-assets/zephyr_test_cases.json`.

## Why this RAG architecture is different

1. Quality hardening happens before indexing, not only at retrieval time.
1. Contradictions and stale content are actively controlled.
1. Critical conflicts can be excluded from index automatically.
1. Runtime uses dynamic auto-routing across retrieval modes (`auto|hybrid|vectorless|semantic|token`) instead of fixed-mode retrieval.
1. Multi-hop questions are decomposed into subqueries with evidence fusion.
1. Entity-first prefilter improves precision on endpoint/version/flag-heavy questions.
1. Graph rerank layer boosts candidates through module-link propagation.
1. Runtime guardrails and contradiction warning propagation remain active at answer time.
1. System collects production feedback loop signals (usage + user feedback) for ongoing tuning.
1. Code-first evidence is explicit: AST/code-aware chunks and code dependency graph (`imports/calls/config`) improve claim traceability from docs to code.

## Strict-local (air-gapped) implementation

Strict-local mode is first-class, not an afterthought.

Supported behavior:

1. Local runtime path with Ollama.
1. Default local base model path includes Qwen (`qwen2.5:7b`).
1. Setup wizard can bootstrap local Ollama installation and model pull.
1. In local provider mode (`local`/`ollama`), external provider keys are not required.
1. Strict-local fallback can switch API sandbox backend from `docker` to `prism` when Docker is unavailable.
1. Strict-local fallback can disable external mock preparation when strict-local requires external-off posture.

## Cloud and hybrid behavior

1. Cloud/hybrid can use external provider integrations.
1. External mock and test-management uploads are optional by policy.
1. Credential ownership stays on client side for enabled integrations.

## Setup and onboarding model

Primary entry points:

```bash
python3 scripts/onboard_client.py --mode bundle-only
python3 scripts/onboard_client.py --mode install-local
```

Client-side setup:

```bash
python3 docsops/scripts/setup_client_env_wizard.py
```

One-shot local provisioning path (same machine):

```bash
python3 scripts/provision_client_repo.py --client <profile> --client-repo <path> --docsops-dir docsops --install-scheduler linux
```

Provisioning wizard asks for documentation languages:

1. English is always enabled as default source language.
1. You can add extra locales (for example `ru,de,es`).
1. Selected locales are saved into runtime profile and used to generate bundle `i18n.yml`.

## Weekly automation runtime

Weekly local runner:

- `docsops/scripts/run_weekly_gap_batch.py`

It orchestrates detection, generation, validation, knowledge tasks, and consolidated reporting.

## About git synchronization (`git_sync`)

`git_sync` is an optional pre-weekly step that can execute `git fetch` + `git pull`.

Why optional:

1. Some clients require no auto-pull behavior.
1. Some teams use strict branch governance.
1. Some environments always run on already-updated working copy.

Where configured:

- `docsops/config/client_runtime.yml` -> `git_sync`
- setup wizard asks this explicitly and writes `git_sync.enabled` based on client answer.

Typical config:

```yaml
git_sync:
  enabled: false
  repo_path: .
  remote: origin
  branch: ""
  fetch_first: true
  rebase: true
  autostash: true
  continue_on_error: true
```

## Build and publish model

Site generator defaults to MkDocs in current baseline.

Common commands:

```bash
npm run serve:mkdocs
npm run build:mkdocs
```

Publish path depends on configured review branch and CI/CD target integration.

## Security, licensing, and hardening

1. Local signed JWT license validation.
1. Capability pack gating for premium surface.
1. Anti-tamper and production hardening controls.
1. Degraded community fallback when entitlement is missing.
1. Offline renewal path for strict-local clients.

## Key artifacts generated by pipeline

1. `reports/consolidated_report.json`
1. `reports/docsops_status.json`
1. `reports/kpi-wall.json`
1. `reports/kpi-sla-report.json`
1. `reports/retrieval_evals_report.json`
1. `reports/rag_contradictions_report.json`
1. `docs/assets/knowledge-retrieval-index.json`
1. `docs/assets/knowledge-graph.jsonld`

## Quick start

```bash
python3 -m pip install -r requirements.txt
npm install
python3 scripts/onboard_client.py --mode install-local
python3 docsops/scripts/setup_client_env_wizard.py
python3 scripts/run_autopipeline.py --docsops-root docsops --reports-dir reports --auto-generate
```

## Canonical references (deep docs)

1. `docs/operations/CANONICAL_FLOW.md`
1. `docs/operations/UNIFIED_CLIENT_CONFIG.md`
1. `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md`
1. `docs/operations/PLAN_TIERS.md`
1. `docs/operations/OPERATOR_RUNBOOK.md`
1. `docs/concepts/intelligent-knowledge-system.md`
1. `production-gate.md`

## Canonical mirror docs

- `README_SETUP.md` (canonical) -> `docsops/README_SETUP.md` (mirror)
- `POLICY_PACKS.md` (canonical) -> `docsops/POLICY_PACKS.md` (mirror)

Sync mirrors:

```bash
python3 scripts/sync_docs_mirrors.py
```
