---
title: Pipeline Capabilities Catalog
description: Generated catalog of available pipeline commands, templates, policy packs,
  and assets for client configuration.
content_type: reference
product: both
tags:
- Operations
- Reference
last_reviewed: '2026-03-24'
original_author: Developer
---

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->


# Pipeline Capabilities Catalog

## Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.


This catalog has two layers:

1. npm script entry points (from `package.json`)
1. direct CLI entry points in `scripts/*.py` that are used by provisioning/operator flows and are not exposed as npm commands

Non-script concepts (policy semantics, sales packaging, pilot/full scope) are documented in ops guides.

Use this catalog with `runtime.custom_tasks.weekly` in client profiles to enable any capability.


## Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

## How to enable any capability for a client

```yaml
runtime:
  custom_tasks:
    weekly:
      - id: "my-task"
        enabled: true
        command: "npm run <script-name>"
        continue_on_error: true
```

| Script | Category | Command |
| --- | --- | --- |
| `agent:claude:auto` | Agent/Demo | `bash scripts/claude-auto.sh` |
| `agent:codex:auto` | Agent/Demo | `bash scripts/codex-auto.sh` |
| `api-first-demo` | API-first | `bash scripts/api_first_demo_live.sh` |
| `api-first-demo:stop` | API-first | `bash scripts/api_first_demo_stop.sh` |
| `api-first:demo` | API-first | `bash -lc 'set -e; API_SANDBOX_EXTERNAL_BASE_URL=\"https://<your-real-public-mock-url>/v1\" bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010 external; python3 scripts/run_api_first_flow.py --project-slug taskstream --notes demos/api-first/taskstream-planning-notes.md --spec api/openapi.yaml --spec-tree api/taskstream --docs-provider mkdocs --inject-demo-nav --verify-user-path --mock-base-url https://<your-real-public-mock-url>/v1 --generate-test-assets --upload-test-assets --sync-playground-endpoint --auto-remediate --max-attempts 3'` |
| `api-first:demo:live` | API-first | `bash scripts/api_first_demo_live.sh` |
| `api-first:demo:stop` | API-first | `bash scripts/api_first_demo_stop.sh` |
| `api:first:flow:taskstream` | API-first | `python3 scripts/run_api_first_flow.py --project-slug taskstream --notes demos/api-first/taskstream-planning-notes.md --spec api/openapi.yaml --spec-tree api/taskstream --docs-provider mkdocs --inject-demo-nav --auto-remediate` |
| `api:first:v0:taskstream` | API-first | `python3 scripts/run_api_first_flow.py --project-slug taskstream --notes demos/api-first/taskstream-planning-notes.md --spec api/openapi.yaml --spec-tree api/taskstream --docs-provider mkdocs --auto-remediate --max-attempts 3` |
| `api:first:verify-user-path` | API-first | `python3 scripts/self_verify_api_user_path.py --base-url https://<your-real-public-mock-url>/v1` |
| `api:first:verify-user-path:prodlike` | API-first | `python3 scripts/self_verify_prodlike_user_path.py --base-url http://localhost:4011/v1` |
| `api:test:assets` | API-first | `python3 scripts/generate_api_test_assets.py --spec api/openapi.yaml --output-dir reports/api-test-assets --testrail-csv reports/api-test-assets/testrail_test_cases.csv --zephyr-json reports/api-test-assets/zephyr_test_cases.json` |
| `api:test:upload` | API-first | `python3 scripts/upload_api_test_assets.py --cases-json reports/api-test-assets/api_test_cases.json --report reports/api-test-assets/upload_report.json` |
| `audit:public` | Audit | `python3 scripts/generate_public_docs_audit.py` |
| `audit:public:wizard` | Audit | `python3 scripts/generate_public_docs_audit.py --interactive` |
| `audit:public:llm` | Audit | `python3 scripts/generate_public_docs_audit.py --llm-enabled --llm-model claude-sonnet-4-5` |
| `audit:public:llm-summary` | Audit | `python3 scripts/generate_public_docs_audit.py --llm-enabled --llm-summary-only --llm-model claude-sonnet-4-5` |
| `audit:executive-pdf` | Audit | `python3 scripts/generate_executive_audit_pdf.py --scorecard-json reports/audit_scorecard.json --public-audit-json reports/public_docs_audit.json --company-name "Client"` |
| `audit:scorecard` | Audit | `python3 scripts/generate_audit_scorecard.py --docs-dir docs --reports-dir reports --spec-path api/openapi.yaml --policy-pack policy_packs/api-first.yml --glossary-path glossary.yml --stale-days 180 --auto-run-smoke --json-output reports/audit_scorecard.json --html-output reports/audit_scorecard.html` |
| `api:sandbox:live` | API-first | `bash scripts/api_sandbox_live.sh up taskstream ./api/openapi.yaml 4010` |
| `api:sandbox:live:logs` | API-first | `bash scripts/api_sandbox_live.sh logs taskstream ./api/openapi.yaml 4010` |
| `api:sandbox:live:status` | API-first | `bash scripts/api_sandbox_live.sh status taskstream ./api/openapi.yaml 4010` |
| `api:sandbox:live:stop` | API-first | `bash scripts/api_sandbox_live.sh down taskstream ./api/openapi.yaml 4010` |
| `api:sandbox:mock` | API-first | `docker compose -f docker-compose.api-sandbox.yml up -d` |
| `api:sandbox:prodlike` | API-first | `bash scripts/api_prodlike_project.sh` |
| `api:sandbox:prodlike:down` | API-first | `bash scripts/api_prodlike_project.sh down taskstream 4011` |
| `api:sandbox:prodlike:logs` | API-first | `bash scripts/api_prodlike_project.sh logs taskstream 4011` |
| `api:sandbox:prodlike:status` | API-first | `bash scripts/api_prodlike_project.sh status taskstream 4011` |
| `api:sandbox:prodlike:up` | API-first | `bash scripts/api_prodlike_project.sh up taskstream 4011` |
| `api:sandbox:project` | API-first | `bash scripts/api_sandbox_project.sh` |
| `api:sandbox:stop` | API-first | `docker compose -f docker-compose.api-sandbox.yml down` |
| `askai:configure` | General | `python3 scripts/configure_ask_ai.py` |
| `askai:disable` | General | `python3 scripts/configure_ask_ai.py --disable` |
| `askai:enable` | General | `python3 scripts/configure_ask_ai.py --enable` |
| `askai:runtime:install` | General | `python3 scripts/install_ask_ai_runtime.py --target-dir .` |
| `askai:runtime:install:force` | General | `python3 scripts/install_ask_ai_runtime.py --target-dir . --force` |
| `askai:status` | General | `python3 scripts/configure_ask_ai.py --status` |
| `badges` | General | `python3 scripts/generate_badge.py --json reports/kpi-wall.json --output reports` |
| `build` | Build/Generate | `python3 scripts/run_generator.py build` |
| `build:docusaurus` | Build/Generate | `npx docusaurus build` |
| `build:intent` | Build/Generate | `python3 scripts/assemble_intent_experience.py` |
| `build:intent:all` | Build/Generate | `python3 scripts/build_all_intent_experiences.py` |
| `build:knowledge-graph` | Build/Generate | `python3 scripts/generate_knowledge_graph_jsonld.py --modules-dir knowledge_modules --output docs/assets/knowledge-graph.jsonld --report reports/knowledge_graph_report.json` |
| `build:knowledge-index` | Build/Generate | `python3 scripts/generate_knowledge_retrieval_index.py` |
| `build:mkdocs` | Build/Generate | `mkdocs build --strict` |
| `configurator` | General | `python3 scripts/generate_configurator.py` |
| `consolidate` | General | `npm run gaps && npm run kpi-wall && npm run kpi-sla && npm run i18n:sync && npm run validate:knowledge && python3 scripts/consolidate_reports.py` |
| `consolidate:reports-only` | General | `python3 scripts/consolidate_reports.py` |
| `convert:to-docusaurus` | General | `python3 scripts/markdown_converter.py to-docusaurus docs/` |
| `convert:to-mkdocs` | General | `python3 scripts/markdown_converter.py to-mkdocs docs/` |
| `demo:api-first` | Agent/Demo | `bash scripts/api_first_demo_live.sh` |
| `demo:api-first:stop` | Agent/Demo | `bash scripts/api_first_demo_stop.sh` |
| `demo:claude:loop` | Agent/Demo | `bash scripts/claude-demo-loop.sh` |
| `demo:codex` | Agent/Demo | `bash scripts/codex-demo.sh` |
| `demo:codex:loop` | Agent/Demo | `bash scripts/codex-demo-loop.sh` |
| `docs-contract` | General | `python3 scripts/check_docs_contract.py --base origin/main --head HEAD --json-output reports/pr_docs_contract.json` |
| `docs-ops:e2e` | VeriOps tests | `python3 scripts/test_docs_ops_e2e.py` |
| `docs-ops:golden` | VeriOps tests | `python3 scripts/test_golden_reports_and_workflows.py` |
| `docs-ops:test-suite` | VeriOps tests | `python3 -m pytest -q tests/test_autopipeline_suite.py` |
| `drift-check` | General | `python3 scripts/check_api_sdk_drift.py --base origin/main --head HEAD --json-output reports/api_sdk_drift_report.json --md-output reports/api_sdk_drift_report.md` |
| `eval:retrieval` | General | `python3 scripts/run_retrieval_evals.py --index docs/assets/knowledge-retrieval-index.json --auto-generate-dataset --dataset-out reports/retrieval_eval_dataset.generated.yml --report reports/retrieval_evals_report.json --top-k 3 --min-precision 0.5 --min-recall 0.5 --max-hallucination-rate 0.5` |
| `gaps` | Gap detection | `python3 -m scripts.gap_detection.cli analyze` |
| `gaps:code` | Gap detection | `python3 -m scripts.gap_detection.cli code` |
| `gaps:community` | Gap detection | `python3 -m scripts.gap_detection.cli community` |
| `gaps:full` | Gap detection | `python3 -m scripts.gap_detection.cli full --generate` |
| `gaps:generate` | Gap detection | `python3 -m scripts.gap_detection.cli generate --report reports/doc_gaps_report.json` |
| `generate:multilang-tabs` | General | `python3 scripts/generate_multilang_tabs.py --paths docs templates --scope api --write` |
| `generate:multilang-tabs:all` | General | `python3 scripts/generate_multilang_tabs.py --paths docs templates --scope all --write` |
| `generator:detect` | General | `python3 scripts/run_generator.py detect` |
| `generator:info` | General | `python3 scripts/run_generator.py info` |
| `glossary:sync` | General | `python3 scripts/sync_project_glossary.py --paths docs --glossary glossary.yml --report reports/glossary_sync_report.json --write` |
| `i18n:migrate` | Localization | `python3 scripts/i18n_migrate.py` |
| `i18n:sync` | Localization | `python3 scripts/i18n_sync.py` |
| `i18n:translate` | Localization | `python3 scripts/i18n_translate.py` |
| `i18n:translate:all` | Localization | `python3 scripts/i18n_translate.py --all-missing` |
| `i18n:translate:stale` | Localization | `python3 scripts/i18n_translate.py --stale-only` |
| `kpi-full` | KPI/SLA | `npm run kpi-wall && npm run badges` |
| `kpi-sla` | KPI/SLA | `python3 scripts/evaluate_kpi_sla.py --current reports/kpi-wall.json --policy-pack policy_packs/api-first.yml --json-output reports/kpi-sla-report.json --md-output reports/kpi-sla-report.md` |
| `kpi-wall` | KPI/SLA | `python3 scripts/generate_kpi_wall.py --docs-dir docs --reports-dir reports --stale-days 90` |
| `lint` | Lint/Quality | `npm run normalize:docs:check && npm run lint:vale && npm run lint:md && npm run lint:spell && npm run lint:frontmatter && npm run lint:geo && npm run lint:knowledge && npm run lint:snippets && npm run lint:multilang` |
| `lint:diagrams` | Lint/Quality | `python3 scripts/validate_diagram_content.py docs templates` |
| `lint:examples-smoke` | Lint/Quality | `python3 scripts/check_code_examples_smoke.py --paths docs templates` |
| `lint:examples-smoke:network` | Lint/Quality | `python3 scripts/check_code_examples_smoke.py --paths docs templates --allow-network` |
| `lint:frontmatter` | Lint/Quality | `python3 scripts/validate_frontmatter.py` |
| `lint:geo` | Lint/Quality | `python3 scripts/seo_geo_optimizer.py docs/` |
| `lint:knowledge` | Lint/Quality | `python3 scripts/validate_knowledge_modules.py` |
| `lint:layers` | Lint/Quality | `python3 scripts/doc_layers_validator.py` |
| `lint:md` | Lint/Quality | `markdownlint docs/` |
| `lint:multilang` | Lint/Quality | `python3 scripts/validate_multilang_examples.py --docs-dir docs --scope api --required-languages curl,javascript,python` |
| `lint:multilang:all` | Lint/Quality | `python3 scripts/validate_multilang_examples.py --docs-dir docs --scope all --required-languages curl,javascript,python` |
| `lint:openapi` | Lint/Quality | `npx -y @stoplight/spectral-cli lint api/openapi.yaml --ruleset .spectral.yml && npx -y @redocly/cli lint api/openapi.yaml && npx -y @apidevtools/swagger-cli validate api/openapi.yaml && python3 scripts/validate_openapi_contract.py api/openapi.yaml` |
| `lint:snippets` | Lint/Quality | `python3 scripts/lint_code_snippets.py docs/` |
| `lint:snippets:strict` | Lint/Quality | `python3 scripts/lint_code_snippets.py docs/ templates/ --strict` |
| `lint:spell` | Lint/Quality | `cspell "docs/**/*.md" --no-must-find-files` |
| `lint:vale` | Lint/Quality | `vale docs/` |
| `new-doc` | General | `python3 scripts/new_doc.py` |
| `normalize:docs` | General | `python3 scripts/normalize_docs.py docs/` |
| `normalize:docs:check` | General | `python3 scripts/normalize_docs.py docs/ --check` |
| `onboard:client` | General | `python3 scripts/onboard_client.py` |
| `openapi:overrides` | General | `python3 scripts/apply_openapi_overrides.py --spec api/openapi.yaml --spec-tree api/taskstream --overrides api/overrides/openapi.manual.yml` |
| `openapi:regression` | General | `python3 scripts/check_openapi_regression.py --spec api/openapi.yaml --spec-tree api/taskstream --snapshot api/.openapi-regression.json` |
| `openapi:regression:update` | General | `python3 scripts/check_openapi_regression.py --spec api/openapi.yaml --spec-tree api/taskstream --snapshot api/.openapi-regression.json --update` |
| `prepare` | General | `husky install` |
| `release-pack` | General | `python3 scripts/generate_release_docs_pack.py --output reports/release-docs-pack.md` |
| `serve` | General | `python3 scripts/run_generator.py serve` |
| `serve:docusaurus` | General | `npx docusaurus start` |
| `serve:mkdocs` | General | `mkdocs serve` |
| `test:adapter` | General | `python3 -m pytest tests/test_docusaurus_adapter.py -v` |
| `test:all` | General | `python3 -m pytest -q tests` |
| `test:configurator` | General | `python3 -m pytest tests/test_gui_configurator.py -v` |
| `validate:full` | Validation | `npm run validate:minimal && npm run lint:layers && npm run lint:diagrams && npm run validate:knowledge && npm run docs-ops:e2e && npm run docs-ops:golden && npm run docs-ops:test-suite && python3 test_pipeline.py` |
| `validate:knowledge` | Validation | `npm run lint:knowledge && npm run build:intent:all && npm run build:knowledge-index && npm run build:knowledge-graph && npm run eval:retrieval` |
| `validate:minimal` | Validation | `npm run normalize:docs:check && npm run lint:md && npm run lint:frontmatter && npm run lint:geo && npm run lint:multilang && npm run lint:examples-smoke` |

## Direct CLI entry points (not exposed as npm scripts)

These are part of the current implementation and are invoked directly by operator/provisioning/weekly flows.

| Script | Purpose |
| --- | --- |
| `scripts/build_client_bundle.py` | Build client-specific bundle in `generated/client_bundles/<client_id>/`. |
| `scripts/provision_client_repo.py` | One-shot install into client repo (bundle copy, config/policy, env checklist, scheduler install). |
| `scripts/init_pipeline.py` | Bootstrap pipeline directly from source into another repo (self-install path). |
| `scripts/run_weekly_gap_batch.py` | Main weekly local runner (gaps/stale/kpi/api-first/modules/custom tasks/consolidation). |
| `scripts/auto_fix_pr_docs.py` | PR branch docs autofix helper for optional GitHub workflow. |
| `scripts/ensure_external_mock_server.py` | Resolve/create external mock endpoint (Postman-supported flow). |
| `scripts/extract_knowledge_modules_from_docs.py` | Auto-extract knowledge modules from docs markdown. |
| `scripts/gap_detector.py` | Legacy/direct gap detector entry used in some compatibility paths. |
| `scripts/generate_docusaurus_config.py` | Generate/update Docusaurus config in adapter flows. |
| `scripts/generate_facets_index.py` | Build faceted search index artifacts. |
| `scripts/generate_fastapi_stubs_from_openapi.py` | Generate FastAPI stubs from OpenAPI. |
| `scripts/generate_openapi_from_planning_notes.py` | Generate OpenAPI root/tree from planning notes. |
| `scripts/generate_protocol_server_stubs.py` | Generate protocol server stubs with business-logic placeholders for REST, GraphQL, gRPC, AsyncAPI, and WebSocket. |
| `scripts/generate_pipeline_capabilities_catalog.py` | Regenerate this capabilities catalog file. |
| `scripts/lifecycle_manager.py` | Lifecycle scan/report/redirect guidance generation. |
| `scripts/manage_demo_nav.py` | Demo nav injection/removal helper. |
| `scripts/pilot_analysis.py` | Pilot analysis/report helper. |
| `scripts/preprocess_variables.py` | Variables pre-processing helper for docs generation flows. |
| `scripts/upload_to_algolia.py` | Upload generated search records to Algolia. |
| `scripts/validate_pr_dod.py` | DoD validation helper for PR workflows. |
| `scripts/run_multi_protocol_contract_flow.py` | Unified orchestrator for all 5 protocol documentation flows (REST, GraphQL, gRPC, AsyncAPI, WebSocket). Runs 9 stages: ingest, contract validation, server stub generation, lint, regression, docs generation, quality gates, test assets, publish. |
| `scripts/generate_protocol_contract_from_planning_notes.py` | Generate protocol contracts (GraphQL SDL, Proto3, AsyncAPI YAML, WebSocket YAML) from planning notes markdown. |
| `scripts/generate_protocol_docs.py` | Auto-generate reference documentation from protocol contracts using protocol-specific templates. |
| `scripts/generate_protocol_test_assets.py` | Generate protocol-aware test cases with signature-based smart merge. Outputs JSON, TestRail CSV, Zephyr JSON, test matrix, and fuzz scenarios. |
| `scripts/run_protocol_self_verify.py` | Runtime validation against live/mock endpoints: GraphQL introspection, gRPC invocation, AsyncAPI event publish, WebSocket connection and message routing. |
| `scripts/validate_graphql_contract.py` | GraphQL SDL contract validation (syntax, semantics, operation types). |
| `scripts/validate_proto_contract.py` | Proto3 contract validation (syntax, service definitions, RPC methods). |
| `scripts/validate_asyncapi_contract.py` | AsyncAPI contract validation (channels, schemas, delivery guarantees). |
| `scripts/validate_websocket_contract.py` | WebSocket channel contract validation (message schemas, connection lifecycle). |
| `scripts/generate_public_docs_audit.py` | Public documentation site auditor: crawls live sites, evaluates broken links, SEO/GEO, API coverage, code examples, freshness. Supports interactive wizard and LLM-powered expert analysis. |
| `scripts/generate_audit_scorecard.py` | Comprehensive audit scorecard generator combining docs quality, API coverage, code examples, glossary health, and policy compliance into a single score. |
| `scripts/generate_executive_audit_pdf.py` | Consulting-grade executive PDF report from audit scorecard and public docs audit results. Includes score gauges, risk matrices, financial impact tables, and methodology appendix. |
| `scripts/generate_embeddings.py` | Generate FAISS vector index from knowledge modules using `text-embedding-3-small` (1536 dimensions). Builds `retrieval.faiss` and `retrieval-metadata.json`. |

## Multi-protocol contract pipeline

The pipeline supports five API protocols with a unified orchestrator (`run_multi_protocol_contract_flow.py`). Each protocol has its own contract format, validator, reference template, test generator, and sandbox fallback.

| Protocol | Contract format | Validator | Sandbox fallback |
| --- | --- | --- | --- |
| REST | OpenAPI 3.0 YAML | `validate_openapi_contract.py` + Spectral + Redocly | Prism / Postman mock server |
| GraphQL | SDL (`.graphql`) | `validate_graphql_contract.py` | `postman-echo.com/post` |
| gRPC | Proto3 (`.proto`) | `validate_proto_contract.py` | `postman-echo.com/post` (JSON-over-HTTP) |
| AsyncAPI | AsyncAPI 2.6 YAML | `validate_asyncapi_contract.py` | `postman-echo.com/post` + `echo.websocket.events` |
| WebSocket | Channel YAML | `validate_websocket_contract.py` | `echo.websocket.events` |

**9 pipeline stages per protocol:** ingest, contract validation, server stub generation, lint, regression detection, docs generation, quality gates (frontmatter + snippet lint + self-verification), test assets generation with smart merge, publish.

**Autofix cycle:** up to 3 auto-remediation attempts per protocol. Regenerates docs and retries semantic consistency checks on failure.

**Contract generation from planning notes:** `generate_protocol_contract_from_planning_notes.py` generates protocol specs from markdown planning notes.

**Self-verification:** `run_protocol_self_verify.py` validates generated docs against live/mock endpoints (GraphQL introspection, gRPC method invocation, AsyncAPI event publish, WebSocket connection routing).

## Test assets generation and smart merge

`generate_protocol_test_assets.py` generates protocol-aware test cases for all five protocols with signature-based smart merge to preserve custom and manual test cases across contract changes.

**Test categories per protocol:**

| Protocol | Categories |
| --- | --- |
| REST | CRUD happy paths, validation errors, auth, rate limiting, pagination |
| GraphQL | Query/mutation/subscription happy path, invalid input, auth, injection, latency |
| gRPC | Unary/streaming positive, status codes, deadline/retry, authorization, latency SLO |
| AsyncAPI | Publish validation, invalid payload, ordering/idempotency, security, throughput |
| WebSocket | Connection/auth, message envelope, reconnect, security, concurrency |

**Output formats:** `api_test_cases.json`, `testrail_test_cases.csv` (TestRail), `zephyr_test_cases.json` (Zephyr Scale), `test_matrix.json`, `fuzz_scenarios.json`.

**Smart merge rules:** auto-generated cases are replaced on contract change; customized cases (`customized: true`) are preserved and flagged `needs_review: true` when the contract signature changes; manual cases (`origin: "manual"`) are never overwritten.

**TestRail/Zephyr upload:** `upload_api_test_assets.py` pushes generated cases to TestRail or Zephyr Scale. The `needs_review` flag propagates to both platforms so QA teams can triage stale custom cases.

## Quality checks (32 automated)

The pipeline enforces 32 automated checks on every documentation page across four categories:

| Category | Count | What they verify |
| --- | --- | --- |
| GEO checks | 8 | LLM and AI search optimization: meta descriptions, first paragraph length, heading hierarchy, fact density |
| SEO checks | 14 | Traditional search optimization: title length, URL depth, internal links, image alt text, structured data |
| Style checks | 6 | American English, active voice, no weasel words, no contractions, second person, present tense |
| Contract checks | 4 | Schema validation, regression detection, snippet lint, self-verification against endpoints |

## RAG retrieval pipeline

The pipeline generates a knowledge retrieval layer with six advanced features:

| Feature | Description |
| --- | --- |
| Token-aware chunking | Splits modules into 750-token chunks with 100-token overlap (`cl100k_base`) |
| Hybrid search (RRF) | Fuses semantic (FAISS) and token-overlap rankings with Reciprocal Rank Fusion (k=60) |
| HyDE query expansion | Generates hypothetical doc passage via LLM before embedding for better retrieval on vague queries |
| Cross-encoder reranking | Rescores top 20 candidates with `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Embedding cache | In-memory LRU cache (TTL 3,600 seconds, max 512 entries) for query embeddings |
| Multi-mode evaluation | Compares token, semantic, hybrid, and hybrid+rerank modes across curated queries |

**Pipeline scripts:**

1. `extract_knowledge_modules_from_docs.py` -- auto-chunk docs into knowledge modules
1. `validate_knowledge_modules.py` -- schema validation, duplicate ID detection, cycle check
1. `generate_knowledge_retrieval_index.py` -- JSON index for Algolia + FAISS input
1. `generate_embeddings.py` -- FAISS vector index (`text-embedding-3-small`, 1536 dims)
1. `generate_knowledge_graph_jsonld.py` -- JSON-LD knowledge graph
1. `run_retrieval_evals.py` -- precision@k, recall@k, hallucination rate evaluation

## Public docs auditor and executive PDF

The public docs auditor crawls live documentation sites and generates a comprehensive quality assessment.

**Audit modes:**

| Mode | Command | Description |
| --- | --- | --- |
| Basic | `npm run audit:public` | Crawl + evaluate (no LLM) |
| Interactive wizard | `npm run audit:public:wizard` | Step-by-step guided audit |
| LLM-powered | `npm run audit:public:llm` | Full expert analysis with Claude |
| LLM summary only | `npm run audit:public:llm-summary` | Quick LLM summary without full crawl |
| Executive PDF | `npm run audit:executive-pdf` | Consulting-grade PDF from audit results |
| Scorecard | `npm run audit:scorecard` | Comprehensive scoring across all quality dimensions |

**Executive PDF contents:** cover page with headline findings, executive summary with score gauge and grade, per-site metrics table, board-level KPI bars with financial impact, risk matrix with priority actions, expert analysis (LLM or data-driven fallback), methodology appendix, evidence appendix.

**Audit scorecard dimensions:** docs quality (SEO/GEO), API coverage, code example reliability, glossary health, content freshness, policy compliance.

## API-first external sandbox note

For public web playground usage, prefer `external` sandbox mode and a public HTTPS mock URL with CORS:

```bash
API_FIRST_DEMO_SANDBOX_BACKEND=external \
API_FIRST_DEMO_MOCK_BASE_URL="https://<your-real-public-mock-url>/v1" \
bash scripts/api_first_demo_live.sh
```

The pipeline is provider-agnostic. You can use Postman Mock Servers, Stoplight-hosted Prism, Mockoon Cloud, or your own hosted Prism-compatible endpoint.

For Postman auto-prepare mode, provide:

- `POSTMAN_API_KEY`
- `POSTMAN_WORKSPACE_ID`
- optional `POSTMAN_COLLECTION_UID` (if empty, pipeline imports collection from generated OpenAPI)
- optional `POSTMAN_MOCK_SERVER_ID`

## PR auto-doc workflow capability

Enable in client profile with `runtime.pr_autofix`.

Installed workflow behavior:

1. Trigger on PR events (`opened`, `synchronize`, `reopened`, `labeled`).
1. Analyze only current PR diff (`base...head`).
1. Run docs auto-fix script if docs contract/drift gates require docs updates.
1. Commit generated docs into the same PR branch.
1. Rerun checks automatically.

## Templates

These can be shipped via `bundle.include_paths` and used by LLM generation flow.

- `templates/admin-guide.md`
- `templates/api-endpoint.md`
- `templates/api-reference.md`
- `templates/architecture-overview.md`
- `templates/authentication-guide.md`
- `templates/best-practices.md`
- `templates/changelog.md`
- `templates/concept.md`
- `templates/configuration-guide.md`
- `templates/configuration-reference.md`
- `templates/deployment-guide.md`
- `templates/error-handling-guide.md`
- `templates/faq.md`
- `templates/glossary-page.md`
- `templates/how-to.md`
- `templates/integration-guide.md`
- `templates/interactive-diagram.html`
- `templates/migration-guide.md`
- `templates/plg-persona-guide.md`
- `templates/plg-value-page.md`
- `templates/quickstart.md`
- `templates/reference.md`
- `templates/release-note.md`
- `templates/sdk-reference.md`
- `templates/security-guide.md`
- `templates/testing-guide.md`
- `templates/troubleshooting.md`
- `templates/tutorial.md`
- `templates/upgrade-guide.md`
- `templates/use-case.md`
- `templates/user-guide.md`
- `templates/webhooks-guide.md`

## Policy Packs

- `api-first.yml`
- `minimal.yml`
- `monorepo.yml`
- `multi-product.yml`
- `plg.yml`

## Knowledge Modules

Can be copied into client bundle with `bundle.include_paths: ['knowledge_modules']`.

- `webhook-auth-baseline.yml`
- `webhook-retry-policy.yml`

## Docker Compose Profiles

- `docker-compose.api-sandbox.live.yml`
- `docker-compose.api-sandbox.prodlike.yml`
- `docker-compose.api-sandbox.yml`
- `docker-compose.docs-ops.yml`

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
