---
title: "Feature-to-Value Master Matrix (Exhaustive)"
description: "Exhaustive no-duplicate mapping generated from README, PIPELINE_CAPABILITIES_CATALOG, and CANONICAL_FLOW."
content_type: reference
product: both
tags:
  - Operations
  - Reference
---

# Feature-to-value master matrix (exhaustive, no duplicates)

Source set:

1. `README.md`
1. `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md`
1. `docs/operations/CANONICAL_FLOW.md`

Internal-only call prep material. Not included in documentation site navigation.

| Capability and meaning (feature language) | Marketing framing (pain -> outcome) |
| --- | --- |
| [README] Detects documentation work automatically. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Generates and updates documentation. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Validates quality and policy compliance. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] Prepares and evaluates RAG knowledge layers. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Optionally serves retrieval-time Ask AI runtime. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Runs in cloud, hybrid, or strict-local environments. | Pain: compliance constraints and egress restrictions. Outcome: secure deployment in regulated environments. |
| [README] Teams generate docs quickly. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Quality drifts after releases. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] API docs and implementation diverge. | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] AI retrieval answers from contradictory or stale sources. | Pain: outdated guidance causes operational mistakes. Outcome: freshness control and fewer incidents. |
| [README] DocsOps layer (always core): generation, validation, governance, reporting, operations. | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [README] RAG layer (optional retrieval runtime): question answering on top of prepared knowledge. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Pilot: `$5,000`, 21 calendar days. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Full implementation: `$15,000` one-time. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] RAG add-on (retrieval-time runtime): `$10,000` one-time. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Pilot credit policy: if a client buys full implementation after a paid pilot, the pilot fee is credited. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Full after pilot: `$10,000` (`$15,000 - $5,000` credit). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Full+RAG after pilot: `$20,000` total (`$10,000` full after credit + `$10,000` RAG add-on). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Retainer tiers: `$1,500`, `$3,000`, `$6,000` monthly. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Community/degraded mode: free lint defaults only. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] Full implementation: full DocsOps + RAG preparation, without retrieval-time Ask AI runtime. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Full+RAG: full DocsOps + full retrieval-time Ask AI runtime. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Markdown/content hygiene defaults (normalization + snippet checks). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Frontmatter and SEO/GEO validation (`fact_checks` path). | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] Example smoke checks (`self_checks`) for generated docs content. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Minimal weekly status outputs (`reports/consolidated_report.json` fallback, `reports/docsops_status.json`, `reports/READY_FOR_REVIEW.txt`). | Pain: updates do not reliably reach users. Outcome: controlled review and publishing flow. |
| [README] Templates included in the delivered bundle/repository remain available for manual generation flow. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] Gap detection, drift/docs-contract checks, KPI/SLA. | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [README] Glossary sync and lifecycle management. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] API-first flow and all protocol pipelines (REST/GraphQL/gRPC/AsyncAPI/WebSocket). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Knowledge extraction/index/graph/retrieval evals and retrieval-time Ask AI runtime. | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [README] Custom weekly tasks and premium integrations (for example Algolia upload, Ask AI billing runtime). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Onboard client and install bundle/config. | Pain: slow, manual setup. Outcome: repeatable rollout with lower implementation friction. |
| [README] Setup wizard prepares environment and mode-specific fallbacks. | Pain: slow, manual setup. Outcome: repeatable rollout with lower implementation friction. |
| [README] Weekly runner executes docs operations pipeline. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Consolidated report is generated. | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [README] Local LLM assistant processes prioritized tasks. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Team reviews diffs and approves. | Pain: updates do not reliably reach users. Outcome: controlled review and publishing flow. |
| [README] Finalize gate reruns checks. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] Review branch flow can commit/push automatically. | Pain: updates do not reliably reach users. Outcome: controlled review and publishing flow. |
| [README] Site build and publish run via configured targets. | Pain: updates do not reliably reach users. Outcome: controlled review and publishing flow. |
| [README] Flow is not only `git diff -> commit`. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Build/publish are integrated operational steps and are enabled by default in the current runtime profile (still configurable by client runtime settings). | Pain: updates do not reliably reach users. Outcome: controlled review and publishing flow. |
| [README] Docs-first (default operating model). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Code-first documentation updates from repository signals. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] API-first generation from planning notes/contracts. | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] Hybrid mode combining docs-first and API-first. | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] Tutorial | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] How-to | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Concept | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Reference | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Troubleshooting | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] API reference and endpoint docs. | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] Architecture, deployment, integration, authentication, and configuration guides. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Migration, upgrade, testing, error-handling, FAQ, glossary, and changelog pages. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] Admin/security/best-practices/use-case/user-guide pages. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Protocol-specific references (GraphQL, gRPC, AsyncAPI, WebSocket). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Legal templates and interactive diagram template. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] If a matching template exists, generation starts from that template. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] If no suitable template exists, a new template is created in `templates/` first by LLM policy flow. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] The document is generated only after template creation, not as ad-hoc text. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] `scripts/new_doc.py` is strict: if required template file is missing, it fails and asks to create template first. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] Common factual values are centralized in `docs/_variables.yml`. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] Generated docs use shared variables instead of hardcoded constants. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] Bundle packaging includes `docs/_variables.yml` so client-side generation stays consistent. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] Intent routing from plain-language prompt (no orchestration commands required). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Source-of-truth sync from client repository state (current codebase, contracts, and latest diffs), so generation reflects real implementation changes instead of static drafts. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Doc/protocol type inference and target path selection. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Template selection (or template creation first when missing). | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] Frontmatter creation with required metadata (`title`, `description`, `content_type`, tags, product scope). | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] Shared-variable substitution from `docs/_variables.yml`. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] File placement to correct docs section by content type. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Navigation update instructions for site config (`mkdocs.yml`/provider equivalent). | Pain: updates do not reliably reach users. Outcome: controlled review and publishing flow. |
| [README] Glossary marker sync (`sync_project_glossary.py`) to keep terminology consistent. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] Protocol pipelines for API-first requests (REST or multi-protocol entrypoints), not ad-hoc contract drafting. | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] Endpoint/server code generation with business-logic stub placeholders from contracts and planning notes. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Contract test asset generation (protocol-aware cases, coverage artifacts, and TestRail/Zephyr-ready outputs when enabled). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Weekly/autopipeline execution for quality/regression stages. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] Lint and quality gates (Vale, markdownlint, cspell, frontmatter, SEO/GEO, snippets/smoke). | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] Knowledge prep chain (`extract_knowledge_modules_from_docs.py` -> `validate_knowledge_modules.py` -> `generate_knowledge_retrieval_index.py`). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Consolidated reports and review handoff artifacts. | Pain: updates do not reliably reach users. Outcome: controlled review and publishing flow. |
| [README] Markdown docs (primary authoring and generation surface). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] OpenAPI, GraphQL SDL, Proto, AsyncAPI, and WebSocket contract files. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Knowledge modules YAML (`knowledge_modules/*.yml`) for retrieval preparation. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] JSON-LD knowledge graph artifacts. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] API test assets for TestRail/Zephyr import (`.csv`, `.json`, plus coverage reports). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Report artifacts in JSON and Markdown, plus runtime telemetry in JSONL and selected HTML reports. | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [README] RAG artifacts: retrieval index JSON, contradiction/stale reports JSON, retrieval eval reports/datasets, and runtime usage/feedback logs. | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [README] REST (OpenAPI) | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] GraphQL | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] gRPC | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] AsyncAPI | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] WebSocket | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] Contract generation/update from planning notes. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Contract validation and regression checks. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Server stub generation with business-logic placeholders (enabled by default in current API-first runtime, configurable per protocol). | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] Runtime self-verification against sandbox/live endpoints. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Protocol test assets generation. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Smart merge for customized test assets. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Optional upload exports for TestRail/Zephyr. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] The pipeline generates endpoint/server stub code with business-logic placeholders (`scripts/generate_protocol_server_stubs.py`). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] The generated contract and stubs can be wired to mock sandbox modes (`docker`, `prism`, `external`) for real Try-it usage in docs. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Playground endpoint sync can keep documentation sandbox URL aligned with active mock base URL. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] External mock auto-prepare (for example Postman) can provision/update a shared docs sandbox endpoint. | Pain: slow, manual setup. Outcome: repeatable rollout with lower implementation friction. |
| [README] Normalization. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Style lint (Vale). | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] Markdown lint. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] Spelling. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Frontmatter validation. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] SEO/GEO optimization checks. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Snippet lint and code example smoke checks. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] Knowledge module validation. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Optional diagram and multilingual example checks. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Lifecycle management (active/deprecated/removed behavior). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Glossary sync and terminology consistency. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [README] KPI/SLA gates. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] Drift and docs contract checks. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `gap_detection` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `drift_detection` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `docs_contract` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `kpi_sla` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [README] `rag_optimization` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] `code_intelligence` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `ontology_graph` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] `retrieval_evals` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `terminology_management` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `multilang_examples` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `normalization` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `snippet_lint` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] `diagram_validation` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `self_checks` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `fact_checks` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `lifecycle_management` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `knowledge_validation` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] `i18n_sync` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `release_pack` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Build/generate: docs build, knowledge index/graph build, intent experience assembly, release pack generation. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Lint/quality: vale, markdownlint, cspell, frontmatter, geo/seo, snippets, multilingual examples, diagrams. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] Validation: minimal/full validation chains, knowledge validation, protocol contract validators. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Gap detection and prioritization: code/community/search gap analysis, consolidated reporting. | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [README] KPI/SLA and governance: KPI wall, SLA evaluation, lifecycle checks, terminology sync. | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [README] API-first operations: REST and non-REST contract generation, regression checks, sandbox/self-verify, test asset generation/upload. | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] RAG prep and retrieval evaluation: module extraction/validation, retrieval index, knowledge graph, eval gates, contradiction/stale controls. | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [README] Ask AI runtime: runtime install/config, retrieval-time answering, guardrails, contradiction warnings, usage/feedback telemetry. | Pain: conflicting sources create confidently wrong answers. Outcome: earlier conflict detection and lower response-risk. |
| [README] Localization and i18n: sync, translation, multilingual quality controls. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] Audit/reporting utilities: public audit, scorecard, executive artifacts. | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [README] Onboarding/provisioning: bundle build, install-local provisioning, setup wizard, scheduler setup. | Pain: slow, manual setup. Outcome: repeatable rollout with lower implementation friction. |
| [README] Security/licensing/hardening: license gate, anti-tamper policy, capability-pack enforcement, offline renewal support. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] Catalog includes full inventory (including demo/agent commands). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Default commercial autopipeline includes non-demo capabilities according to plan gates. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] Full includes all non-demo capabilities except retrieval-time RAG runtime. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Full+RAG includes full non-demo surface including retrieval-time RAG runtime. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Extract docs into knowledge modules with metadata. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Validate module schema/consistency. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] Run stale-check (outdated content detection). | Pain: outdated guidance causes operational mistakes. Outcome: freshness control and fewer incidents. |
| [README] Run contradiction-check (conflicting content detection). | Pain: conflicting sources create confidently wrong answers. Outcome: earlier conflict detection and lower response-risk. |
| [README] Exclude critical conflicting modules from retrieval index. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Build retrieval index. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Build knowledge graph (JSON-LD). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Build AST/code-aware index and code dependency graph for code-first evidence. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Run retrieval eval gate (precision/recall/hallucination thresholds). | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [README] Ask AI runtime API + widget. | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] Hybrid retrieval with rerank and cache options. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Auto retrieval routing (`auto`, `hybrid`, `vectorless`, `semantic`, `token`). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Vectorless structural retrieval for highly structured docs. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Query decomposition for multi-hop questions. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Entity-first retrieval prefilter. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Graph rerank using module links/metadata. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Low-confidence guardrail for safe fallback answers. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Runtime contradiction warnings if citations touch critical conflict set. | Pain: conflicting sources create confidently wrong answers. Outcome: earlier conflict detection and lower response-risk. |
| [README] Usage telemetry and user feedback logging. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Indexes existing test code patterns (pytest, unittest, Allure-step ecosystems) from client repository. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Retrieves similar tests/steps and generates new tests that follow local conventions. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Validates generated test syntax and structure before output. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [README] Produces reusable test assets for API/protocol flows and supports import/export targets for TestRail and Zephyr. | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] `docsops/scripts/generate_tests_from_rag.py` (RAG-based test synthesis from existing tests). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] `scripts/generate_protocol_test_assets.py` and `scripts/generate_api_test_assets.py` (contract/protocol test assets). | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] `scripts/upload_api_test_assets.py` (optional upload flow to TestRail/Zephyr). | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] Output examples: `reports/api-test-assets/testrail_test_cases.csv`, `reports/api-test-assets/zephyr_test_cases.json`. | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [README] Quality hardening happens before indexing, not only at retrieval time. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Contradictions and stale content are actively controlled. | Pain: conflicting sources create confidently wrong answers. Outcome: earlier conflict detection and lower response-risk. |
| [README] Critical conflicts can be excluded from index automatically. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Runtime uses dynamic auto-routing across retrieval modes (`auto\|hybrid\|vectorless\|semantic\|token`) instead of fixed-mode retrieval. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Multi-hop questions are decomposed into subqueries with evidence fusion. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Entity-first prefilter improves precision on endpoint/version/flag-heavy questions. | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [README] Graph rerank layer boosts candidates through module-link propagation. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Runtime guardrails and contradiction warning propagation remain active at answer time. | Pain: conflicting sources create confidently wrong answers. Outcome: earlier conflict detection and lower response-risk. |
| [README] System collects production feedback loop signals (usage + user feedback) for ongoing tuning. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Code-first evidence is explicit: AST/code-aware chunks and code dependency graph (`imports/calls/config`) improve claim traceability from docs to code. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] Local runtime path with Ollama. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Default local base model path includes Qwen (`qwen2.5:7b`). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Setup wizard can bootstrap local Ollama installation and model pull. | Pain: slow, manual setup. Outcome: repeatable rollout with lower implementation friction. |
| [README] In local provider mode (`local`/`ollama`), external provider keys are not required. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Strict-local fallback can switch API sandbox backend from `docker` to `prism` when Docker is unavailable. | Pain: compliance constraints and egress restrictions. Outcome: secure deployment in regulated environments. |
| [README] Strict-local fallback can disable external mock preparation when strict-local requires external-off posture. | Pain: compliance constraints and egress restrictions. Outcome: secure deployment in regulated environments. |
| [README] Cloud/hybrid can use external provider integrations. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] External mock and test-management uploads are optional by policy. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Credential ownership stays on client side for enabled integrations. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] English is always enabled as default source language. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] You can add extra locales (for example `ru,de,es`). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Selected locales are saved into runtime profile and used to generate bundle `i18n.yml`. | Pain: slow, manual setup. Outcome: repeatable rollout with lower implementation friction. |
| [README] Some clients require no auto-pull behavior. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Some teams use strict branch governance. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Some environments always run on already-updated working copy. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] setup wizard asks this explicitly and writes `git_sync.enabled` based on client answer. | Pain: slow, manual setup. Outcome: repeatable rollout with lower implementation friction. |
| [README] Local signed JWT license validation. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Capability pack gating for premium surface. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Anti-tamper and production hardening controls. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Degraded community fallback when entitlement is missing. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] Offline renewal path for strict-local clients. | Pain: compliance constraints and egress restrictions. Outcome: secure deployment in regulated environments. |
| [README] `reports/consolidated_report.json` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [README] `reports/docsops_status.json` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [README] `reports/kpi-wall.json` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [README] `reports/kpi-sla-report.json` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [README] `reports/retrieval_evals_report.json` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [README] `reports/rag_contradictions_report.json` | Pain: conflicting sources create confidently wrong answers. Outcome: earlier conflict detection and lower response-risk. |
| [README] `docs/assets/knowledge-retrieval-index.json` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] `docs/assets/knowledge-graph.jsonld` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] `docs/operations/CANONICAL_FLOW.md` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `docs/operations/UNIFIED_CLIENT_CONFIG.md` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `docs/operations/PLAN_TIERS.md` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `docs/operations/OPERATOR_RUNBOOK.md` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [README] `docs/concepts/intelligent-knowledge-system.md` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [README] `production-gate.md` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [PIPELINE_CAPABILITIES_CATALOG] Operations | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Reference | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] This catalog is a full inventory of available commands. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] In commercial packaging: | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] If a capability needs external infrastructure (for example, provider credentials, external mock service, Docker runtime), setup wizard records it as a client-side prerequisite. | Pain: slow, manual setup. Outcome: repeatable rollout with lower implementation friction. |
| [PIPELINE_CAPABILITIES_CATALOG] Knowledge preparation layer (included in `full` and `full+rag`): | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] docs -> knowledge modules extraction/validation | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] retrieval index generation (`knowledge-retrieval-index.json`) | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] JSON-LD knowledge graph generation (`knowledge-graph.jsonld`) | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] retrieval evaluation gate/reporting | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [PIPELINE_CAPABILITIES_CATALOG] stale detection in docs quality loop | Pain: outdated guidance causes operational mistakes. Outcome: freshness control and fewer incidents. |
| [PIPELINE_CAPABILITIES_CATALOG] contradiction detection and critical-module exclusion from retrieval index | Pain: conflicting sources create confidently wrong answers. Outcome: earlier conflict detection and lower response-risk. |
| [PIPELINE_CAPABILITIES_CATALOG] AST/code-aware indexing for code-first repositories | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] code dependency graph extraction (`imports/calls/config deps`) | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Retrieval-time runtime layer (included in `full+rag`): | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Ask AI runtime API and widget | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] semantic retrieval (FAISS) with hybrid/rerank/HyDE/cache options | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] auto-routing retrieval mode (`auto\|hybrid\|vectorless\|semantic\|token`) | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] vectorless structural retrieval for high-structure docs and precise fact navigation | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] query decomposition (multi-hop question split into 2-3 subqueries + evidence fusion) | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] entity-first retrieval (endpoint/version/feature-flag/entity prefilter before main ranking) | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] graph rerank layer (lightweight module-link propagation on dependencies/tags/topic) | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] runtime confidence guardrail (low-confidence safe response) | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] contradiction warning propagation to client response | Pain: conflicting sources create confidently wrong answers. Outcome: earlier conflict detection and lower response-risk. |
| [PIPELINE_CAPABILITIES_CATALOG] language-aware retrieval routing (query locale -> same-locale knowledge, fallback to English) | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] usage logging and end-user feedback logging | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Better precision on structured enterprise docs without replacing hybrid retrieval. | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [PIPELINE_CAPABILITIES_CATALOG] More robust multi-hop answers by combining evidence from decomposed subqueries. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Lower false-positive relevance by prioritizing explicit entities before semantic similarity. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Stronger final ordering through graph-aware reranking over module relationships. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] The pipeline does not feed raw docs directly to AI. It first cleans and structures them (`knowledge preparation pipeline`). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Docs are split into semantic chunks with metadata: type, audience, source, and verification time (`knowledge modules`). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Before indexing, quality gates check stale content, broken examples, gaps, and terminology consistency (`quality gates`). | Pain: outdated guidance causes operational mistakes. Outcome: freshness control and fewer incidents. |
| [PIPELINE_CAPABILITIES_CATALOG] Stale and contradiction checks are separate controls: | Pain: conflicting sources create confidently wrong answers. Outcome: earlier conflict detection and lower response-risk. |
| [PIPELINE_CAPABILITIES_CATALOG] stale-check: "is this doc outdated?" | Pain: outdated guidance causes operational mistakes. Outcome: freshness control and fewer incidents. |
| [PIPELINE_CAPABILITIES_CATALOG] contradiction-check: "do docs conflict right now?" | Pain: conflicting sources create confidently wrong answers. Outcome: earlier conflict detection and lower response-risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Critically conflicting modules are excluded automatically from retrieval index (`critical-module exclusion from retrieval index`). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] After hardening, the system builds: | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] retrieval index (`knowledge-retrieval-index.json`) | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] knowledge graph (`knowledge-graph.jsonld`) | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Retrieval quality is measured before production with gate thresholds (`retrieval eval gate: precision/recall/hallucination`). | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [PIPELINE_CAPABILITIES_CATALOG] At answer time, runtime uses retrieval-time RAG only; when confidence is low, it returns a safe fallback instead of guessing (`low-confidence guardrail`). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Query language is resolved from explicit locale / `Accept-Language` / query text; retrieval uses same-locale sources when available, otherwise falls back to English. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] If cited modules are in critical contradiction set, client receives warning in response (`runtime contradiction warnings`). | Pain: conflicting sources create confidently wrong answers. Outcome: earlier conflict detection and lower response-risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Production signals are captured continuously: real questions, latency, citations, and helpful/not-helpful feedback (`usage log + feedback loop`). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Retrieval runtime auto-routes mode by query/corpus (`auto\|hybrid\|vectorless\|semantic\|token`). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Vectorless structural retrieval is used for long, high-structure corpora when it improves precision. | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [PIPELINE_CAPABILITIES_CATALOG] Complex questions can be decomposed into 2-3 subqueries, then merged through evidence fusion before final ranking. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Entity-first retrieval pre-prioritizes explicit entities (endpoint/version/feature flag/term) before semantic ranking. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Final ranking includes graph-aware reranking using module relationships (`dependencies`, `tags`, `topic` links). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] For code-first flows, AST/code-aware chunks and dependency graph are built to improve evidence grounding for documentation claims. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Many RAG products optimize retrieval over whatever docs they receive, but do not harden docs quality before indexing. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] This pipeline adds quality hardening before index build (`pre-index quality hardening`), which reduces confident wrong answers. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] It includes automatic stop-controls: stale-check, contradiction-check, retrieval eval gate, and low-confidence guardrail. | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [PIPELINE_CAPABILITIES_CATALOG] Code intelligence has fail-open safety (`code_intelligence.fail_open=true`): if extraction fails, core pipeline still completes. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] It includes multilingual hardening: locale-aware retrieval routing and locale-aware eval gates with per-locale thresholds. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [PIPELINE_CAPABILITIES_CATALOG] It supports strict-local and air-gapped operation modes for regulated clients. | Pain: compliance constraints and egress restrictions. Outcome: secure deployment in regulated environments. |
| [PIPELINE_CAPABILITIES_CATALOG] It is not only a chat widget; it is a managed docs quality + RAG operating system (`docs-ops + RAG`). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Client side: | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Provider credentials (`OPENAI/ANTHROPIC/AZURE`, `ALGOLIA`, `POSTMAN`, `TESTRAIL/ZEPHYR`) when corresponding integrations are enabled. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Runtime/runner prerequisites (`python3`, `node`, `npm`, optional `docker`). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Operator side: | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Signed `docsops/license.jwt`. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Capability pack (for premium features when required by policy). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Baseline policy/runtime defaults delivered in bundle. | Pain: slow, manual setup. Outcome: repeatable rollout with lower implementation friction. |
| [PIPELINE_CAPABILITIES_CATALOG] Strict-local fallback: | Pain: compliance constraints and egress restrictions. Outcome: secure deployment in regulated environments. |
| [PIPELINE_CAPABILITIES_CATALOG] If Docker is unavailable, use `api_first.sandbox_backend=prism`. | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] External provider credentials can stay empty when external integrations are disabled. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] id: "my-task" | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] [Documentation index](../index.md) | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Client Onboarding | Pain: slow, manual setup. Outcome: repeatable rollout with lower implementation friction. |
| [CANONICAL_FLOW] Delivery | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Docs-first is the default operating surface. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Code-first and API-first are integrated branches of the same autopipeline. | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [CANONICAL_FLOW] Multi-protocol API support includes REST, GraphQL, gRPC, AsyncAPI, and WebSocket. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Full implementation includes all advanced capabilities except retrieval-time RAG. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Full+RAG adds retrieval-time Ask AI runtime over prepared knowledge. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Pilot: `$5,000` for 21 calendar days. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] RAG add-on: `$10,000` one-time. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Pilot credit policy: after a paid pilot, `$5,000` is credited toward full implementation. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Full after pilot: `$10,000`. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Full+RAG after pilot: `$20,000` total. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Retainers: `$1,500`, `$3,000`, `$6,000` monthly. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Full implementation: full docs/API operations plus RAG preparation, without retrieval-time RAG. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Full+RAG: full stack including retrieval-time Ask AI runtime. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Cloud. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Hybrid. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Strict-local (air-gapped). | Pain: compliance constraints and egress restrictions. Outcome: secure deployment in regulated environments. |
| [CANONICAL_FLOW] Confirm client operating mode (cloud, hybrid, strict-local). | Pain: compliance constraints and egress restrictions. Outcome: secure deployment in regulated environments. |
| [CANONICAL_FLOW] Confirm scope (pilot, full, full+rag). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Confirm prerequisites and credential ownership. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Create/update `.env.docsops.local`. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Explain missing prerequisites. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Apply strict-local fallbacks when needed. | Pain: compliance constraints and egress restrictions. Outcome: secure deployment in regulated environments. |
| [CANONICAL_FLOW] Bootstrap local Ollama runtime when selected by mode/profile. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Gap, stale, drift, KPI/SLA, lifecycle, and quality checks. | Pain: outdated guidance causes operational mistakes. Outcome: freshness control and fewer incidents. |
| [CANONICAL_FLOW] Docs generation/update using templates and policy constraints. | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [CANONICAL_FLOW] API-first flow when enabled, including multi-protocol chain. | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [CANONICAL_FLOW] Knowledge preparation layer for RAG. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Consolidated report generation. | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [CANONICAL_FLOW] Do not feed raw documentation directly to AI retrieval. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Run knowledge preparation first: normalize and structure documentation. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Split documents into semantic chunks and create knowledge modules. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Attach module metadata for intent, audience, source/provenance, and verification timestamp. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Run mandatory pre-index quality gates for freshness, example correctness, coverage gaps, terminology consistency, and structural consistency. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Run stale-check and contradiction-check as separate controls. | Pain: conflicting sources create confidently wrong answers. Outcome: earlier conflict detection and lower response-risk. |
| [CANONICAL_FLOW] Exclude critical conflicting modules from retrieval index automatically. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Build retrieval assets only after quality hardening: | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [CANONICAL_FLOW] retrieval index (`docs/assets/knowledge-retrieval-index.json`) | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] knowledge graph (`docs/assets/knowledge-graph.jsonld`) | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] For code-first repositories, build AST/code-aware index and code dependency graph: | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Run retrieval evaluation gate before production use: | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [CANONICAL_FLOW] precision | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [CANONICAL_FLOW] recall | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [CANONICAL_FLOW] hallucination rate | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [CANONICAL_FLOW] Ask AI runtime uses retrieval-time RAG context only (no free-form guessing). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] If confidence is low, runtime uses safe fallback (`low-confidence guardrail`). | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] If cited modules are in contradiction-risk set, runtime returns explicit contradiction warnings. | Pain: conflicting sources create confidently wrong answers. Outcome: earlier conflict detection and lower response-risk. |
| [CANONICAL_FLOW] Usage and feedback loop is always logged: | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] user query | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] latency | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] cited modules | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] helpful/not-helpful feedback | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Retrieval mode auto-routing is active (`auto\|hybrid\|vectorless\|semantic\|token`) based on query and corpus characteristics. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Vectorless structural retrieval is available for long, strongly structured docs. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Query decomposition and evidence fusion are used for complex multi-hop questions. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Entity-first retrieval prioritizes exact entities (for example endpoint, version, feature flag) before final ranking. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Graph re-rank layer reorders candidates using module relationships (`dependencies`, `tags`, `topic` links). | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Most RAG stacks optimize retrieval over whatever corpus they receive, but do not harden knowledge quality before indexing. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] This pipeline applies pre-index quality hardening, which reduces high-confidence wrong answers. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] It has built-in stop-controls: stale-check, contradiction-check, retrieval eval gate, and low-confidence guardrail. | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [CANONICAL_FLOW] Code intelligence extraction has fail-open safety in runtime config (`code_intelligence.fail_open=true`) to avoid blocking whole pipeline on parser edge-cases. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] It supports regulated operation modes (`strict-local`, `on-prem`, and air-gapped variants). | Pain: compliance constraints and egress restrictions. Outcome: secure deployment in regulated environments. |
| [CANONICAL_FLOW] It is a docs operations system plus controlled RAG runtime, not only a chat layer. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Combined vectorless + hybrid + entity-first + graph rerank improves both precise structural lookup and broad semantic retrieval: | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] vectorless path improves precision on long, structured docs, | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [CANONICAL_FLOW] decomposition + evidence fusion improves recall on multi-hop questions, | Pain: no objective readiness signal for AI responses. Outcome: measurable go/no-go quality control before production. |
| [CANONICAL_FLOW] entity-first reduces false matches for exact technical entities, | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] graph rerank promotes logically connected modules for higher final answer coherence. | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [CANONICAL_FLOW] Team reviews diffs and report outputs. | Pain: updates do not reliably reach users. Outcome: controlled review and publishing flow. |
| [CANONICAL_FLOW] Finalize gate reruns lint/validation loop. | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [CANONICAL_FLOW] Review branch flow can push updates automatically. | Pain: updates do not reliably reach users. Outcome: controlled review and publishing flow. |
| [CANONICAL_FLOW] Site build/publish is executed by configured target and CI/CD policy. | Pain: updates do not reliably reach users. Outcome: controlled review and publishing flow. |
| [CANONICAL_FLOW] Local signed JWT validation is enforced. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Premium capabilities require entitlement/capability pack. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Anti-tamper and hardening controls apply in production profile. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [CANONICAL_FLOW] Missing/invalid entitlements trigger degraded behavior instead of silent bypass. | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `agent:claude:auto` (Agent/Demo) -> `bash scripts/claude-auto.sh` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `agent:codex:auto` (Agent/Demo) -> `bash scripts/codex-auto.sh` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api-first-demo` (API-first) -> `bash scripts/api_first_demo_live.sh` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api-first-demo:stop` (API-first) -> `bash scripts/api_first_demo_stop.sh` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api-first:demo` (API-first) -> `bash -lc 'set -e; bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010; trap "bash scripts/api_sandbox_project.sh down taskstream ./api/openapi.yaml 4010" EXIT; python3 scripts/run_api_first_flow.py --project-slug taskstream --notes demos/api-first/taskstream-planning-notes.md --spec api/openapi.yaml --spec-tree api/taskstream --docs-provider mkdocs --inject-demo-nav --verify-user-path --mock-base-url http://localhost:4010/v1 --auto-remediate --max-attempts 3'` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api-first:demo:live` (API-first) -> `bash scripts/api_first_demo_live.sh` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api-first:demo:stop` (API-first) -> `bash scripts/api_first_demo_stop.sh` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:first:flow:taskstream` (API-first) -> `python3 scripts/run_api_first_flow.py --project-slug taskstream --notes demos/api-first/taskstream-planning-notes.md --spec api/openapi.yaml --spec-tree api/taskstream --docs-provider mkdocs --inject-demo-nav --auto-remediate` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:first:v0:taskstream` (API-first) -> `python3 scripts/run_api_first_flow.py --project-slug taskstream --notes demos/api-first/taskstream-planning-notes.md --spec api/openapi.yaml --spec-tree api/taskstream --docs-provider mkdocs --auto-remediate --max-attempts 3` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:first:verify-user-path` (API-first) -> `python3 scripts/self_verify_api_user_path.py --base-url http://localhost:4010/v1` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:first:verify-user-path:prodlike` (API-first) -> `python3 scripts/self_verify_prodlike_user_path.py --base-url http://localhost:4011/v1` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:sandbox:live` (API-first) -> `bash scripts/api_sandbox_live.sh up taskstream ./api/openapi.yaml 4010` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:sandbox:live:logs` (API-first) -> `bash scripts/api_sandbox_live.sh logs taskstream ./api/openapi.yaml 4010` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:sandbox:live:status` (API-first) -> `bash scripts/api_sandbox_live.sh status taskstream ./api/openapi.yaml 4010` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:sandbox:live:stop` (API-first) -> `bash scripts/api_sandbox_live.sh down taskstream ./api/openapi.yaml 4010` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:sandbox:mock` (API-first) -> `docker compose -f docker-compose.api-sandbox.yml up -d` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:sandbox:prodlike` (API-first) -> `bash scripts/api_prodlike_project.sh` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:sandbox:prodlike:down` (API-first) -> `bash scripts/api_prodlike_project.sh down taskstream 4011` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:sandbox:prodlike:logs` (API-first) -> `bash scripts/api_prodlike_project.sh logs taskstream 4011` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:sandbox:prodlike:status` (API-first) -> `bash scripts/api_prodlike_project.sh status taskstream 4011` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:sandbox:prodlike:up` (API-first) -> `bash scripts/api_prodlike_project.sh up taskstream 4011` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:sandbox:project` (API-first) -> `bash scripts/api_sandbox_project.sh` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:sandbox:stop` (API-first) -> `docker compose -f docker-compose.api-sandbox.yml down` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:test:assets` (API-first) -> `python3 scripts/generate_api_test_assets.py --spec api/openapi.yaml --output-dir reports/api-test-assets --testrail-csv reports/api-test-assets/testrail_test_cases.csv --zephyr-json reports/api-test-assets/zephyr_test_cases.json` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `api:test:upload` (API-first) -> `python3 scripts/upload_api_test_assets.py --cases-json reports/api-test-assets/api_test_cases.json --report reports/api-test-assets/upload_report.json` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `askai:configure` (General) -> `python3 scripts/configure_ask_ai.py` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `askai:disable` (General) -> `python3 scripts/configure_ask_ai.py --disable` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `askai:enable` (General) -> `python3 scripts/configure_ask_ai.py --enable` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `askai:runtime:install` (General) -> `python3 scripts/install_ask_ai_runtime.py --target-dir .` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `askai:runtime:install:force` (General) -> `python3 scripts/install_ask_ai_runtime.py --target-dir . --force` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `askai:status` (General) -> `python3 scripts/configure_ask_ai.py --status` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `audit:executive-pdf` (General) -> `python3 scripts/generate_executive_audit_pdf.py --scorecard-json reports/audit_scorecard.json --public-audit-json reports/public_docs_audit.json --llm-summary-json reports/public_docs_audit_llm_summary.json --company-name "Client"` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `audit:public` (General) -> `python3 scripts/generate_public_docs_audit.py` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `audit:public:llm` (General) -> `python3 scripts/generate_public_docs_audit.py --llm-enabled --llm-model claude-sonnet-4-5 --llm-api-key-env-name ANTHROPIC_API_KEY` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `audit:public:llm-summary` (General) -> `python3 scripts/generate_public_docs_audit.py --llm-enabled --llm-summary-only --llm-model claude-sonnet-4-5 --llm-api-key-env-name ANTHROPIC_API_KEY` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `audit:public:wizard` (General) -> `python3 scripts/generate_public_docs_audit.py --interactive` | Pain: slow, manual setup. Outcome: repeatable rollout with lower implementation friction. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `audit:scorecard` (General) -> `python3 scripts/generate_audit_scorecard.py --docs-dir docs --reports-dir reports --spec-path api/openapi.yaml --policy-pack policy_packs/api-first.yml --glossary-path glossary.yml --stale-days 180 --auto-run-smoke --json-output reports/audit_scorecard.json --html-output reports/audit_scorecard.html` | Pain: outdated guidance causes operational mistakes. Outcome: freshness control and fewer incidents. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `badges` (General) -> `python3 scripts/generate_badge.py --json reports/kpi-wall.json --output reports` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `build` (Build/Generate) -> `python3 scripts/run_generator.py build` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `build:docusaurus` (Build/Generate) -> `npx docusaurus build` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `build:intent` (Build/Generate) -> `python3 scripts/assemble_intent_experience.py` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `build:intent:all` (Build/Generate) -> `python3 scripts/build_all_intent_experiences.py` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `build:knowledge-enrich:llm` (Build/Generate) -> `python3 scripts/enrich_knowledge_modules_semantic.py` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `build:knowledge-graph` (Build/Generate) -> `python3 scripts/generate_knowledge_graph_jsonld.py --modules-dir knowledge_modules --output docs/assets/knowledge-graph.jsonld --report reports/knowledge_graph_report.json` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `build:knowledge-index` (Build/Generate) -> `python3 scripts/generate_knowledge_retrieval_index.py` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `build:mkdocs` (Build/Generate) -> `mkdocs build --strict` | Pain: updates do not reliably reach users. Outcome: controlled review and publishing flow. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `build:rag:reindex` (Build/Generate) -> `python3 scripts/rag_reindex_lifecycle.py --repo-root . --with-embeddings --provider local` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `bundle:free-enterprise` (General) -> `python3 scripts/build_free_enterprise_bundle.py --client profiles/clients/acme.client.yml` | Pain: slow, manual setup. Outcome: repeatable rollout with lower implementation friction. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `configurator` (General) -> `python3 scripts/generate_configurator.py` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `confluence:migrate` (General) -> `python3 scripts/run_confluence_migration.py` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `consolidate` (General) -> `npm run gaps && npm run kpi-wall && npm run kpi-sla && npm run i18n:sync && npm run validate:knowledge && python3 scripts/consolidate_reports.py` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `consolidate:reports-only` (General) -> `python3 scripts/consolidate_reports.py` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `convert:to-docusaurus` (General) -> `python3 scripts/markdown_converter.py to-docusaurus docs/` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `convert:to-mkdocs` (General) -> `python3 scripts/markdown_converter.py to-mkdocs docs/` | Pain: updates do not reliably reach users. Outcome: controlled review and publishing flow. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `demo:api-first` (Agent/Demo) -> `bash scripts/api_first_demo_live.sh` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `demo:api-first:stop` (Agent/Demo) -> `bash scripts/api_first_demo_stop.sh` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `demo:claude:loop` (Agent/Demo) -> `bash scripts/claude-demo-loop.sh` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `demo:codex` (Agent/Demo) -> `bash scripts/codex-demo.sh` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `demo:codex:loop` (Agent/Demo) -> `bash scripts/codex-demo-loop.sh` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `doc:compile` (General) -> `python3 scripts/compile_doc_overview.py --docs-dir docs --reports-dir reports --modalities all` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `docs-contract` (General) -> `python3 scripts/check_docs_contract.py --base origin/main --head HEAD --json-output reports/pr_docs_contract.json` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `docs-ops:e2e` (VeriOps tests) -> `python3 scripts/test_docs_ops_e2e.py` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `docs-ops:golden` (VeriOps tests) -> `python3 scripts/test_golden_reports_and_workflows.py` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `docs-ops:test-suite` (VeriOps tests) -> `python3 -m pytest -q tests/test_autopipeline_suite.py` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `docsops:generate` (General) -> `python3 scripts/docsops_generate.py generate --mode operator --trigger always` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `docsops:generate:auto` (General) -> `python3 scripts/docsops_generate.py generate --mode operator --trigger always --auto` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `docsops:generate:policy` (General) -> `python3 scripts/docsops_generate.py generate --mode operator --trigger policy --auto` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `docsops:generate:veridoc` (General) -> `python3 scripts/docsops_generate.py generate --mode veridoc --trigger policy --auto` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `drift-check` (General) -> `python3 scripts/check_api_sdk_drift.py --base origin/main --head HEAD --json-output reports/api_sdk_drift_report.json --md-output reports/api_sdk_drift_report.md` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `eval:retrieval` (General) -> `python3 scripts/run_retrieval_evals_gate.py` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `gaps` (Gap detection) -> `python3 -m scripts.gap_detection.cli analyze` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `gaps:code` (Gap detection) -> `python3 -m scripts.gap_detection.cli code` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `gaps:community` (Gap detection) -> `python3 -m scripts.gap_detection.cli community` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `gaps:full` (Gap detection) -> `python3 -m scripts.gap_detection.cli full --generate` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `gaps:generate` (Gap detection) -> `python3 -m scripts.gap_detection.cli generate --report reports/doc_gaps_report.json` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `generate:multilang-tabs` (General) -> `python3 scripts/generate_multilang_tabs.py --paths docs templates --scope api --write` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `generate:multilang-tabs:all` (General) -> `python3 scripts/generate_multilang_tabs.py --paths docs templates --scope all --write` | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `generator:detect` (General) -> `python3 scripts/run_generator.py detect` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `generator:info` (General) -> `python3 scripts/run_generator.py info` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `glossary:sync` (General) -> `python3 scripts/sync_project_glossary.py --paths docs --glossary glossary.yml --report reports/glossary_sync_report.json --write` | Pain: inconsistent documentation standards. Outcome: consistent outputs and faster onboarding. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `i18n:migrate` (Localization) -> `python3 scripts/i18n_migrate.py` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `i18n:sync` (Localization) -> `python3 scripts/i18n_sync.py` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `i18n:translate` (Localization) -> `python3 scripts/i18n_translate.py` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `i18n:translate:all` (Localization) -> `python3 scripts/i18n_translate.py --all-missing` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `i18n:translate:stale` (Localization) -> `python3 scripts/i18n_translate.py --stale-only` | Pain: outdated guidance causes operational mistakes. Outcome: freshness control and fewer incidents. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `kpi-full` (KPI/SLA) -> `npm run kpi-wall && npm run badges` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `kpi-sla` (KPI/SLA) -> `python3 scripts/evaluate_kpi_sla.py --current reports/kpi-wall.json --policy-pack policy_packs/api-first.yml --json-output reports/kpi-sla-report.json --md-output reports/kpi-sla-report.md` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `kpi-wall` (KPI/SLA) -> `python3 scripts/generate_kpi_wall.py --docs-dir docs --reports-dir reports --stale-days 90` | Pain: outdated guidance causes operational mistakes. Outcome: freshness control and fewer incidents. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint` (Lint/Quality) -> `npm run normalize:docs:check && npm run lint:vale && npm run lint:md && npm run lint:spell && npm run lint:frontmatter && npm run lint:geo && npm run lint:knowledge && npm run lint:snippets && npm run lint:multilang` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint:diagrams` (Lint/Quality) -> `python3 scripts/validate_diagram_content.py docs templates --strict` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint:examples-smoke` (Lint/Quality) -> `python3 scripts/check_code_examples_smoke.py --paths docs templates` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint:examples-smoke:network` (Lint/Quality) -> `python3 scripts/check_code_examples_smoke.py --paths docs templates --allow-network` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint:frontmatter` (Lint/Quality) -> `python3 scripts/validate_frontmatter.py` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint:geo` (Lint/Quality) -> `python3 scripts/seo_geo_optimizer.py docs/` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint:knowledge` (Lint/Quality) -> `python3 scripts/validate_knowledge_modules.py` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint:layers` (Lint/Quality) -> `python3 scripts/doc_layers_validator.py --strict` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint:md` (Lint/Quality) -> `markdownlint docs/` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint:multilang` (Lint/Quality) -> `python3 scripts/validate_multilang_examples.py --docs-dir docs --scope api --required-languages curl,javascript,python` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint:multilang:all` (Lint/Quality) -> `python3 scripts/validate_multilang_examples.py --docs-dir docs --scope all --required-languages curl,javascript,python` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint:openapi` (Lint/Quality) -> `npx -y @stoplight/spectral-cli lint api/openapi.yaml --ruleset .spectral.yml && npx -y @redocly/cli lint api/openapi.yaml && npx -y @apidevtools/swagger-cli validate api/openapi.yaml && python3 scripts/validate_openapi_contract.py api/openapi.yaml` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint:snippets` (Lint/Quality) -> `python3 scripts/lint_code_snippets.py docs/ --strict` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint:snippets:strict` (Lint/Quality) -> `python3 scripts/lint_code_snippets.py docs/ templates/ --strict` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint:spell` (Lint/Quality) -> `cspell "docs/**/*.md" --no-must-find-files` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `lint:vale` (Lint/Quality) -> `vale docs/` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `new-doc` (General) -> `python3 scripts/new_doc.py` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `normalize:docs` (General) -> `python3 scripts/normalize_docs.py docs/` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `normalize:docs:check` (General) -> `python3 scripts/normalize_docs.py docs/ --check` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `onboard:client` (General) -> `python3 scripts/onboard_client.py` | Pain: slow, manual setup. Outcome: repeatable rollout with lower implementation friction. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `openapi:overrides` (General) -> `python3 scripts/apply_openapi_overrides.py --spec api/openapi.yaml --spec-tree api/taskstream --overrides api/overrides/openapi.manual.yml` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `openapi:regression` (General) -> `python3 scripts/check_openapi_regression.py --spec api/openapi.yaml --spec-tree api/taskstream --snapshot api/.openapi-regression.json` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `openapi:regression:update` (General) -> `python3 scripts/check_openapi_regression.py --spec api/openapi.yaml --spec-tree api/taskstream --snapshot api/.openapi-regression.json --update` | Pain: contract/code/docs drift. Outcome: faster integrations and fewer API regressions. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `prepare` (General) -> `husky install` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `release-pack` (General) -> `python3 scripts/generate_release_docs_pack.py --output reports/release-docs-pack.md` | Pain: quality is not visible or measurable. Outcome: better governance and decision speed. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `serve` (General) -> `python3 scripts/run_generator.py serve` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `serve:docusaurus` (General) -> `npx docusaurus start` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `serve:mkdocs` (General) -> `mkdocs serve` | Pain: updates do not reliably reach users. Outcome: controlled review and publishing flow. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `smoke:prod` (General) -> `python3 scripts/production_smoke.py` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `test:adapter` (General) -> `python3 -m pytest tests/test_docusaurus_adapter.py -v` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `test:all` (General) -> `python3 -m pytest -q tests` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `test:configurator` (General) -> `python3 -m pytest tests/test_gui_configurator.py -v` | Pain: manual and inconsistent operations. Outcome: standardized automation and reduced delivery risk. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `validate:full` (Validation) -> `npm run validate:minimal && npm run lint:layers && npm run lint:diagrams && npm run validate:knowledge && npm run docs-ops:e2e && npm run docs-ops:golden && npm run docs-ops:test-suite && python3 test_pipeline.py` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `validate:knowledge` (Validation) -> `npm run lint:knowledge && npm run build:intent:all && npm run build:knowledge-index && npm run build:knowledge-graph && npm run eval:retrieval` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `validate:knowledge:with-llm-enrich` (Validation) -> `npm run build:knowledge-enrich:llm && npm run validate:knowledge` | Pain: AI answers from noisy raw corpora. Outcome: more reliable retrieval and stronger answer grounding. |
| [PIPELINE_CAPABILITIES_CATALOG] Script `validate:minimal` (Validation) -> `npm run normalize:docs:check && npm run lint:md && npm run lint:frontmatter && npm run lint:geo && npm run lint:multilang && npm run lint:examples-smoke` | Pain: quality defects reach production docs. Outcome: predictable quality and lower rework. |


## Objection handling (call-ready)

| Client objection | Short response | How to prove it live |
| --- | --- | --- |
| "We already built something internally." | Great baseline. Our value is not another generator, but governed quality, retrieval reliability, and production controls. | Show hard gates, contradiction/stale controls, eval gate, and review artifacts. |
| "We can hire a technical writer for less." | A writer improves content, but does not replace automated quality gates, retrieval governance, and runtime feedback loops. | Separate content authoring from docs-ops control plane and show recurring operational savings. |
| "n8n + scripts are enough for us." | Good for MVP workflowing, not enough for production-grade answer quality guarantees. | Contrast orchestration vs quality control plane (hardening, evals, guardrails). |
| "MR/diff docs generation is enough." | Good for speed, weak for reliability at scale. | Show risks: stale/conflict drift and no objective readiness threshold without eval gate. |
| "This looks too complex to adopt." | Rollout is modular: start with Full (prep/governance), add retrieval runtime later. | Present phased rollout: pilot -> full -> full+rag. |
| "It is too expensive." | Cost is usually in repeated mistakes, support load, and rework, not in initial setup. | Convert to TCO: manual effort + incident risk + integration delays. |
| "We cannot send data to external LLMs." | Supported: strict-local/on-prem/air-gapped operation modes. | Show runtime policy and strict-local path with external integrations disabled. |
| "We do not trust RAG accuracy." | Valid concern. We use measured gates, not assumptions. | Show precision/recall/hallucination thresholds and eval reports pre-production. |
| "What if a new step fails and blocks delivery?" | Non-critical code intelligence uses fail-open policy to preserve pipeline continuity. | Show `code_intelligence.fail_open=true` behavior in gate reports. |
| "We have too much legacy and non-standard process." | The pipeline is designed for mixed realities: docs-first, code-first, API-first, and hybrid. | Show modular capabilities and selective enablement by plan/runtime. |
| "We want to avoid vendor lock-in." | Artifacts stay in your repo in open formats (md/yml/json/jsonl). | Show output artifacts and reuse without platform lock. |
| "If docs come from code, conflicts should not exist." | Conflicts also come from runbooks, policies, SLAs, and cross-team process docs. | Walk through stale/contradiction examples outside source code. |

## Next steps

- [Documentation index](../index.md)
