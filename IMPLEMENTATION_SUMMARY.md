# Implementation summary

This document describes the current state of the Auto-Doc Pipeline: what is implemented, what each component does, and how the pieces fit together.

## System architecture

The pipeline operates as a documentation operations system with four layers:

```text
Layer 1: Quality enforcement (CI gates on every PR)
Layer 2: Detection (drift, gaps, staleness)
Layer 3: Reporting (KPI, badges, dashboards)
Layer 4: Generation support (templates, variables, AI instructions, verification)
```

## Mandatory PR gates (4 workflows)

These workflows run on every pull request. If any gate fails, the PR cannot merge.

| Gate | Workflow | What it checks |
| --- | --- | --- |
| Docs quality | `docs-check.yml` | Vale style (American English, Google Guide, write-good), markdownlint formatting, cspell spelling, frontmatter schema, SEO/GEO optimization. Auto-detects MkDocs or Docusaurus. |
| PR DoD contract | `pr-dod-contract.yml` | If interface files changed (controllers, routes, models), docs must change in the same PR. |
| API/SDK drift | `api-sdk-drift-gate.yml` | If OpenAPI specs or SDK code changed, corresponding reference docs must update. Creates issues on drift. |
| Code examples smoke | `code-examples-smoke.yml` | Executes fenced code blocks tagged `smoke` in 8 languages: Python, Bash, JavaScript, TypeScript, Go, curl, JSON, YAML. |

## Supporting automation (8 workflows)

These workflows run on schedule or on specific triggers.

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `ci-documentation.yml` | Push to main | Full validation sweep across all docs. |
| `kpi-wall.yml` | Weekly (Monday) | Generates quality score, staleness %, gap count, WOW trends, SVG badges. |
| `release-docs-pack.yml` | Release event | Packages release-specific documentation artifacts. |
| `docs-ops-e2e.yml` | Push to main | Runs end-to-end pipeline validation (51 tests). |
| `lifecycle-management.yml` | Weekly | Scans for stale/deprecated pages, creates issues, proposes draft PRs. |
| `openapi-source-sync.yml` | Push with OpenAPI changes | Resolves API spec from api-first or code-first strategy. |
| `algolia-index.yml` | Deploy (optional) | Uploads search records to Algolia with robust payload handling. |
| `changelog.yml` | Release event | Generates automated release notes. |

## Command surface

### Validation commands

| Command | What it does |
| --- | --- |
| `npm run validate:minimal` | Vale + markdownlint + frontmatter validation |
| `npm run validate:full` | All checks including SEO/GEO and code snippets |
| `npm run lint:md` | Markdownlint only |
| `npm run lint:frontmatter` | Frontmatter schema validation only |
| `npm run lint:geo` | SEO/GEO optimization checks only |
| `npm run lint:examples-smoke` | Code example execution only |
| `npm run lint:snippets` | Code snippet linting only |
| `npm run lint:snippets:strict` | Strict code snippet linting |

### Contract and drift commands

| Command | What it does |
| --- | --- |
| `npm run docs-contract` | PR interface-to-docs contract check |
| `npm run drift-check` | API/SDK drift detection |

### Reporting commands

| Command | What it does |
| --- | --- |
| `npm run kpi-wall` | Generate KPI dashboard |
| `npm run kpi-sla` | Evaluate KPI against SLA thresholds |
| `npm run kpi-full` | KPI wall + badges combined |
| `npm run badges` | Generate SVG badge images |
| `npm run release-pack` | Generate release documentation pack |
| `npm run gaps` | Run gap detection |

### Site generator commands

| Command | What it does |
| --- | --- |
| `npm run generator:detect` | Show which generator is active |
| `npm run generator:info` | Detailed generator information |
| `npm run build` | Build site (auto-detect generator) |
| `npm run serve` | Start preview server (auto-detect) |
| `npm run build:mkdocs` | Build with MkDocs explicitly |
| `npm run build:docusaurus` | Build with Docusaurus explicitly |
| `npm run serve:mkdocs` | Preview with MkDocs |
| `npm run serve:docusaurus` | Preview with Docusaurus |
| `npm run convert:to-docusaurus` | Convert MkDocs Markdown to Docusaurus |
| `npm run convert:to-mkdocs` | Convert Docusaurus Markdown to MkDocs |

### Setup and utility commands

| Command | What it does |
| --- | --- |
| `npm run configurator` | Generate browser-based setup wizard |
| `npm run new-doc` | Create new document from template |
| `npm run api:sandbox:mock` | Start mock API sandbox from OpenAPI spec |
| `npm run api:sandbox:stop` | Stop mock API sandbox |

### Test commands

| Command | What it does |
| --- | --- |
| `npm run docs-ops:e2e` | End-to-end tests |
| `npm run docs-ops:golden` | Golden file comparison tests |
| `npm run docs-ops:test-suite` | Full test suite (51 tests across 15 classes) |
| `npm run test:adapter` | Docusaurus adapter tests (25 tests) |
| `npm run test:configurator` | GUI configurator tests (7 tests) |

## Scripts inventory (35+)

### Core validation scripts

| Script | Purpose |
| --- | --- |
| `validate_frontmatter.py` | Validates Markdown frontmatter against `docs-schema.yml` |
| `seo_geo_optimizer.py` | 60+ SEO/GEO checks with optional auto-fix |
| `lint_code_snippets.py` | Code block syntax and structure validation |
| `check_code_examples_smoke.py` | Executes tagged code blocks in 8 languages |
| `doc_layers_validator.py` | Diataxis framework layer integrity checks |

### Contract and drift scripts

| Script | Purpose |
| --- | --- |
| `check_docs_contract.py` | PR-level interface-to-docs contract enforcement |
| `check_api_sdk_drift.py` | API/SDK change vs docs synchronization |
| `validate_pr_dod.py` | Definition of Done contract checks |

### Reporting scripts

| Script | Purpose |
| --- | --- |
| `generate_kpi_wall.py` | KPI dashboard with 8+ metrics and WOW trends |
| `evaluate_kpi_sla.py` | KPI threshold evaluation against policy pack SLA |
| `generate_badge.py` | SVG badge generation from KPI data |
| `generate_release_docs_pack.py` | Release-specific documentation packaging |
| `pilot_analysis.py` | Pilot program impact analysis and debt scoring |

### Gap detection scripts

| Script | Purpose |
| --- | --- |
| `gap_detector.py` | Unified entry point for gap analysis |
| `gap_detection/code_analyzer.py` | Code/doc mismatch detection |
| `gap_detection/community_collector.py` | Community-source signal collection |
| `gap_detection/algolia_parser.py` | Search-failure pattern analysis |
| `gap_detection/gap_aggregator.py` | Multi-signal prioritization |
| `gap_detection/batch_generator.py` | Batch issue and report generation |
| `gap_detection/cli.py` | Modular gap detection CLI |

### Site generator scripts

| Script | Purpose |
| --- | --- |
| `site_generator.py` | ABC with auto-detection, factory method |
| `markdown_converter.py` | Bidirectional MkDocs/Docusaurus Markdown conversion |
| `generate_docusaurus_config.py` | Nav-to-sidebar conversion and config generation |
| `preprocess_variables.py` | `{{ variable }}` replacement for Docusaurus |
| `run_generator.py` | Auto-detecting CLI wrapper for build/serve/detect |

### Setup scripts

| Script | Purpose |
| --- | --- |
| `init_pipeline.py` | Bootstrap pipeline in new repositories with generator choice |
| `generate_configurator.py` | Browser-based GUI wizard (6-step configuration) |
| `new_doc.py` | Create new document from templates |
| `auto_metadata.py` | Automatic metadata enrichment |

### Lifecycle and search scripts

| Script | Purpose |
| --- | --- |
| `lifecycle_manager.py` | Draft/active/deprecated/archived state tracking |
| `upload_to_algolia.py` | Algolia search record upload |
| `generate_facets_index.py` | Client-side faceted search index generation |
| `algolia_config.py` | Algolia configuration management |

## Policy packs (5)

| Pack | Use case | Quality % | Max stale % | Max gaps | Max drop |
| --- | --- | --- | --- | --- | --- |
| `minimal.yml` | Pilot, new teams | 75 | 20 | 10 | 8 |
| `api-first.yml` | OpenAPI-driven products | 82 | 12 | 6 | 4 |
| `monorepo.yml` | Multi-service repos | 80 | 15 | 8 | 6 |
| `multi-product.yml` | Product families | 80 | 15 | 8 | 6 |
| `plg.yml` | Product-led growth | 85 | 10 | 5 | 3 |

## Templates (27)

All templates in `templates/` are pre-validated to pass Vale, markdownlint, frontmatter validation, and SEO/GEO checks. See `README.md` for the full template list.

## AI documentation support

### Instruction files

- `CLAUDE.md`: 1200+ lines of instructions for Claude Code including Stripe-quality standards, template enforcement, shared variables mandate, self-verification with auto-correction, and 16-step generation flow.
- `AGENTS.md`: Same instructions adapted for Codex.

### AI workflow

1. Select template (never write from scratch).
1. Use shared variables from `_variables.yml`.
1. Generate content following Stripe-quality standards.
1. Execute all code blocks and verify output.
1. Fact-check all assertions (versions, ports, paths).
1. Auto-correct any errors found.
1. Replace hardcoded values with variables.
1. Update navigation in `mkdocs.yml`.
1. Log verification summary.

### Variables system

`docs/_variables.yml` is the single source of truth for all product-specific values. Documents use `{{ variable_name }}` syntax. The macros plugin substitutes variables at build time.

## Configuration files

| File | Purpose |
| --- | --- |
| `.vale.ini` | Style enforcement: American English, Google Guide, write-good |
| `.markdownlint.yml` | Markdown formatting rules |
| `cspell.json` | Spelling dictionary with 200+ custom terms |
| `docs-schema.yml` | Frontmatter JSON Schema validation |
| `mkdocs.yml` | MkDocs Material theme configuration |
| `.pre-commit-config.yaml` | Pre-commit hook framework |
| `package.json` | npm scripts (49 commands) |
| `Makefile` | Make shortcuts for common operations |

## Site generator abstraction

The pipeline supports MkDocs and Docusaurus via a unified abstraction:

- Auto-detection from config files (`mkdocs.yml` vs `docusaurus.config.js`).
- Bidirectional Markdown conversion (admonitions, tabs, frontmatter).
- Generator-agnostic validation scripts.
- Docusaurus scaffold with config templates, CSS, and React components.

## GUI configurator

`scripts/generate_configurator.py` generates a self-contained HTML wizard at `reports/pipeline-configurator.html` with 6 steps:

1. Policy pack selection.
1. Variable editing.
1. Generator choice.
1. KPI threshold tuning.
1. Live preview.
1. Export as files or batch download.

## Operational readiness

The pipeline is ready for service delivery:

- Baseline measurement with `pilot_analysis.py`.
- Pilot execution with daily/weekly validation cadence.
- Executive reporting with before/after KPI comparison.
- GUI configurator for client self-service.
- See `PILOT_VS_FULL_IMPLEMENTATION.md` for delivery modes.
- See `CUSTOMIZATION_PER_COMPANY.md` for per-client configuration.
- See `OPERATOR_RUNBOOK.md` for execution steps.
