---
title: "Unified Client Configuration"
description: "Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation."
content_type: reference
product: both
last_reviewed: "2026-03-11"
tags:
  - Operations
  - Configuration
---

# Unified Client Configuration

Single source of truth for per-client setup:

- `profiles/clients/<client>.client.yml`

This file controls all client-specific behavior: repo paths, flow mode, modules, quality strictness, automation schedule, and legal labeling.

Operator-first setup path (recommended):
\11. Run `python3 scripts/onboard_client.py`.
\11. Answer wizard questions (preset + client data + repo path + scheduler).
\11. Review generated profile in `profiles/clients/generated/<client_id>.client.yml`.
\11. Confirm install.
\11. Verify outputs:

- `<client-repo>/docsops/config/client_runtime.yml`
- `<client-repo>/docsops/policy_packs/selected.yml`
- `<client-repo>/docsops/ENV_CHECKLIST.md`

Plan packaging reference:

- `docs/operations/PLAN_TIERS.md` (Basic / Pro / Enterprise presets)

## 1. Client identity

```yaml
client:
  id: "acme"
  company_name: "ACME Inc."
  contact_email: "docs-owner@acme.example"
```

## 2. Bundle packaging

```yaml
bundle:
  output_dir: "generated/client_bundles"
  base_policy_pack: "multi-product"
  style_guide: "google"
  policy_overrides: {}
  include_scripts: []
  include_docs: []
  include_paths: []
```

### `base_policy_pack`

Available built-ins:

- `minimal`
- `api-first`
- `monorepo`
- `multi-product`
- `plg`

### `policy_overrides`

Deep-merged into selected policy pack for per-client tuning.

Example:

```yaml
bundle:
  policy_overrides:
    kpi_sla:
      min_doc_coverage: 90
      max_quality_score_drop: 2
```

### `style_guide` (Vale style profile)

```yaml
bundle:
  style_guide: "google" # google | microsoft | hybrid
```

Builder writes `.vale.ini` in client bundle automatically based on this setting.

Notes:

- `google` -> Google-based lint profile
- `microsoft` -> Microsoft-based lint profile
- `hybrid` -> both style packs enabled
- run `vale sync` in client repo after provisioning to fetch selected style packages

### `include_paths` (important for templates and knowledge)

Allows copying any extra files and folders into the bundle:

```yaml
bundle:
  include_paths:
    - "templates/interactive-diagram.html"
    - "knowledge_modules"
```

Use this for:

- interactive diagrams
- knowledge modules
- any custom assets

## 3. LLM instruction packaging

```yaml
bundle:
  llm:
    codex_instructions_source: "AGENTS.md"
    claude_instructions_source: "CLAUDE.md"
    inject_managed_block: true
    docsops_root_in_client_repo: "docsops"
```

When `inject_managed_block=true`, builder auto-inserts managed docsops block into bundled `AGENTS.md` and `CLAUDE.md`.

## 4. Automation schedule (weekly)

```yaml
bundle:
  automation:
    weekly_gap_report:
      enabled: true
      since_days: 7
      day_of_week: "monday"
      time_24h: "09:00"
```

## 5. Runtime behavior

```yaml
runtime:
  docs_flow:
    mode: "code-first" # code-first | api-first | hybrid
  docs_root: "docs"
  api_root: "api"
  sdk_root: "sdk"
  preferred_llm: "claude"
  output_targets: ["sphinx", "readme"]
```

## 6. API-first configuration (one branch, not the whole product)

```yaml
runtime:
  api_first:
    enabled: true
    project_slug: "acme"
    notes_path: "notes/api-planning.md"
    spec_path: "api/openapi.yaml"
    spec_tree_path: "api/acme"
    docs_provider: "mkdocs"
    docs_spec_target: "docs/assets/api"
    stubs_output: "generated/api-stubs/fastapi/app/main.py"
    generate_from_notes: true
    verify_user_path: false
    mock_base_url: "http://localhost:4010/v1"
    run_docs_lint: false
    auto_remediate: true
    max_attempts: 3
```

## 7. Module switches

```yaml
runtime:
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
    rag_optimization: true
    normalization: true
    snippet_lint: true
    self_checks: true
    fact_checks: true
    lifecycle_management: true
    knowledge_validation: true
    i18n_sync: true
    release_pack: true
```

### Module -> required script in bundle

- `gap_detection` -> `scripts/gap_detector.py`
- `drift_detection` -> `scripts/check_api_sdk_drift.py`
- `docs_contract` -> `scripts/check_docs_contract.py`
- `kpi_sla` -> `scripts/evaluate_kpi_sla.py` + `scripts/generate_kpi_wall.py`
- `normalization` -> `scripts/normalize_docs.py`
- `snippet_lint` -> `scripts/lint_code_snippets.py`
- `self_checks` -> `scripts/check_code_examples_smoke.py`
- `fact_checks` -> `scripts/seo_geo_optimizer.py` + `scripts/doc_layers_validator.py`
- `lifecycle_management` -> `scripts/lifecycle_manager.py` (+ lifecycle report/redirect guidance)
- `knowledge_validation` -> `scripts/extract_knowledge_modules_from_docs.py` + `scripts/validate_knowledge_modules.py`
- `rag_optimization` -> `scripts/generate_knowledge_retrieval_index.py`
- `i18n_sync` -> `scripts/i18n_sync.py`
- `release_pack` -> `scripts/generate_release_docs_pack.py`
- `api-first/hybrid` -> `scripts/run_api_first_flow.py` (+ related api-first scripts)

If script is missing in bundle, module is skipped or warned.

Important: API-first is only one flow branch.
The pipeline supports and generates all major doc types (tutorial/how-to/concept/reference/troubleshooting/release/security/sdk/api/user/admin/runbook), and quality automation applies across them.

## 8. Universal tasks (core UTP, not optional extras)

Use `runtime.custom_tasks.weekly` to wire any command from the capabilities catalog.

```yaml
runtime:
  custom_tasks:
    weekly:
      - id: "geo-lint"
        enabled: true
        command: "python3 docsops/scripts/seo_geo_optimizer.py docs/"
        continue_on_error: true
      - id: "openapi-lint"
        enabled: true
        command: "npm run lint:openapi"
        continue_on_error: true
    on_demand: []
```

Full list of available capabilities:

- `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md`
- regenerate catalog: `python3 scripts/generate_pipeline_capabilities_catalog.py`

## 9. Integrations (single control point)

Use one section to configure cross-stack integrations for any supported generator.

```yaml
runtime:
  integrations:
    algolia:
      enabled: true
      docs_dir: "docs"
      report_output: "reports/seo-report.json"
      upload_on_weekly: true
      app_id_env: "ALGOLIA_APP_ID"
      api_key_env: "ALGOLIA_API_KEY"
      index_name_env: "ALGOLIA_INDEX_NAME"
      index_name_default: "docs"
    ask_ai:
      enabled: true
      auto_configure_on_provision: true
      install_runtime_pack: false
      provider: "openai"
      billing_mode: "user-subscription"
      model: "gpt-4.1-mini"
      base_url: "https://api.openai.com/v1"
```

How it works:

- `algolia.enabled=true`: weekly runner generates Algolia payload from docs.
- `algolia.upload_on_weekly=true`: weekly runner also uploads to Algolia (if env credentials are set).
- `ask_ai.auto_configure_on_provision=true`: provisioning auto-writes `config/ask-ai.yml`.
- `ask_ai.install_runtime_pack=true`: provisioning auto-installs Ask AI runtime pack.

Manual verification for integrations:

- If `algolia.enabled=true`, ensure env names in `runtime.integrations.algolia.*_env` match client secrets naming.
- If `ask_ai.enabled=true`, confirm generated `config/ask-ai.yml` in client repo has expected provider/model/billing mode.

### Core UTP tasks (default-on baseline)

```yaml
runtime:
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
      - id: "intent-all"
        enabled: true
        command: "python3 docsops/scripts/build_all_intent_experiences.py"
        continue_on_error: true
```

### Additional examples

#### SEO/GEO weekly

```yaml
runtime:
  custom_tasks:
    weekly:
      - id: "seo-geo"
        enabled: true
        command: "python3 docsops/scripts/seo_geo_optimizer.py docs/"
        continue_on_error: true
```

#### RAG / knowledge base weekly

```yaml
runtime:
  custom_tasks:
    weekly:
      - id: "knowledge-validate"
        enabled: true
        command: "python3 docsops/scripts/validate_knowledge_modules.py"
        continue_on_error: true
      - id: "knowledge-index"
        enabled: true
        command: "python3 docsops/scripts/generate_knowledge_retrieval_index.py"
        continue_on_error: true
      - id: "intent-all"
        enabled: true
        command: "python3 docsops/scripts/build_all_intent_experiences.py"
        continue_on_error: true
```

#### Multilingual (i18n) baseline

```yaml
runtime:
  modules:
    i18n_sync: true
  custom_tasks:
    weekly:
      - id: "i18n-translate-stale"
        enabled: false
        command: "python3 docsops/scripts/i18n_translate.py --stale-only"
        continue_on_error: true
```

Bundle requirements:

```yaml
bundle:
  include_scripts:
    - "scripts/i18n_sync.py"
    - "scripts/i18n_translate.py"
    - "scripts/i18n_migrate.py"
    - "scripts/i18n_utils.py"
```

Practical mode:

- Keep `i18n_sync` always on (checks coverage/drift for locales).
- Keep auto-translation off by default (`enabled: false`) unless client explicitly wants it.

#### Interactive diagrams assets

```yaml
bundle:
  include_paths:
    - "templates/interactive-diagram.html"
```

#### Search facets index

```yaml
runtime:
  custom_tasks:
    weekly:
      - id: "facets-index"
        enabled: true
        command: "python3 docsops/scripts/generate_facets_index.py --docs-dir docs --output docs/assets/facets-index.json"
        continue_on_error: true
```

#### Algolia push

```yaml
runtime:
  custom_tasks:
    weekly:
      - id: "algolia-upload"
        enabled: true
        command: "python3 docsops/scripts/upload_to_algolia.py"
        continue_on_error: true
```

## 9. Private tuning

```yaml
private_tuning:
  gap_priority_weights:
    business_impact: 0.45
    user_frequency: 0.35
    implementation_cost: 0.20
  stale_days: 21
  weekly_stale_days: 180
  rag_chunk_target_tokens: 420
  verify_max_attempts: 3
```

`weekly_stale_days` default is 180 (half year), configurable per client.

## 10. Legal labeling

```yaml
legal:
  license_type: "commercial"
  redistribution_allowed: false
  reseller_allowed: false
```

Builder generates:

- `LICENSE-COMMERCIAL.md`
- `NOTICE`

## 11. Flow presets (copy-paste)

### Code-first only

```yaml
runtime:
  docs_flow:
    mode: "code-first"
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
```

### API-first only

```yaml
runtime:
  docs_flow:
    mode: "api-first"
  api_first:
    enabled: true
    generate_from_notes: true
```

### Hybrid

```yaml
runtime:
  docs_flow:
    mode: "hybrid"
  api_first:
    enabled: true
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
```

### Full UTP baseline (recommended)

```yaml
runtime:
  docs_flow:
    mode: "hybrid"
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
    rag_optimization: true
    normalization: true
    snippet_lint: true
    knowledge_validation: true
    i18n_sync: true
    release_pack: true
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
```

Default automation order in weekly runner:

\11. extract knowledge modules from docs (`extract_knowledge_modules_from_docs.py`)
\11. validate modules (`validate_knowledge_modules.py`)
\11. regenerate retrieval index (`generate_knowledge_retrieval_index.py`)

## 9. Fully automated RAG/knowledge flow

To run RAG and knowledge base maintenance without manual commands:

\11. Configure once in client profile:

- enable `runtime.modules.knowledge_validation: true`
- enable `runtime.modules.rag_optimization: true`
- add `runtime.custom_tasks.weekly` entries (for example intent experiences)
- include `bundle.include_paths: ["knowledge_modules"]`
- include scripts:
  - `scripts/extract_knowledge_modules_from_docs.py`
  - `scripts/validate_knowledge_modules.py`
  - `scripts/generate_knowledge_retrieval_index.py`

\11. Provision once:

- install bundle with `scripts/provision_client_repo.py`
- install scheduler with `--install-scheduler linux` or `--install-scheduler windows`

\11. Weekly automation then runs by itself:

- scheduler triggers `run_weekly_gap_batch.py`
- it runs `extract_knowledge_modules_from_docs.py`
- it runs `validate_knowledge_modules.py`
- it runs `generate_knowledge_retrieval_index.py`
- it runs all enabled `custom_tasks.weekly`
- it writes consolidated reports

Outcome:

- operators do not run commands manually each week
- operators only review report output and final published docs

## Next steps

- [Documentation index](../index.md)
