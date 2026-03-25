---
title: Plan Tiers (Basic / Pro / Enterprise)
description: Feature packaging matrix and defaults for Basic, Pro, and Enterprise
  client plans.
content_type: reference
product: both
last_reviewed: '2026-03-24'
tags:
- Operations
- Pricing
original_author: Developer
---


# Plan Tiers (Basic / Pro / Enterprise)

## Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.


This document defines how pipeline functionality is packaged by client plan.

Use this with:

- `profiles/clients/<client>.client.yml`
- `docs/operations/UNIFIED_CLIENT_CONFIG.md`

Important:

- Basic/Pro/Enterprise are packaging presets, not hardcoded runtime limits.
- They are starting points for profile generation and commercial scope design.
- Pilot scope is defined separately by `profiles/clients/presets/pilot-evidence.yml`.
- Full implementation usually starts from plan-level Pro/Enterprise.
- In profile files, this is typically mapped to:
  - `profiles/clients/presets/startup.yml` (Pro-equivalent)
  - `profiles/clients/presets/enterprise.yml` (Enterprise-equivalent)

Practical mapping:

- Pilot -> `profiles/clients/presets/pilot-evidence.yml`
- Full Basic -> `profiles/clients/presets/small.yml`
- Full Pro -> `profiles/clients/presets/startup.yml`
- Full Enterprise -> `profiles/clients/presets/enterprise.yml`

In short:

- Plan = business scope level
- Preset = technical starting template
- Pilot/Full = implementation format


## Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

## 1. Feature matrix

| Capability | Basic | Pro | Enterprise |
| --- | --- | --- | --- |
| Core quality gates (normalize, snippets, smoke) | Yes | Yes | Yes |
| Gap detection | Yes | Yes | Yes |
| Weekly stale checks | Yes | Yes | Yes |
| Drift + docs contract gates | No | Yes | Yes |
| KPI/SLA reports | No | Yes | Yes |
| API-first flow | No | Optional | Full |
| Non-REST API-first autopipeline (GraphQL/gRPC/AsyncAPI/WebSocket) | No | No | Yes |
| Non-REST server stubs (business-logic placeholders) | No | No | Yes |
| Non-REST external mock auto-prepare (Postman) | No | No | Yes |
| API test assets (cases/matrix/fuzz docs) | No | Yes | Yes |
| TestRail/Zephyr upload from pipeline | No | Optional | Optional |
| RAG/knowledge validation/index | No | Yes | Yes |
| JSON-LD ontology/graph layer | No | Yes | Yes |
| Retrieval evals (Precision/Recall/Hallucination) | No | Yes | Yes |
| Terminology auto-sync (glossary markers) | Yes | Yes | Yes |
| PR auto-doc fix to same PR branch | Optional | Optional | Optional |
| i18n sync | No | Optional | Yes |
| SEO/GEO optimization weekly | Optional | Yes | Yes |
| Custom weekly task slots | 2 | 6 | Unlimited |
| Strict policy profile | minimal | api-first/monorepo | multi-product/plg + overrides |

## 2. Default plan presets

### Basic preset

```yaml
bundle:
  base_policy_pack: "minimal"
  style_guide: "google"
runtime:
  docs_flow:
    mode: "code-first"
  pr_autofix:
    enabled: false
  modules:
    gap_detection: true
    drift_detection: false
    docs_contract: false
    kpi_sla: false
    rag_optimization: false
    ontology_graph: false
    retrieval_evals: false
    terminology_management: true
    normalization: true
    snippet_lint: true
    self_checks: true
    fact_checks: true
    knowledge_validation: false
    i18n_sync: false
    release_pack: true
  api_first:
    enabled: false
  custom_tasks:
    weekly:
      - id: "seo-geo-lite"
        enabled: true
        command: "python3 docsops/scripts/seo_geo_optimizer.py docs/"
        continue_on_error: true
      - id: "max-two-tasks"
        enabled: false
        command: ""
        continue_on_error: true
private_tuning:
  weekly_stale_days: 180
```

### Pro preset

```yaml
bundle:
  base_policy_pack: "api-first"
  style_guide: "hybrid"
runtime:
  docs_flow:
    mode: "hybrid"
  pr_autofix:
    enabled: false
    require_label: false
    label_name: "auto-doc-fix"
    enable_auto_merge: false
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
    rag_optimization: true
    ontology_graph: true
    retrieval_evals: true
    terminology_management: true
    normalization: true
    snippet_lint: true
    self_checks: true
    fact_checks: true
    knowledge_validation: true
    i18n_sync: true
    release_pack: true
  api_first:
    enabled: true
    openapi_version: "3.1.0"
    manual_overrides_path: "api/overrides/openapi.manual.yml"
    regression_snapshot_path: "api/.openapi-regression.json"
    update_regression_snapshot: false
    generate_from_notes: true
    sandbox_backend: "external"
    mock_service: "custom"
    mock_base_url: "https://<your-real-public-mock-url>/v1"
    sync_playground_endpoint: true
    generate_test_assets: true
    test_assets_output_dir: "reports/api-test-assets"
    testrail_csv: "reports/api-test-assets/testrail_test_cases.csv"
    zephyr_json: "reports/api-test-assets/zephyr_test_cases.json"
    upload_test_assets: false
    upload_test_assets_strict: false
    test_assets_upload_report: "reports/api-test-assets/upload_report.json"
    external_mock:
      enabled: true
      provider: "postman"
      base_path: "/v1"
    auto_remediate: true
    max_attempts: 3
  custom_tasks:
    weekly:
      - id: "seo-geo"
        enabled: true
        command: "python3 docsops/scripts/seo_geo_optimizer.py docs/"
        continue_on_error: true
      - id: "knowledge-index"
        enabled: true
        command: "python3 docsops/scripts/generate_knowledge_retrieval_index.py"
        continue_on_error: true
private_tuning:
  weekly_stale_days: 180
```

### Enterprise preset

```yaml
bundle:
  base_policy_pack: "multi-product"
  style_guide: "microsoft"
  policy_overrides:
    kpi_sla:
      min_doc_coverage: 90
      max_stale_pct: 10
      max_quality_score_drop: 2
runtime:
  docs_flow:
    mode: "hybrid"
  pr_autofix:
    enabled: false
    require_label: false
    label_name: "auto-doc-fix"
    enable_auto_merge: false
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
    rag_optimization: true
    ontology_graph: true
    retrieval_evals: true
    terminology_management: true
    normalization: true
    snippet_lint: true
    self_checks: true
    fact_checks: true
    knowledge_validation: true
    i18n_sync: true
    release_pack: true
  api_first:
    enabled: true
    openapi_version: "3.1.0"
    manual_overrides_path: "api/overrides/openapi.manual.yml"
    regression_snapshot_path: "api/.openapi-regression.json"
    update_regression_snapshot: false
    generate_from_notes: true
    verify_user_path: true
    sandbox_backend: "external"
    mock_service: "custom"
    mock_base_url: "https://<your-real-public-mock-url>/v1"
    sync_playground_endpoint: true
    generate_test_assets: true
    test_assets_output_dir: "reports/api-test-assets"
    testrail_csv: "reports/api-test-assets/testrail_test_cases.csv"
    zephyr_json: "reports/api-test-assets/zephyr_test_cases.json"
    upload_test_assets: false
    upload_test_assets_strict: false
    test_assets_upload_report: "reports/api-test-assets/upload_report.json"
    external_mock:
      enabled: true
      provider: "postman"
      base_path: "/v1"
    run_docs_lint: true
    auto_remediate: true
    max_attempts: 5
  api_protocols:
    - "rest"
    - "graphql"
    - "grpc"
    - "asyncapi"
    - "websocket"
  api_protocol_settings:
    graphql:
      enabled: true
      mode: "api-first"
      generate_server_stubs: true
      stubs_output: "generated/api-stubs/graphql/handlers.py"
    grpc:
      enabled: true
      mode: "api-first"
      generate_server_stubs: true
      stubs_output: "generated/api-stubs/grpc/handlers.py"
    asyncapi:
      enabled: true
      mode: "api-first"
      generate_server_stubs: true
      stubs_output: "generated/api-stubs/asyncapi/handlers.py"
    websocket:
      enabled: true
      mode: "api-first"
      generate_server_stubs: true
      stubs_output: "generated/api-stubs/websocket/handlers.py"
  custom_tasks:
    weekly:
      - id: "seo-geo"
        enabled: true
        command: "python3 docsops/scripts/seo_geo_optimizer.py docs/"
        continue_on_error: true
      - id: "knowledge-validate"
        enabled: true
        command: "python3 docsops/scripts/validate_knowledge_modules.py"
        continue_on_error: true
      - id: "knowledge-index"
        enabled: true
        command: "python3 docsops/scripts/generate_knowledge_retrieval_index.py"
        continue_on_error: true
      - id: "intent-experiences"
        enabled: true
        command: "python3 docsops/scripts/build_all_intent_experiences.py"
        continue_on_error: true
private_tuning:
  weekly_stale_days: 180
```

## 3. How to apply a plan for a client

\11. Copy `profiles/clients/_template.client.yml` to `profiles/clients/<client>.client.yml`.
\11. Copy one preset from this page into the new profile.
\11. Adjust paths (`docs_root`, `api_root`, `sdk_root`) and output targets.
\11. Build/install:

```bash
python3 scripts/provision_client_repo.py \
  --client profiles/clients/<client>.client.yml \
  --client-repo /path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler linux
```

## 4. License enforcement

Plan tiers are enforced at runtime by `scripts/license_gate.py`. Every gated script calls `license_gate.require("feature_name")` before executing protected logic. The license is validated offline using an Ed25519-signed JWT stored at `docsops/license.jwt`.

Without a valid license, the pipeline runs in **community mode** (degraded):

- Markdown lint, frontmatter validation, SEO/GEO report-only, gap detection code-only, glossary sync, lifecycle management, REST protocol.
- No scoring, no auto-fix, no drift detection, no KPI/SLA, no PDF reports, no multi-protocol.
- Quality gates warn-only (never block).

License features per plan:

| Feature gate | Pilot | Professional | Enterprise |
| --- | --- | --- | --- |
| `seo_geo_scoring` | No | Yes | Yes |
| `api_first_flow` | No | Yes | Yes |
| `drift_detection` | No | Yes | Yes |
| `kpi_wall_sla` | No | Yes | Yes |
| `test_assets_generation` | No | Yes | Yes |
| `consolidated_reports` | No | Yes | Yes |
| `multi_protocol_pipeline` | No | No | Yes |
| `knowledge_modules` | No | No | Yes |
| `knowledge_graph` | No | No | Yes |
| `faiss_retrieval` | No | No | Yes |
| `executive_audit_pdf` | No | No | Yes |
| `i18n_system` | No | No | Yes |
| `custom_policy_packs` | No | No | Yes |
| `testrail_zephyr_upload` | No | No | Yes |

Protocols per plan: Pilot and Professional allow REST only. Enterprise allows all 5 protocols.

Offline grace period: Pilot 3 days, Professional 7 days, Enterprise 30 days.

Check license status: `python3 docsops/scripts/license_gate.py`.

Dev/test bypass: `export VERIOPS_LICENSE_PLAN=enterprise`.

## 5. Plan upgrade path

- `Basic -> Pro`: turn on `drift_detection`, `docs_contract`, `kpi_sla`, `rag_optimization`, `knowledge_validation`, set `api_first.enabled=true`. Update `licensing.plan` to `professional`.
- `Pro -> Enterprise`: enable `verify_user_path`, `run_docs_lint`, stricter `policy_overrides.kpi_sla`, add full weekly custom tasks. Update `licensing.plan` to `enterprise`.

After any plan change, rebuild the bundle and re-provision.

## Next steps

- [Operator Runbook](OPERATOR_RUNBOOK.md) -- step-by-step retainer procedures
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
