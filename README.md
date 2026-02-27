# Auto-Doc Pipeline

An automated documentation operations system for technical products.

You install it into a company repository. It enforces documentation quality, detects when docs fall behind code, generates reports, and helps AI assistants (Claude, Codex) produce Stripe-quality documentation from the first draft.

## What this system does (plain language)

Imagine you have a software product with documentation. This pipeline does the following:

1. **Checks every document for quality** before it merges. Grammar, style, spelling, formatting, SEO, metadata. If something is wrong, the pull request fails until the author fixes it.
1. **Detects when code changes but docs do not.** If a developer changes an API endpoint and does not update the reference docs, the pipeline blocks the PR and tells them what to update.
1. **Runs code examples from docs to verify they work.** If a tutorial says `print(2 + 2)` and claims the output is 5, the pipeline catches it. Supports Python, Bash, JavaScript, TypeScript, Go, JSON, YAML, and curl.
1. **Finds documentation gaps automatically.** It scans code changes, community signals, search analytics, and existing docs to produce a prioritized backlog of what needs to be written.
1. **Produces KPI dashboards and reports.** Quality scores, staleness percentages, gap counts, week-over-week trends, and SVG badges for your README.
1. **Manages document lifecycle.** Tracks draft, active, deprecated, and archived states. Automatically creates issues when pages go stale.
1. **Helps AI write better docs.** The `CLAUDE.md` and `AGENTS.md` files contain detailed instructions that make Claude and Codex produce documentation that passes all quality gates on the first attempt, using templates, shared variables, and self-verification.
1. **Supports two site generators.** MkDocs (default) and Docusaurus, with automatic detection and bidirectional Markdown conversion between formats.
1. **Includes an interactive API sandbox.** Swagger UI or Redoc embedded in docs, with configurable `Try it out` routing to sandbox or production.
1. **Ships with 27 production-ready templates.** Tutorials, how-to guides, API references, troubleshooting pages, quickstarts, changelogs, glossaries, and 20 more. Each template passes all linters out of the box.

## How it works (the flow)

```text
Developer changes code
        |
        v
Opens Pull Request
        |
        v
4 mandatory CI gates run automatically:
  1. docs-check.yml        -> style, formatting, spelling, frontmatter, SEO/GEO
  2. pr-dod-contract.yml   -> if interface changed, docs must change too
  3. api-sdk-drift-gate.yml -> if OpenAPI/SDK changed, reference docs must update
  4. code-examples-smoke.yml -> all tagged code blocks must execute without errors
        |
        v
If any gate fails -> PR is blocked with clear error message
If all gates pass -> PR can merge
        |
        v
Supporting automation runs on schedule:
  - KPI dashboard generation (weekly)
  - Gap detection (weekly)
  - Lifecycle management (weekly)
  - Algolia search indexing (on deploy)
```

## What is included

### Quality gates (mandatory on every PR)

1. **Docs quality gate** (`docs-check.yml`): Vale style checks (American English, Google Developer Style Guide, write-good), markdownlint formatting, cspell spelling, frontmatter schema validation, SEO/GEO optimization checks. Auto-detects MkDocs or Docusaurus.
1. **PR DoD contract** (`pr-dod-contract.yml`): If interface files changed (controllers, routes, models) and docs did not change, the PR fails.
1. **API/SDK drift gate** (`api-sdk-drift-gate.yml`): If OpenAPI specs or SDK code changed without corresponding reference docs updates, the PR fails. Creates GitHub issues for unresolved drift.
1. **Code examples smoke** (`code-examples-smoke.yml`): Executes fenced code blocks tagged with `smoke` in eight languages: Python, Bash, JavaScript, TypeScript, Go, curl, JSON, YAML.

### Supporting automation (runs on schedule or triggers)

1. **CI documentation sweep** (`ci-documentation.yml`): Full validation across all docs.
1. **KPI wall** (`kpi-wall.yml`): Weekly quality score, staleness, gap count, and trend dashboard.
1. **Release docs pack** (`release-docs-pack.yml`): Generates documentation package for each release.
1. **E2E test suite** (`docs-ops-e2e.yml`): End-to-end pipeline validation.
1. **Lifecycle management** (`lifecycle-management.yml`): Scans for stale/deprecated pages, creates issues, proposes draft PRs.
1. **OpenAPI source sync** (`openapi-source-sync.yml`): Resolves API spec from api-first or code-first strategy.
1. **Algolia indexing** (`algolia-index.yml`): Optional search index upload.
1. **Changelog** (`changelog.yml`): Automated release note generation.

### Scripts (35+)

| Category | Scripts | What they do |
| --- | --- | --- |
| Validation | `validate_frontmatter.py`, `seo_geo_optimizer.py`, `lint_code_snippets.py`, `check_code_examples_smoke.py`, `doc_layers_validator.py` | Check quality, formatting, SEO, code validity |
| Contracts | `check_docs_contract.py`, `check_api_sdk_drift.py`, `validate_pr_dod.py` | Enforce docs-as-code contracts |
| Reporting | `generate_kpi_wall.py`, `evaluate_kpi_sla.py`, `generate_badge.py`, `generate_release_docs_pack.py`, `pilot_analysis.py` | Produce dashboards, badges, reports |
| Gap detection | `gap_detector.py`, `gap_detection/` (6 modules) | Find missing docs from code, search, community |
| Site generation | `site_generator.py`, `markdown_converter.py`, `generate_docusaurus_config.py`, `preprocess_variables.py`, `run_generator.py` | Build, serve, convert between MkDocs and Docusaurus |
| Setup | `init_pipeline.py`, `generate_configurator.py`, `new_doc.py`, `auto_metadata.py` | Bootstrap pipeline, generate GUI wizard, create docs from templates |
| Lifecycle | `lifecycle_manager.py` | Track draft/active/deprecated/archived states |
| Search | `upload_to_algolia.py`, `generate_facets_index.py` | Optional Algolia integration |

### Templates (27)

Pre-validated Markdown templates that pass all linters out of the box:

| Template | Purpose |
| --- | --- |
| `tutorial.md` | Step-by-step learning guides |
| `how-to.md` | Task-oriented guides |
| `concept.md` | Explanation and understanding pages |
| `reference.md` | Technical specification pages |
| `troubleshooting.md` | Problem-cause-solution guides |
| `quickstart.md` | 5-10 minute onboarding |
| `api-reference.md` | API endpoint documentation |
| `authentication-guide.md` | Auth pattern documentation |
| `migration-guide.md` | Version upgrade guides |
| `deployment-guide.md` | Production setup guides |
| `webhooks-guide.md` | Webhook integration docs |
| `sdk-reference.md` | SDK client library docs |
| `security-guide.md` | Security policy docs |
| `configuration-guide.md` | Configuration setup docs |
| `configuration-reference.md` | Config options table |
| `integration-guide.md` | Third-party integration docs |
| `testing-guide.md` | Testing approach docs |
| `error-handling-guide.md` | Error codes and recovery |
| `architecture-overview.md` | System architecture docs |
| `best-practices.md` | Guidelines and patterns |
| `use-case.md` | Business use-case pages |
| `release-note.md` | Version changelog |
| `changelog.md` | Release notes format |
| `faq.md` | Frequently asked questions |
| `glossary-page.md` | Terminology reference |
| `plg-persona-guide.md` | PLG persona targeting |
| `plg-value-page.md` | PLG value proposition |

### Policy packs (5)

Policy packs adapt the pipeline to different companies and team sizes:

| Pack | Best for | Quality threshold | Max stale % |
| --- | --- | --- | --- |
| `minimal.yml` | New teams, pilot week, restricted environments | 75% | 20% |
| `api-first.yml` | OpenAPI-driven teams, SDK-heavy products | 82% | 12% |
| `monorepo.yml` | Multiple services in one repo | 80% | 15% |
| `multi-product.yml` | One docs system for multiple products | 80% | 15% |
| `plg.yml` | Product-led growth, self-serve activation | 85% | 10% |

### Variables system

All company-specific values live in one file: `docs/_variables.yml`. Every document references variables instead of hardcoding values. When you change the port number or product name, it updates across all docs automatically.

```yaml
# docs/_variables.yml
product_name: "Acme API"
default_port: 5678
cloud_url: "https://app.acme.com"
api_version: "v2"
support_email: "support@acme.com"
```

In documentation:

```markdown
Run {{ product_name }} on port {{ default_port }}.
Visit [{{ product_name }} Cloud]({{ cloud_url }}).
```

## Local commands

### With Make

```bash
make install            # Install all dependencies
make validate-minimal   # Run core quality checks
make validate-full      # Run all quality checks
make test               # Run test suite
make docs-serve         # Start documentation preview
make configurator       # Generate browser-based setup wizard
```

### With npm (cross-platform, no Make required)

```bash
npm install                     # Install dependencies
npm run validate:minimal        # Core quality checks
npm run validate:full           # All quality checks
npm run docs-ops:test-suite     # Run 51 tests
npm run serve                   # Start docs preview (auto-detects generator)
npm run configurator            # Generate setup wizard
npm run gaps                    # Run gap detection
npm run kpi-wall                # Generate KPI dashboard
```

## Site generator support

The pipeline supports two documentation site generators:

1. **MkDocs** (default): Uses `mkdocs.yml`, Material theme. Preview at `http://127.0.0.1:8000`.
1. **Docusaurus**: Uses `docusaurus.config.js`, React-based. Preview at `http://localhost:3000`.

The pipeline auto-detects which generator to use based on which config file exists.

```bash
npm run generator:detect          # Check active generator
npm run convert:to-docusaurus     # Switch from MkDocs to Docusaurus
npm run convert:to-mkdocs         # Switch from Docusaurus to MkDocs
```

## AI documentation workflow

The pipeline includes two instruction files that make AI assistants produce high-quality docs:

1. **`CLAUDE.md`**: Instructions for Claude Code. Covers templates, variables, self-verification, formatting rules, and Stripe-quality standards.
1. **`AGENTS.md`**: Instructions for Codex. Same content adapted for Codex workflow.

When Claude or Codex generates documentation in this repository, they:

1. Select the matching template from `templates/` (never write from scratch).
1. Use variables from `docs/_variables.yml` for all product-specific values.
1. Follow Vale style rules (American English, active voice, no weasel words).
1. Execute all code examples and verify output matches documentation.
1. Fact-check all specific claims (versions, ports, paths, counts).
1. Auto-correct any mismatches found during verification.
1. Update `mkdocs.yml` navigation when adding new pages.

## Test coverage

51 automated tests across 15 test classes:

```bash
npm run docs-ops:test-suite     # Main test suite
npm run test:adapter            # 25 Docusaurus adapter tests
npm run test:configurator       # 7 GUI configurator tests
```

## Start here

| Your situation | Read this first |
| --- | --- |
| Never used this before | `QUICK_START.md` |
| Windows user starting from zero | `BEGINNER_GUIDE.md` |
| Setting up for the first time | `README_SETUP.md` |
| Installing into another repository | `SETUP_FOR_PROJECTS.md` |
| Private repository | `PRIVATE_REPO_SETUP.md` |
| Running a pilot week for a client | `PILOT_VS_FULL_IMPLEMENTATION.md` |
| Customizing for a specific company | `CUSTOMIZATION_PER_COMPANY.md` |
| API-first team workflow | `API_FIRST_PLAYBOOK.md` |
| Product-led growth docs | `PLG_PLAYBOOK.md` |
| Understanding policy packs | `POLICY_PACKS.md` |
| Team daily usage | `USER_GUIDE.md` |
| Implementation delivery | `OPERATOR_RUNBOOK.md` |
| Full feature inventory | `PACKAGE_CONTENTS.md` |

## Security

Read `SECURITY_OPERATIONS.md` before enabling automation in a company repository.

Key rule: secrets live only in CI secret stores, never in code or config files.
