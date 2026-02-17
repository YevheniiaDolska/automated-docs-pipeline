# Documentation Pipeline Setup Guide

## What This System Is

This repository is a unified documentation operations system.
It combines technical writing workflows, quality gates, SEO/GEO optimization,
metadata governance, gap detection, and reporting in one pipeline.

The goal is not random AI drafting.
The goal is repeatable, high-quality documentation output with measurable
business impact.

## Quick Start (Windows PowerShell)

### 1. Install Python and dependencies

```powershell
# From project root
cd "C:\Users\Kroha\Documents\development\Auto-Doc Pipeline"

python --version
# If this prints Python 3.x, continue.

pip install -r requirements.txt
```

### 2. Verify core scripts

Run these from project root:

```powershell
python3 scripts\validate_frontmatter.py docs
python3 scripts\doc_layers_validator.py docs
python3 scripts\seo_geo_optimizer.py docs
python3 scripts\gap_detector.py
python3 scripts\new_doc.py --help
python3 scripts\lifecycle_manager.py --help
python3 scripts\generate_facets_index.py --help
python3 scripts\upload_to_algolia.py --help
```

If you are in the `scripts` folder, return to root first:

```powershell
cd ..
```

### 3. Run quality checks

```powershell
npm install
npm run lint:md
npm run lint:frontmatter
npm run lint:seo
```

### 4. Build and preview docs

```powershell
mkdocs serve
# http://127.0.0.1:8000

mkdocs build
```

## Core Capabilities

### Content system

- Diataxis-aligned templates for tutorials, how-to guides, concepts, and reference docs.
- Specialized templates for API, integration, security, testing, configuration, and webhooks.
- Reusable variables via `docs/_variables.yml` to keep content consistent.

### Quality system

- Style and clarity checks (Vale + write-good).
- Markdown structure checks (`markdownlint`).
- Frontmatter schema validation.
- Documentation-layer validation for structural quality.
- API quality checks (Spectral, where applicable).
- Optional spelling checks (`cspell`).

### Growth and discoverability system

- SEO/GEO checks with actionable recommendations.
- Metadata completeness validation.
- Faceted search index generation.
- Optional Algolia integration for scale.

### Governance and planning system

- Gap detection from code deltas, stale docs, and community signals.
- Lifecycle tracking for documentation freshness.
- Pilot analysis with before/after KPI reporting.

## Recommended Daily Workflow

1. Draft or update docs using templates and snippets.
1. Run local quality gates before commit.
1. Open PR and let CI re-run checks.
1. Review gap reports and prioritize high-impact updates.
1. Track publish speed, quality, and support outcomes.

## Troubleshooting

### `ModuleNotFoundError: No module named 'yaml'`

Run:

```powershell
pip install PyYAML
```

Then verify:

```powershell
python3 -c "import yaml; print('PyYAML OK')"
```

### `python` works but npm scripts fail

Use `python3` in shell and ensure `package.json` lint commands reference `python3`.

### `vale` command not found

Install Vale and sync styles:

```powershell
vale --version
vale sync
```

Then run:

```powershell
vale docs templates
```

## What Good Looks Like

A healthy setup means:

- docs checks pass locally and in CI.
- new content follows templates and shared variables.
- metadata is complete and valid.
- markdownlint has no blocking violations in active documentation paths.
- SEO/GEO checks produce actionable, low-noise recommendations.
- gap reports generate clear, prioritized work items.
