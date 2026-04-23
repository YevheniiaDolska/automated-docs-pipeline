---
title: "Pipeline Capabilities Catalog"
description: "Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration."
content_type: reference
product: both
tags:
  - Operations
  - Reference
---

# Pipeline Capabilities Catalog

This file is auto-generated from `package.json` scripts.

Use this catalog with `runtime.custom_tasks.weekly` in client profiles to enable any capability.

## Packaging and Autopipeline Scope

- This catalog is a full inventory of available commands.
- `Agent/Demo` commands are demo-only and are not part of default client autopipeline.
- In commercial packaging:
  - `full` (`professional` plan): smooth autopipeline includes all non-demo capabilities except retrieval-time RAG (`faiss_retrieval`).
  - `full+rag` (`enterprise` plan): smooth autopipeline includes all non-demo capabilities, including retrieval-time RAG.
- If a capability needs external infrastructure (for example, provider credentials, external mock service, Docker runtime), setup wizard records it as a client-side prerequisite.

## RAG System (Current Implementation)

RAG is implemented as a two-layer system:

- Knowledge preparation layer (included in `full` and `full+rag`):
  - docs -> knowledge modules extraction/validation
  - retrieval index generation (`knowledge-retrieval-index.json`)
  - JSON-LD knowledge graph generation (`knowledge-graph.jsonld`)
  - retrieval evaluation gate/reporting
  - stale detection in docs quality loop
  - contradiction detection and critical-module exclusion from retrieval index
- Retrieval-time runtime layer (included in `full+rag`):
  - Ask AI runtime API and widget
  - semantic retrieval (FAISS) with hybrid/rerank/HyDE/cache options
  - runtime confidence guardrail (low-confidence safe response)
  - contradiction warning propagation to client response
  - usage logging and end-user feedback logging

Primary runtime and report artifacts:

- `docs/assets/knowledge-retrieval-index.json`
- `docs/assets/knowledge-graph.jsonld`
- `reports/retrieval_eval_report.json`
- `reports/rag_contradictions_report.json`
- `reports/ask_ai_usage.jsonl`
- `reports/ask_ai_feedback.jsonl`

Operational meaning by plan:

- `community/pilot`: no advanced RAG capabilities in default autopipeline.
- `professional/full`: full docs-ops + RAG preparation (everything except retrieval-time RAG).
- `enterprise/full+rag`: same as `full` plus retrieval-time Ask AI runtime with RAG.

## Prerequisites Ownership

- Client side:
  - Provider credentials (`OPENAI/ANTHROPIC/AZURE`, `ALGOLIA`, `POSTMAN`, `TESTRAIL/ZEPHYR`) when corresponding integrations are enabled.
  - Runtime/runner prerequisites (`python3`, `node`, `npm`, optional `docker`).
- Operator side:
  - Signed `docsops/license.jwt`.
  - Capability pack (for premium features when required by policy).
  - Baseline policy/runtime defaults delivered in bundle.
- Strict-local fallback:
  - If Docker is unavailable, use `api_first.sandbox_backend=prism`.
  - External provider credentials can stay empty when external integrations are disabled.

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
| `api-first:demo` | API-first | `bash -lc 'set -e; bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010; trap "bash scripts/api_sandbox_project.sh down taskstream ./api/openapi.yaml 4010" EXIT; python3 scripts/run_api_first_flow.py --project-slug taskstream --notes demos/api-first/taskstream-planning-notes.md --spec api/openapi.yaml --spec-tree api/taskstream --docs-provider mkdocs --inject-demo-nav --verify-user-path --mock-base-url http://localhost:4010/v1 --auto-remediate --max-attempts 3'` |
| `api-first:demo:live` | API-first | `bash scripts/api_first_demo_live.sh` |
| `api-first:demo:stop` | API-first | `bash scripts/api_first_demo_stop.sh` |
| `api:first:flow:taskstream` | API-first | `python3 scripts/run_api_first_flow.py --project-slug taskstream --notes demos/api-first/taskstream-planning-notes.md --spec api/openapi.yaml --spec-tree api/taskstream --docs-provider mkdocs --inject-demo-nav --auto-remediate` |
| `api:first:v0:taskstream` | API-first | `python3 scripts/run_api_first_flow.py --project-slug taskstream --notes demos/api-first/taskstream-planning-notes.md --spec api/openapi.yaml --spec-tree api/taskstream --docs-provider mkdocs --auto-remediate --max-attempts 3` |
| `api:first:verify-user-path` | API-first | `python3 scripts/self_verify_api_user_path.py --base-url http://localhost:4010/v1` |
| `api:first:verify-user-path:prodlike` | API-first | `python3 scripts/self_verify_prodlike_user_path.py --base-url http://localhost:4011/v1` |
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
| `api:test:assets` | API-first | `python3 scripts/generate_api_test_assets.py --spec api/openapi.yaml --output-dir reports/api-test-assets --testrail-csv reports/api-test-assets/testrail_test_cases.csv --zephyr-json reports/api-test-assets/zephyr_test_cases.json` |
| `api:test:upload` | API-first | `python3 scripts/upload_api_test_assets.py --cases-json reports/api-test-assets/api_test_cases.json --report reports/api-test-assets/upload_report.json` |
| `askai:configure` | General | `python3 scripts/configure_ask_ai.py` |
| `askai:disable` | General | `python3 scripts/configure_ask_ai.py --disable` |
| `askai:enable` | General | `python3 scripts/configure_ask_ai.py --enable` |
| `askai:runtime:install` | General | `python3 scripts/install_ask_ai_runtime.py --target-dir .` |
| `askai:runtime:install:force` | General | `python3 scripts/install_ask_ai_runtime.py --target-dir . --force` |
| `askai:status` | General | `python3 scripts/configure_ask_ai.py --status` |
| `audit:executive-pdf` | General | `python3 scripts/generate_executive_audit_pdf.py --scorecard-json reports/audit_scorecard.json --public-audit-json reports/public_docs_audit.json --llm-summary-json reports/public_docs_audit_llm_summary.json --company-name "Client"` |
| `audit:public` | General | `python3 scripts/generate_public_docs_audit.py` |
| `audit:public:llm` | General | `python3 scripts/generate_public_docs_audit.py --llm-enabled --llm-model claude-sonnet-4-5 --llm-api-key-env-name ANTHROPIC_API_KEY` |
| `audit:public:llm-summary` | General | `python3 scripts/generate_public_docs_audit.py --llm-enabled --llm-summary-only --llm-model claude-sonnet-4-5 --llm-api-key-env-name ANTHROPIC_API_KEY` |
| `audit:public:wizard` | General | `python3 scripts/generate_public_docs_audit.py --interactive` |
| `audit:scorecard` | General | `python3 scripts/generate_audit_scorecard.py --docs-dir docs --reports-dir reports --spec-path api/openapi.yaml --policy-pack policy_packs/api-first.yml --glossary-path glossary.yml --stale-days 180 --auto-run-smoke --json-output reports/audit_scorecard.json --html-output reports/audit_scorecard.html` |
| `badges` | General | `python3 scripts/generate_badge.py --json reports/kpi-wall.json --output reports` |
| `build` | Build/Generate | `python3 scripts/run_generator.py build` |
| `build:docusaurus` | Build/Generate | `npx docusaurus build` |
| `build:intent` | Build/Generate | `python3 scripts/assemble_intent_experience.py` |
| `build:intent:all` | Build/Generate | `python3 scripts/build_all_intent_experiences.py` |
| `build:knowledge-enrich:llm` | Build/Generate | `python3 scripts/enrich_knowledge_modules_semantic.py` |
| `build:knowledge-graph` | Build/Generate | `python3 scripts/generate_knowledge_graph_jsonld.py --modules-dir knowledge_modules --output docs/assets/knowledge-graph.jsonld --report reports/knowledge_graph_report.json` |
| `build:knowledge-index` | Build/Generate | `python3 scripts/generate_knowledge_retrieval_index.py` |
| `build:mkdocs` | Build/Generate | `mkdocs build --strict` |
| `build:rag:reindex` | Build/Generate | `python3 scripts/rag_reindex_lifecycle.py --repo-root . --with-embeddings --provider local` |
| `bundle:free-enterprise` | General | `python3 scripts/build_free_enterprise_bundle.py --client profiles/clients/acme.client.yml` |
| `configurator` | General | `python3 scripts/generate_configurator.py` |
| `confluence:migrate` | General | `python3 scripts/run_confluence_migration.py` |
| `consolidate` | General | `npm run gaps && npm run kpi-wall && npm run kpi-sla && npm run i18n:sync && npm run validate:knowledge && python3 scripts/consolidate_reports.py` |
| `consolidate:reports-only` | General | `python3 scripts/consolidate_reports.py` |
| `convert:to-docusaurus` | General | `python3 scripts/markdown_converter.py to-docusaurus docs/` |
| `convert:to-mkdocs` | General | `python3 scripts/markdown_converter.py to-mkdocs docs/` |
| `demo:api-first` | Agent/Demo | `bash scripts/api_first_demo_live.sh` |
| `demo:api-first:stop` | Agent/Demo | `bash scripts/api_first_demo_stop.sh` |
| `demo:claude:loop` | Agent/Demo | `bash scripts/claude-demo-loop.sh` |
| `demo:codex` | Agent/Demo | `bash scripts/codex-demo.sh` |
| `demo:codex:loop` | Agent/Demo | `bash scripts/codex-demo-loop.sh` |
| `doc:compile` | General | `python3 scripts/compile_doc_overview.py --docs-dir docs --reports-dir reports --modalities all` |
| `docs-contract` | General | `python3 scripts/check_docs_contract.py --base origin/main --head HEAD --json-output reports/pr_docs_contract.json` |
| `docs-ops:e2e` | VeriOps tests | `python3 scripts/test_docs_ops_e2e.py` |
| `docs-ops:golden` | VeriOps tests | `python3 scripts/test_golden_reports_and_workflows.py` |
| `docs-ops:test-suite` | VeriOps tests | `python3 -m pytest -q tests/test_autopipeline_suite.py` |
| `docsops:generate` | General | `python3 scripts/docsops_generate.py generate --mode operator --trigger always` |
| `docsops:generate:auto` | General | `python3 scripts/docsops_generate.py generate --mode operator --trigger always --auto` |
| `docsops:generate:policy` | General | `python3 scripts/docsops_generate.py generate --mode operator --trigger policy --auto` |
| `docsops:generate:veridoc` | General | `python3 scripts/docsops_generate.py generate --mode veridoc --trigger policy --auto` |
| `drift-check` | General | `python3 scripts/check_api_sdk_drift.py --base origin/main --head HEAD --json-output reports/api_sdk_drift_report.json --md-output reports/api_sdk_drift_report.md` |
| `eval:retrieval` | General | `python3 scripts/run_retrieval_evals_gate.py` |
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
| `lint:diagrams` | Lint/Quality | `python3 scripts/validate_diagram_content.py docs templates --strict` |
| `lint:examples-smoke` | Lint/Quality | `python3 scripts/check_code_examples_smoke.py --paths docs templates` |
| `lint:examples-smoke:network` | Lint/Quality | `python3 scripts/check_code_examples_smoke.py --paths docs templates --allow-network` |
| `lint:frontmatter` | Lint/Quality | `python3 scripts/validate_frontmatter.py` |
| `lint:geo` | Lint/Quality | `python3 scripts/seo_geo_optimizer.py docs/` |
| `lint:knowledge` | Lint/Quality | `python3 scripts/validate_knowledge_modules.py` |
| `lint:layers` | Lint/Quality | `python3 scripts/doc_layers_validator.py --strict` |
| `lint:md` | Lint/Quality | `markdownlint docs/` |
| `lint:multilang` | Lint/Quality | `python3 scripts/validate_multilang_examples.py --docs-dir docs --scope api --required-languages curl,javascript,python` |
| `lint:multilang:all` | Lint/Quality | `python3 scripts/validate_multilang_examples.py --docs-dir docs --scope all --required-languages curl,javascript,python` |
| `lint:openapi` | Lint/Quality | `npx -y @stoplight/spectral-cli lint api/openapi.yaml --ruleset .spectral.yml && npx -y @redocly/cli lint api/openapi.yaml && npx -y @apidevtools/swagger-cli validate api/openapi.yaml && python3 scripts/validate_openapi_contract.py api/openapi.yaml` |
| `lint:snippets` | Lint/Quality | `python3 scripts/lint_code_snippets.py docs/ --strict` |
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
| `smoke:prod` | General | `python3 scripts/production_smoke.py` |
| `test:adapter` | General | `python3 -m pytest tests/test_docusaurus_adapter.py -v` |
| `test:all` | General | `python3 -m pytest -q tests` |
| `test:configurator` | General | `python3 -m pytest tests/test_gui_configurator.py -v` |
| `validate:full` | Validation | `npm run validate:minimal && npm run lint:layers && npm run lint:diagrams && npm run validate:knowledge && npm run docs-ops:e2e && npm run docs-ops:golden && npm run docs-ops:test-suite && python3 test_pipeline.py` |
| `validate:knowledge` | Validation | `npm run lint:knowledge && npm run build:intent:all && npm run build:knowledge-index && npm run build:knowledge-graph && npm run eval:retrieval` |
| `validate:knowledge:with-llm-enrich` | Validation | `npm run build:knowledge-enrich:llm && npm run validate:knowledge` |
| `validate:minimal` | Validation | `npm run normalize:docs:check && npm run lint:md && npm run lint:frontmatter && npm run lint:geo && npm run lint:multilang && npm run lint:examples-smoke` |

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
- `templates/protocols`
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

- `auto-api-playground-1.yml`
- `auto-api-playground-2.yml`
- `auto-api-playground-3.yml`
- `auto-assemble-intent-experiences-1.yml`
- `auto-assemble-intent-experiences-2.yml`
- `auto-assemble-intent-experiences-3.yml`
- `auto-asyncapi-api-1.yml`
- `auto-asyncapi-api-2.yml`
- `auto-asyncapi-api-3.yml`
- `auto-asyncapi-api-4.yml`
- `auto-auto-doc-pipeline-study-guide-1.yml`
- `auto-auto-doc-pipeline-study-guide-2.yml`
- `auto-auto-doc-pipeline-study-guide-3.yml`
- `auto-auto-doc-pipeline-study-guide-4.yml`
- `auto-auto-doc-pipeline-study-guide-5.yml`
- `auto-auto-doc-pipeline-study-guide-6.yml`
- `auto-auto-doc-pipeline-study-guide-7.yml`
- `auto-auto-doc-pipeline-study-guide-8.yml`
- `auto-canonical-flow-1.yml`
- `auto-canonical-flow-2.yml`
- `auto-canonical-flow-3.yml`
- `auto-canonical-flow-4.yml`
- `auto-canonical-flow-5.yml`
- `auto-canonical-flow-6.yml`
- `auto-canonical-flow-7.yml`
- `auto-canonical-flow-8.yml`
- `auto-canonical-flow-9.yml`
- `auto-centralized-client-bundles-1.yml`
- `auto-centralized-client-bundles-10.yml`
- `auto-centralized-client-bundles-11.yml`
- `auto-centralized-client-bundles-12.yml`
- `auto-centralized-client-bundles-13.yml`
- `auto-centralized-client-bundles-14.yml`
- `auto-centralized-client-bundles-15.yml`
- `auto-centralized-client-bundles-16.yml`
- `auto-centralized-client-bundles-17.yml`
- `auto-centralized-client-bundles-18.yml`
- `auto-centralized-client-bundles-19.yml`
- `auto-centralized-client-bundles-2.yml`
- `auto-centralized-client-bundles-20.yml`
- `auto-centralized-client-bundles-3.yml`
- `auto-centralized-client-bundles-4.yml`
- `auto-centralized-client-bundles-5.yml`
- `auto-centralized-client-bundles-6.yml`
- `auto-centralized-client-bundles-7.yml`
- `auto-centralized-client-bundles-8.yml`
- `auto-centralized-client-bundles-9.yml`
- `auto-configure-ask-ai-module-1.yml`
- `auto-configure-ask-ai-module-2.yml`
- `auto-configure-ask-ai-module-3.yml`
- `auto-configure-ask-ai-module-4.yml`
- `auto-configure-webhook-trigger-1.yml`
- `auto-configure-webhook-trigger-2.yml`
- `auto-configure-webhook-trigger-3.yml`
- `auto-configure-webhook-trigger-4.yml`
- `auto-data-processing-agreement-1.yml`
- `auto-data-processing-agreement-2.yml`
- `auto-data-processing-agreement-3.yml`
- `auto-data-processing-agreement-4.yml`
- `auto-data-processing-agreement-5.yml`
- `auto-data-processing-agreement-6.yml`
- `auto-data-processing-agreement-7.yml`
- `auto-deprecated-example-1.yml`
- `auto-graphql-api-1.yml`
- `auto-graphql-api-2.yml`
- `auto-graphql-api-3.yml`
- `auto-graphql-api-4.yml`
- `auto-grpc-api-1.yml`
- `auto-grpc-api-2.yml`
- `auto-grpc-api-3.yml`
- `auto-grpc-api-4.yml`
- `auto-index-1.yml`
- `auto-index-2.yml`
- `auto-install-ask-ai-runtime-pack-1.yml`
- `auto-install-ask-ai-runtime-pack-2.yml`
- `auto-install-ask-ai-runtime-pack-3.yml`
- `auto-intelligent-knowledge-system-1.yml`
- `auto-intelligent-knowledge-system-2.yml`
- `auto-intelligent-knowledge-system-3.yml`
- `auto-intelligent-knowledge-system-4.yml`
- `auto-intelligent-knowledge-system-5.yml`
- `auto-intelligent-knowledge-system-6.yml`
- `auto-migrate-from-confluence-1.yml`
- `auto-migrate-from-confluence-2.yml`
- `auto-migrate-from-confluence-3.yml`
- `auto-migrate-from-confluence-4.yml`
- `auto-migrate-from-confluence-5.yml`
- `auto-migrate-from-confluence-6.yml`
- `auto-migrate-from-confluence-7.yml`
- `auto-migrate-from-confluence-8.yml`
- `auto-multi-protocol-architecture-1.yml`
- `auto-multi-protocol-architecture-2.yml`
- `auto-multi-protocol-architecture-3.yml`
- `auto-multi-protocol-architecture-4.yml`
- `auto-multi-protocol-architecture-5.yml`
- `auto-multi-protocol-architecture-6.yml`
- `auto-multi-protocol-wizard-guide-1.yml`
- `auto-multi-protocol-wizard-guide-2.yml`
- `auto-multi-protocol-wizard-guide-3.yml`
- `auto-multi-protocol-wizard-guide-4.yml`
- `auto-multi-protocol-wizard-guide-5.yml`
- `auto-multi-protocol-wizard-guide-6.yml`
- `auto-network-transparency-1.yml`
- `auto-network-transparency-2.yml`
- `auto-network-transparency-3.yml`
- `auto-network-transparency-4.yml`
- `auto-network-transparency-5.yml`
- `auto-network-transparency-6.yml`
- `auto-network-transparency-7.yml`
- `auto-network-transparency-8.yml`
- `auto-network-transparency-9.yml`
- `auto-operator-runbook-1.yml`
- `auto-operator-runbook-10.yml`
- `auto-operator-runbook-11.yml`
- `auto-operator-runbook-12.yml`
- `auto-operator-runbook-13.yml`
- `auto-operator-runbook-14.yml`
- `auto-operator-runbook-15.yml`
- `auto-operator-runbook-16.yml`
- `auto-operator-runbook-17.yml`
- `auto-operator-runbook-18.yml`
- `auto-operator-runbook-19.yml`
- `auto-operator-runbook-2.yml`
- `auto-operator-runbook-20.yml`
- `auto-operator-runbook-21.yml`
- `auto-operator-runbook-22.yml`
- `auto-operator-runbook-23.yml`
- `auto-operator-runbook-24.yml`
- `auto-operator-runbook-3.yml`
- `auto-operator-runbook-4.yml`
- `auto-operator-runbook-5.yml`
- `auto-operator-runbook-6.yml`
- `auto-operator-runbook-7.yml`
- `auto-operator-runbook-8.yml`
- `auto-operator-runbook-9.yml`
- `auto-pipeline-capabilities-catalog-1.yml`
- `auto-pipeline-capabilities-catalog-10.yml`
- `auto-pipeline-capabilities-catalog-11.yml`
- `auto-pipeline-capabilities-catalog-12.yml`
- `auto-pipeline-capabilities-catalog-13.yml`
- `auto-pipeline-capabilities-catalog-14.yml`
- `auto-pipeline-capabilities-catalog-15.yml`
- `auto-pipeline-capabilities-catalog-16.yml`
- `auto-pipeline-capabilities-catalog-17.yml`
- `auto-pipeline-capabilities-catalog-18.yml`
- `auto-pipeline-capabilities-catalog-19.yml`
- `auto-pipeline-capabilities-catalog-2.yml`
- `auto-pipeline-capabilities-catalog-20.yml`
- `auto-pipeline-capabilities-catalog-21.yml`
- `auto-pipeline-capabilities-catalog-22.yml`
- `auto-pipeline-capabilities-catalog-3.yml`
- `auto-pipeline-capabilities-catalog-4.yml`
- `auto-pipeline-capabilities-catalog-5.yml`
- `auto-pipeline-capabilities-catalog-6.yml`
- `auto-pipeline-capabilities-catalog-7.yml`
- `auto-pipeline-capabilities-catalog-8.yml`
- `auto-pipeline-capabilities-catalog-9.yml`
- `auto-plan-tiers-1.yml`
- `auto-plan-tiers-10.yml`
- `auto-plan-tiers-11.yml`
- `auto-plan-tiers-12.yml`
- `auto-plan-tiers-13.yml`
- `auto-plan-tiers-14.yml`
- `auto-plan-tiers-2.yml`
- `auto-plan-tiers-3.yml`
- `auto-plan-tiers-4.yml`
- `auto-plan-tiers-5.yml`
- `auto-plan-tiers-6.yml`
- `auto-plan-tiers-7.yml`
- `auto-plan-tiers-8.yml`
- `auto-plan-tiers-9.yml`
- `auto-privacy-policy-1.yml`
- `auto-privacy-policy-2.yml`
- `auto-privacy-policy-3.yml`
- `auto-privacy-policy-4.yml`
- `auto-privacy-policy-5.yml`
- `auto-privacy-policy-6.yml`
- `auto-privacy-policy-7.yml`
- `auto-quickstart-1.yml`
- `auto-quickstart-2.yml`
- `auto-rest-api-1.yml`
- `auto-run-api-first-production-flow-1.yml`
- `auto-run-api-first-production-flow-10.yml`
- `auto-run-api-first-production-flow-11.yml`
- `auto-run-api-first-production-flow-2.yml`
- `auto-run-api-first-production-flow-3.yml`
- `auto-run-api-first-production-flow-4.yml`
- `auto-run-api-first-production-flow-5.yml`
- `auto-run-api-first-production-flow-6.yml`
- `auto-run-api-first-production-flow-7.yml`
- `auto-run-api-first-production-flow-8.yml`
- `auto-run-api-first-production-flow-9.yml`
- `auto-search-faceted-1.yml`
- `auto-search-faceted-2.yml`
- `auto-search-faceted-3.yml`
- `auto-security-contact-policy-1.yml`
- `auto-security-contact-policy-2.yml`
- `auto-security-policy-1.yml`
- `auto-security-policy-2.yml`
- `auto-security-policy-3.yml`
- `auto-security-policy-4.yml`
- `auto-security-policy-5.yml`
- `auto-security-policy-6.yml`
- `auto-security-policy-7.yml`
- `auto-seo-guide-1.yml`
- `auto-seo-guide-2.yml`
- `auto-seo-guide-3.yml`
- `auto-seo-guide-4.yml`
- `auto-seo-guide-5.yml`
- `auto-seo-guide-6.yml`
- `auto-set-up-real-time-webhook-processing-pipeline-1.yml`
- `auto-set-up-real-time-webhook-processing-pipeline-10.yml`
- `auto-set-up-real-time-webhook-processing-pipeline-11.yml`
- `auto-set-up-real-time-webhook-processing-pipeline-12.yml`
- `auto-set-up-real-time-webhook-processing-pipeline-13.yml`
- `auto-set-up-real-time-webhook-processing-pipeline-14.yml`
- `auto-set-up-real-time-webhook-processing-pipeline-15.yml`
- `auto-set-up-real-time-webhook-processing-pipeline-2.yml`
- `auto-set-up-real-time-webhook-processing-pipeline-3.yml`
- `auto-set-up-real-time-webhook-processing-pipeline-4.yml`
- `auto-set-up-real-time-webhook-processing-pipeline-5.yml`
- `auto-set-up-real-time-webhook-processing-pipeline-6.yml`
- `auto-set-up-real-time-webhook-processing-pipeline-7.yml`
- `auto-set-up-real-time-webhook-processing-pipeline-8.yml`
- `auto-set-up-real-time-webhook-processing-pipeline-9.yml`
- `auto-smart-merge-review-1.yml`
- `auto-smart-merge-review-2.yml`
- `auto-smart-merge-review-3.yml`
- `auto-smart-merge-review-4.yml`
- `auto-tags-1.yml`
- `auto-taskstream-api-playground-1.yml`
- `auto-taskstream-api-playground-2.yml`
- `auto-taskstream-api-playground-3.yml`
- `auto-taskstream-planning-notes-1.yml`
- `auto-terms-of-service-1.yml`
- `auto-terms-of-service-2.yml`
- `auto-terms-of-service-3.yml`
- `auto-terms-of-service-4.yml`
- `auto-terms-of-service-5.yml`
- `auto-unified-client-config-1.yml`
- `auto-unified-client-config-10.yml`
- `auto-unified-client-config-11.yml`
- `auto-unified-client-config-12.yml`
- `auto-unified-client-config-13.yml`
- `auto-unified-client-config-14.yml`
- `auto-unified-client-config-15.yml`
- `auto-unified-client-config-16.yml`
- `auto-unified-client-config-17.yml`
- `auto-unified-client-config-18.yml`
- `auto-unified-client-config-19.yml`
- `auto-unified-client-config-2.yml`
- `auto-unified-client-config-20.yml`
- `auto-unified-client-config-21.yml`
- `auto-unified-client-config-22.yml`
- `auto-unified-client-config-23.yml`
- `auto-unified-client-config-24.yml`
- `auto-unified-client-config-25.yml`
- `auto-unified-client-config-26.yml`
- `auto-unified-client-config-27.yml`
- `auto-unified-client-config-28.yml`
- `auto-unified-client-config-29.yml`
- `auto-unified-client-config-3.yml`
- `auto-unified-client-config-30.yml`
- `auto-unified-client-config-31.yml`
- `auto-unified-client-config-4.yml`
- `auto-unified-client-config-5.yml`
- `auto-unified-client-config-6.yml`
- `auto-unified-client-config-7.yml`
- `auto-unified-client-config-8.yml`
- `auto-unified-client-config-9.yml`
- `auto-variables-guide-1.yml`
- `auto-variables-guide-2.yml`
- `auto-variables-guide-3.yml`
- `auto-variables-guide-4.yml`
- `auto-webhook-1.yml`
- `auto-webhook-2.yml`
- `auto-webhook-3.yml`
- `auto-webhook-not-firing-1.yml`
- `auto-webhook-not-firing-2.yml`
- `auto-webhook-not-firing-3.yml`
- `auto-websocket-api-1.yml`
- `auto-websocket-api-2.yml`
- `auto-websocket-api-3.yml`
- `auto-websocket-api-4.yml`
- `auto-workflow-execution-model-1.yml`
- `auto-workflow-execution-model-2.yml`
- `auto-workflow-execution-model-3.yml`
- `webhook-auth-baseline.yml`
- `webhook-retry-policy.yml`

## Docker Compose Profiles

- `docker-compose.api-sandbox.live.yml`
- `docker-compose.api-sandbox.prodlike.yml`
- `docker-compose.api-sandbox.yml`
- `docker-compose.docs-ops.yml`
- `docker-compose.production.yml`
- `docker-compose.staging.yml`

## Next steps

- [Documentation index](../index.md)
