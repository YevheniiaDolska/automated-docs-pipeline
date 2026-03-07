---
title: "Auto-Doc Pipeline implementation summary"
description: "Review the implemented architecture, scripts, templates, workflows, and policy packs in the Auto-Doc Pipeline."
content_type: reference
product: both
tags:
  - Reference
  - AI
last_reviewed: "2026-03-07"
---

# Implementation summary

This reference summarizes what the Auto-Doc Pipeline currently implements across validation,
gap detection, reporting, generation, and governance.

## Architecture

The pipeline operates as a 4-layer documentation operations system:

1. **Quality enforcement** -- Seven linters run on every PR:
   Vale style, markdownlint, cspell, frontmatter schema, SEO/GEO, code examples smoke,
   and snippet syntax.
1. **Detection** -- API/SDK drift detection, interface-to-docs contract enforcement,
   and gap analysis with three-tier prioritization.
1. **Reporting** -- KPI dashboards with week-over-week trends, SVG badges,
   and SLA evaluation against policy packs.
1. **Generation support** -- 31 templates, shared variables, AI instructions
   (Claude Code and Codex), and self-verification with auto-correction.

## Scripts (35+)

All scripts are in `scripts/` and `scripts/gap_detection/`. They cover:

- **Validation**: `validate_frontmatter.py`, `seo_geo_optimizer.py` (60+ checks),
  `lint_code_snippets.py`, `check_code_examples_smoke.py` (8 languages),
  `doc_layers_validator.py`.
- **Contract and drift**: `check_docs_contract.py`, `check_api_sdk_drift.py`, `validate_pr_dod.py`.
- **Reporting**: `generate_kpi_wall.py`, `evaluate_kpi_sla.py`, `generate_badge.py`, `generate_release_docs_pack.py`, `pilot_analysis.py`.
- **Gap detection**: `gap_detector.py`, `code_analyzer.py`, `community_collector.py`, `algolia_parser.py`, `gap_aggregator.py`, `batch_generator.py`.
- **Site generators**: `site_generator.py`, `markdown_converter.py`, `generate_docusaurus_config.py`, `preprocess_variables.py`, `run_generator.py`.
- **Setup**: `init_pipeline.py`, `generate_configurator.py`, `new_doc.py`, `auto_metadata.py`.
- **Lifecycle and search**: `lifecycle_manager.py`, `upload_to_algolia.py`,
  `generate_facets_index.py`, and `algolia_config.py`.

## Templates (31)

Pre-validated templates in `templates/` cover tutorials, how-to guides, concepts,
references, troubleshooting, quickstarts, API references, SDK references, webhooks,
authentication, configuration, error handling, integration, migration, security, testing,
changelogs, release notes, FAQs, glossaries, use cases, PLG persona guides,
and PLG value pages.

## Workflows (21)

All workflows are in `.github/workflows/`. Four mandatory PR gates block merges
if quality, contract, drift, or code example checks fail. Supporting automation includes
weekly KPI generation, lifecycle management, release docs packaging, end-to-end tests
(51 tests), OpenAPI sync, Algolia indexing, and changelog generation.

## Policy packs (5)

Quality threshold configurations in `policy_packs/`: minimal (75%), api-first (82%), monorepo (80%), multi-product (80%), and plg (85%).

## Consolidated report

The gap detection system produces one consolidated report that combines signals from
code analysis, community questions, search failures, and API changes. Every gap is ranked
into three tiers (critical, high, and medium), so documentation work targets high-impact gaps first.

## Intelligent knowledge system

The pipeline now supports a modular knowledge layer for AI-native retrieval and dynamic experience assembly.

- Source modules are stored in `knowledge_modules/*.yml`.
- Schema and integrity checks run through `knowledge-module-schema.yml`
  and `validate_knowledge_modules.py`.
- Intent-specific pages and channel bundles are assembled via `assemble_intent_experience.py`.
- Module-level retrieval records are generated to
  `docs/assets/knowledge-retrieval-index.json` for search and assistant ingestion.

## Self-verification

AI-generated documentation goes through a mandatory self-verification pass:
code block execution, fact-checking (versions, ports, paths), hardcoded value replacement
with shared variables, and internal consistency checks. This reduces review cycles
from five or more rounds to one or two.

## Lifecycle management

Documents track states (draft, active, deprecated, and archived) with automated alerts.
The `lifecycle-management.yml` workflow scans for stale and deprecated pages weekly
and creates GitHub issues.

## Configuration files

`.vale.ini`, `.markdownlint.yml`, `cspell.json`, `docs-schema.yml`, `mkdocs.yml`,
`.pre-commit-config.yaml`, `package.json` (49 npm commands), and `Makefile`.

## Related guides

| Guide | What it covers |
| --- | --- |
| [Package contents](./PACKAGE_CONTENTS.md) | File-by-file manifest |
| [Getting started: zero to pro](./GETTING_STARTED_ZERO_TO_PRO.md) | Feature walkthrough |
| [Customization per company](./CUSTOMIZATION_PER_COMPANY.md) | Per-company configuration |
