# Implementation summary

This document describes everything currently implemented in the Auto-Doc Pipeline.

## Architecture

The pipeline operates as a 4-layer documentation operations system:

1. **Quality enforcement** -- 7 linters run on every PR (Vale style, markdownlint, cspell, frontmatter schema, SEO/GEO, code examples smoke, snippet syntax).
1. **Detection** -- API/SDK drift detection, interface-to-docs contract enforcement, gap analysis with 3-tier prioritization.
1. **Reporting** -- KPI dashboard with week-over-week trends, SVG badges, SLA evaluation against policy packs.
1. **Generation support** -- 31 templates, shared variables, AI instructions (Claude Code and Codex), self-verification with auto-correction.

## Scripts (35+)

All scripts are in `scripts/` and `scripts/gap_detection/`. They cover:

- **Validation**: `validate_frontmatter.py`, `seo_geo_optimizer.py` (60+ checks), `lint_code_snippets.py`, `check_code_examples_smoke.py` (8 languages), `doc_layers_validator.py`.
- **Contract and drift**: `check_docs_contract.py`, `check_api_sdk_drift.py`, `validate_pr_dod.py`.
- **Reporting**: `generate_kpi_wall.py`, `evaluate_kpi_sla.py`, `generate_badge.py`, `generate_release_docs_pack.py`, `pilot_analysis.py`.
- **Gap detection**: `gap_detector.py`, `code_analyzer.py`, `community_collector.py`, `algolia_parser.py`, `gap_aggregator.py`, `batch_generator.py`.
- **Site generators**: `site_generator.py`, `markdown_converter.py`, `generate_docusaurus_config.py`, `preprocess_variables.py`, `run_generator.py`.
- **Setup**: `init_pipeline.py`, `generate_configurator.py`, `new_doc.py`, `auto_metadata.py`.
- **Lifecycle and search**: `lifecycle_manager.py`, `upload_to_algolia.py`, `generate_facets_index.py`, `algolia_config.py`.

## Templates (31)

Pre-validated templates in `templates/` covering: tutorials, how-to guides, concepts, references, troubleshooting, quickstarts, API references, SDK references, webhooks, authentication, configuration, error handling, integration, migration, security, testing, changelogs, release notes, FAQs, glossaries, use cases, PLG persona guides, and PLG value pages.

## Workflows (21)

All workflows are in `.github/workflows/`. Four mandatory PR gates block merges if quality, contract, drift, or code example checks fail. Supporting automation includes weekly KPI generation, lifecycle management, release documentation packaging, end-to-end tests (51 tests), OpenAPI sync, Algolia indexing, and changelog generation.

## Policy packs (5)

Quality threshold configurations in `policy_packs/`: minimal (75%), api-first (82%), monorepo (80%), multi-product (80%), and plg (85%).

## Consolidated report

The gap detection system produces a single consolidated report that combines signals from code analysis, community questions, search failures, and API changes. Every gap is ranked into 3 tiers (critical, high, medium) so documentation work targets the highest-impact gaps first.

## Self-verification

AI-generated documentation goes through a mandatory self-verification pass: code block execution, fact-checking (versions, ports, paths), hardcoded value replacement with shared variables, and internal consistency checks. This reduces human review cycles from 5+ rounds to 1-2.

## Lifecycle management

Documents track states (draft, active, deprecated, archived) with automated alerts. The `lifecycle-management.yml` workflow scans for stale and deprecated pages weekly and creates GitHub issues.

## Configuration files

`.vale.ini`, `.markdownlint.yml`, `cspell.json`, `docs-schema.yml`, `mkdocs.yml`, `.pre-commit-config.yaml`, `package.json` (49 npm commands), and `Makefile`.

## Related guides

| Guide | What it covers |
| --- | --- |
| `PACKAGE_CONTENTS.md` | File-by-file manifest |
| `GETTING_STARTED_ZERO_TO_PRO.md` | Feature walkthrough |
| `CUSTOMIZATION_PER_COMPANY.md` | Per-company configuration |
