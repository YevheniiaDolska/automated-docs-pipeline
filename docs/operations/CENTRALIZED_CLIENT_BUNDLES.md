---
title: "Централизованная настройка клиентов"
description: "Практический путь настройки клиентских bundle и автозапуска pipeline из одного места."
content_type: reference
product: both
last_reviewed: "2026-03-11"
tags:
  - Operations
  - Client Onboarding
---

<!-- cspell:disable -->
# Централизованная настройка клиентов (очень просто)

Это схема, где вы настраиваете все в одном месте, а клиент работает локально как раньше.

## Главное правило

- Вы запускаете `scripts/onboard_client.py` в своем мастер-репо.
- Скрипт создает/обновляет `profiles/clients/generated/<client_id>.client.yml`.
- Если клиентский репо доступен на этой же машине, скрипт сразу ставит `bundle` в локальный клон клиентского репо.
- Если у вас и у клиента разные ноутбуки, вы собираете `bundle` у себя и передаете клиенту для установки в `docsops/`.
- Клиент дальше просто работает локально через Claude Code / Codex.

## Что именно вы настраиваете (и где)

Один файл клиента: `profiles/clients/<client>.client.yml`.

Полный справочник:

- `docs/operations/UNIFIED_CLIENT_CONFIG.md`
- `docs/operations/PLAN_TIERS.md` (готовые планы Basic/Pro/Enterprise)
- `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md` (полный список доступных команд/плюшек)

### 1) Пути в конкретном репо клиента

```yaml
runtime:
  docs_root: "docs"
  api_root: "openapi"
  sdk_root: "clients"
```

Если у клиента другой layout, меняете только эти 3 строки.

### 2) Какие генераторы документации нужны

```yaml
runtime:
  output_targets: ["sphinx", "readme", "github"]
```

Примеры:

- только Sphinx: `["sphinx"]`
- только ReadMe: `["readme"]`
- смешанный вариант: `["sphinx", "readme"]`

### 2.1) Как выбрать flow: code-first / api-first / hybrid

```yaml
runtime:
  docs_flow:
    mode: "hybrid"
```

- `code-first`: стандартный docs-ops поток
- `api-first`: API-first поток
- `hybrid`: оба потока одновременно

### 3) Какие функции включены

Есть 2 уровня переключения:

\11. Логические флаги для LLM:

```yaml
runtime:
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
    rag_optimization: true
    terminology_management: true
    lifecycle_management: true
```

\11. Практический набор скриптов в bundle:

```yaml
bundle:
  include_scripts:
    - "scripts/check_docs_contract.py"
    - "scripts/check_api_sdk_drift.py"
```

Если функция не нужна, убираете флаг и соответствующий скрипт.

По умолчанию baseline включен:

- self-checks
- multi-language tabs generation/validation for code examples
- fact/style checks
- lifecycle checks/reports
- SEO/GEO
- RAG/knowledge index
- terminology sync to glossary (`sync_project_glossary.py`)
- drift/contract/KPI-SLA

Ключевые возможности (ваше основное УТП) включаются через:

```yaml
runtime:
  custom_tasks:
    weekly:
      - id: "openapi-lint"
        enabled: true
        command: "npm run lint:openapi"
        continue_on_error: true
```

Это не `редкие спецзадачи`, а базовый контур docs-ops платформы. В том числе:

- SEO/GEO (`seo_geo_optimizer.py`)
- RAG/knowledge index (`generate_knowledge_retrieval_index.py`)
- glossary sync (`sync_project_glossary.py`)
- интент-бандлы (`build_all_intent_experiences.py`)
- мультиязычные табы кода (`generate_multilang_tabs.py` + `validate_multilang_examples.py`)
- i18n sync/translate
- интерактивные диаграммы (через `bundle.include_paths`)
- Algolia upload
- любые другие скрипты/команды из полного каталога

### 3.2) API-first advanced controls (manual overrides + regression gate)

```yaml
runtime:
  api_first:
    enabled: true
    openapi_version: "3.1.0"
    manual_overrides_path: "api/overrides/openapi.manual.yml"
    regression_snapshot_path: "api/.openapi-regression.json"
    update_regression_snapshot: false
```

Для этого в `bundle.include_scripts` должны быть:

- `scripts/apply_openapi_overrides.py`
- `scripts/check_openapi_regression.py`

### 3.1) Централизованные интеграции (Algolia + Ask AI)

```yaml
runtime:
  integrations:
    algolia:
      enabled: true
      upload_on_weekly: true
      app_id_env: "ALGOLIA_APP_ID"
      api_key_env: "ALGOLIA_API_KEY"
      index_name_env: "ALGOLIA_INDEX_NAME"
    ask_ai:
      enabled: true
      auto_configure_on_provision: true
      install_runtime_pack: false
      provider: "openai"
      billing_mode: "user-subscription"
      model: "gpt-4.1-mini"
```

Что это дает:

- Algolia работает одинаково для всех поддерживаемых site generators.
- Ask AI настраивается автоматически во время provisioning (без ручных CLI-команд).

### 4) Насколько строгие правила качества

```yaml
bundle:
  base_policy_pack: "multi-product"
  policy_overrides:
    kpi_sla:
      min_doc_coverage: 85
```

- `base_policy_pack` = базовый режим
- `policy_overrides` = тонкая докрутка под клиента

### 4.1) Как выбрать style guide (Vale)

```yaml
bundle:
  style_guide: "google" # google | microsoft | hybrid
```

Сборщик сам положит `.vale.ini` в bundle под выбранный профиль.

### 5) Автовставка блока в AGENTS/CLAUDE

```yaml
bundle:
  llm:
    codex_instructions_source: "AGENTS.md"
    claude_instructions_source: "CLAUDE.md"
    inject_managed_block: true
    docsops_root_in_client_repo: "docsops"
```

Сборщик автоматически положит в bundle:

- `AGENTS.md`
- `CLAUDE.md`

И добавит в оба файла управляемый блок с инструкцией читать:

- `docsops/config/client_runtime.yml`
- `docsops/policy_packs/selected.yml`

## Команда сборки

```bash
cd "C:/Users/Kroha/Documents/development/Auto-Doc Pipeline"
python3 scripts/build_client_bundle.py --client profiles/clients/blockstream-demo.client.yml
```

Результат:

```text
generated/client_bundles/blockstream-demo/
```

### Два режима установки

1. На одной машине (у вас есть путь к клиентскому репо): используете `provision_client_repo.py`, scheduler ставится сразу.

1. На разных ноутбуках: вы собираете bundle командой выше, клиент кладет bundle в `<client-repo>/docsops`, затем клиент ставит scheduler локально:

```bash
bash docsops/ops/install_cron_weekly.sh
```

Windows:

```bash
powershell -ExecutionPolicy Bypass -File docsops/ops/install_windows_task.ps1
```

Scheduler использует локальную таймзону машины, где установлен. Если установлен на клиентском ноутбуке, Monday run идет по времени клиента.

Быстрый старт по пресетам:

- `profiles/clients/presets/small.yml`
- `profiles/clients/presets/startup.yml`
- `profiles/clients/presets/enterprise.yml`

Самый быстрый запуск:

```bash
python3 scripts/onboard_client.py
```

Скрипт задает вопросы, создает клиентский профиль, собирает bundle, ставит в клиентский репозиторий и устанавливает scheduler.
`onboard_client.py` остается в вашем мастер-репо и не включается в клиентский bundle по умолчанию.

Перед установкой вы видите preview профиля и подтверждаете запуск.

## Команда "под ключ" (без возни клиента)

Если вы хотите сразу настроить и запускать за клиента, используйте provisioning:

```bash
python3 scripts/provision_client_repo.py \
  --client profiles/clients/blockstream-demo.client.yml \
  --client-repo /path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler linux
```

Для Windows:

```bash
python3 scripts/provision_client_repo.py \
  --client profiles/clients/blockstream-demo.client.yml \
  --client-repo C:/path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler windows
```

Что делает команда:

\11. Собирает bundle из клиентского профиля.
\11. Копирует bundle в репозиторий клиента (`docsops/`).
\11. Генерирует `docsops/ENV_CHECKLIST.md` автоматически.
\11. Ставит weekly scheduler (cron или Task Scheduler).
\11. Клиенту не нужно руками настраивать pipeline.

### Ручная проверка оператора (после установки)

\11. Проверить `<client-repo>/docsops/config/client_runtime.yml`.
\11. Проверить `<client-repo>/docsops/policy_packs/selected.yml`.
\11. Проверить `<client-repo>/docsops/ENV_CHECKLIST.md` и передать список env/secrets клиенту.
\11. Убедиться, что scheduler установлен (cron entry или Task Scheduler task).
\11. Запустить один тестовый weekly run и убедиться, что `reports/consolidated_report.json` обновился.

## Как это ставится клиенту

Клиент кладет папку bundle в свой репо, например:

```text
<client-repo>/docsops/
```

Там уже будут:

- `config/client_runtime.yml`
- `policy_packs/selected.yml`
- `scripts/...`
- `AGENTS.md`
- `CLAUDE.md`
- `LICENSE-COMMERCIAL.md`
- `NOTICE`
- `ops/run_weekly_docsops.sh` / `ops/run_weekly_docsops.ps1`
- `ops/install_cron_weekly.sh` / `ops/install_windows_task.ps1`
- `ops/runbook.md`

## Не ломает ли это локальный опыт?

Не ломает.

- Клиент по-прежнему работает локально.
- LLM читает локальные `AGENTS.md`/`CLAUDE.md`.
- Все проверки и генерация выполняются локально в репо клиента.
- Еженедельный отчёт формируется по расписанию автоматически.

## Еженедельный автоматический поток

Скрипт `docsops/scripts/run_weekly_gap_batch.py` по расписанию:

\11. Собирает gap report за последние 7 дней.
\11. Проверяет stale-доки (по умолчанию 180 дней без изменений).
\11. Запускает KPI/SLA (если включено в bundle).
\11. При `mode=api-first|hybrid` запускает API-first flow (если включено в `runtime.api_first.enabled`).
\11. Применяет manual overrides к OpenAPI артефактам (если задан `manual_overrides_path`).
\11. Проверяет regression snapshot (если задан `regression_snapshot_path`).
\11. Генерирует и валидирует мультиязычные вкладки кода (новый стандарт).
\11. Выполняет smoke-проверки кода и сверяет `expected-output` (если указан).
\11. Запускает `runtime.custom_tasks.weekly` (если включены).
\11. Создает `reports/consolidated_report.json`.

Важно: API-first здесь только один из подпроцессов. Главный контур охватывает все типы документации и quality automation целиком.

Порог stale можно менять для каждого клиента:

- `private_tuning.weekly_stale_days` в `profiles/clients/<client>.client.yml`

Дальше оператор или команда:

\11. Передает consolidated report локальной LLM для batch generation.
\11. Делает быстрый визуальный финальный просмотр готовых docs.

## Что добавить в `.gitignore` клиента

Рекомендуемый минимум:

```gitignore
reports/docsops-weekly.log
```

Это локальный лог планировщика. Его обычно не коммитят.

JSON/Markdown отчеты (`reports/consolidated_report.json` и связанные отчеты) обычно оставляют в репозитории, если команда ведет историю отчетов в git.

## RAG/knowledge без ручных запусков

Это уже укладывается в текущий smooth flow:

\11. Один раз настроить профиль клиента (`*.client.yml`):

- `runtime.modules.knowledge_validation: true`
- `runtime.modules.rag_optimization: true`
- `runtime.custom_tasks.weekly` для RAG-задач, включая `build_all_intent_experiences.py`
- `bundle.include_paths: ["knowledge_modules"]`

\11. Один раз сделать provisioning:

- `provision_client_repo.py` ставит `docsops/` в клиентский репозиторий
- сразу ставится расписание (`cron` или `Task Scheduler`)

\11. Далее weekly job идет автоматически:

- запускается `run_weekly_gap_batch.py`
- внутри выполняются:
  - `extract_knowledge_modules_from_docs.py`
  - `validate_knowledge_modules.py`
  - `generate_knowledge_retrieval_index.py`
  - любые `custom_tasks.weekly` (например `build_all_intent_experiences.py`)
- отчеты формируются автоматически

Итог:

- клиентская команда не запускает команды вручную
- человек только смотрит weekly report и выборочно проверяет финальные docs

Поведение отчетов:

- weekly запуск пишет в те же имена файлов
- новые отчеты заменяют старые
- ручное удаление старых отчетов не требуется

Как клиенту быстро понять, что отчет новый (самый простой способ):

\11. В проводнике/Finder/файловом менеджере найти `reports/consolidated_report.json`.
\11. Посмотреть `Modified` (дата/время изменения файла).
\11. Если `Modified` свежее (после планового запуска), отчет новый и готов к передаче локальной LLM.

Этого достаточно. Открывать дополнительные файлы не нужно.

Дополнительные тех-маркеры (опционально):

- `reports/READY_FOR_REVIEW.txt`
- `reports/docsops_status.json`

## Два простых примера

### Клиент 1: только Sphinx, без drift

```yaml
runtime:
  output_targets: ["sphinx"]
  modules:
    gap_detection: true
    drift_detection: false
    docs_contract: true
    kpi_sla: true
    rag_optimization: true
    terminology_management: true
bundle:
  include_scripts:
    - "scripts/check_docs_contract.py"
    - "scripts/evaluate_kpi_sla.py"
    - "scripts/sync_project_glossary.py"
```

### Клиент 2: ReadMe + GitHub, очень строгий quality bar

```yaml
runtime:
  output_targets: ["readme", "github"]
bundle:
  base_policy_pack: "plg"
  policy_overrides:
    kpi_sla:
      min_doc_coverage: 90
      max_quality_score_drop: 2
```

Вы меняете только профиль YAML. Код пайплайна не трогаете.

## Next steps

- [Documentation index](../index.md)
