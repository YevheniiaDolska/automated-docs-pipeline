---
title: Plan Tiers (Basic / Pro / Enterprise)
description: Feature packaging matrix and defaults for Basic, Pro, and Enterprise
  client plans.
content_type: reference
product: both
last_reviewed: '2026-03-11'
tags:
- Operations
- Pricing
original_author: Developer
---


# Plan Tiers (Basic / Pro / Enterprise)

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

## 1. Feature matrix

| Capability | Basic | Pro | Enterprise |
| --- | --- | --- | --- |
| Core quality gates (normalize, snippets, smoke) | Yes | Yes | Yes |
| Gap detection | Yes | Yes | Yes |
| Weekly stale checks | Yes | Yes | Yes |
| Drift + docs contract gates | No | Yes | Yes |
| KPI/SLA reports | No | Yes | Yes |
| API-first flow | No | Optional | Full |
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

## 4. Plan upgrade path

- `Basic -> Pro`: turn on `drift_detection`, `docs_contract`, `kpi_sla`, `rag_optimization`, `knowledge_validation`, set `api_first.enabled=true`.
- `Pro -> Enterprise`: enable `verify_user_path`, `run_docs_lint`, stricter `policy_overrides.kpi_sla`, add full weekly custom tasks.

## Next steps

- [Documentation index](../index.md)
