# Auto-Doc Pipeline

An automated documentation operations system for technical products.

Install it into a company repository. It enforces documentation quality, detects when docs fall behind code, generates consolidated reports, and enables LLM assistants (Claude Code, Codex) to produce Stripe-quality documentation from the first draft with built-in self-verification.

## How the pipeline works

```text
Monday 09:00 UTC (cron)
        |
        v
weekly-consolidation.yml runs:
  gaps (code + community + algolia) -> doc_gaps_report.json
  API/SDK drift                     -> api_sdk_drift_report.json
  KPI wall                          -> kpi-wall.json
  SLA evaluation                    -> kpi-sla-report.json
        |
        v
consolidate_reports.py merges 4 reports
        |
        v
reports/consolidated_report.json + GitHub Issue created
        |
        v
User: git pull -> Claude Code -> "Process reports/consolidated_report.json"
        |
        v
LLM prioritizes (3 tiers), creates/updates docs, self-verifies, lints
        |
        v
User: reviews diffs (git diff), commits
```

### Consolidated weekly report

The `scripts/consolidate_reports.py` script merges four input reports into a single `reports/consolidated_report.json`. The `weekly-consolidation.yml` workflow runs every Monday at 09:00 UTC, commits the consolidated report to the repository, and opens a GitHub Issue with instructions for the next documentation cycle.

Input reports:

| Report | Source | Content |
| --- | --- | --- |
| `doc_gaps_report.json` | Code changes, community signals, Algolia search analytics | Missing or outdated documentation |
| `api_sdk_drift_report.json` | OpenAPI spec and SDK diff against docs | API and SDK reference drift |
| `kpi-wall.json` | Quality scoring across all docs | Quality score, staleness, metadata completeness |
| `kpi-sla-report.json` | KPI wall evaluated against policy pack thresholds | SLA breaches and compliance status |

### LLM-driven documentation generation

When Claude Code or Codex processes the consolidated report, it:

1. Prioritizes action items into three tiers (critical, important, routine).
1. Selects the matching template from `templates/` (never writes from scratch).
1. Uses variables from `docs/_variables.yml` for all product-specific values.
1. Follows Vale style rules (American English, active voice, no weasel words).
1. Self-verifies: executes all code examples, checks shell commands, fact-checks assertions (versions, ports, paths, counts).
1. Auto-corrects any mismatches found during verification.
1. Updates `mkdocs.yml` navigation when adding new pages.
1. Runs linters before committing.

Instructions live in `CLAUDE.md` (for Claude Code) and `AGENTS.md` (for Codex).

## Quality gates

### CI/CD: docs-check.yml (7 parallel checks + build)

Every pull request that touches `docs/` triggers seven parallel checks:

| Check | Tool | What it validates |
| --- | --- | --- |
| Style | Vale | American English, Google Developer Style Guide, write-good |
| Formatting | markdownlint | Markdown structure, blank lines, heading hierarchy |
| Spelling | cspell | Technical terms, product names, code identifiers |
| Frontmatter | `validate_frontmatter.py` | Required metadata fields, character limits, schema |
| SEO/GEO | `seo_geo_optimizer.py` | 60+ checks for search and LLM optimization |
| Code examples | `check_code_examples_smoke.py` | Executes tagged code blocks in 8 languages |
| API specs | Spectral | OpenAPI/Swagger spec validation |

All seven checks must pass before the `build-docs` job runs (`mkdocs build --strict` or `npx docusaurus build`).

### Pre-commit hooks (6 checks)

The `.husky/pre-commit` hook runs on every commit with staged `.md` files:

1. Spectral (API specs, if staged)
1. Vale (style)
1. markdownlint (formatting)
1. cspell (spelling)
1. Frontmatter validation
1. GEO optimization

### Additional CI workflows

| Workflow | Trigger | Purpose |
| --- | --- | --- |
| `weekly-consolidation.yml` | Cron Monday 09:00 UTC / manual | Generate consolidated report, open GitHub Issue |
| `pr-dod-contract.yml` | PR | Block if interface changed but docs did not |
| `api-sdk-drift-gate.yml` | PR | Block if OpenAPI/SDK changed without doc updates |
| `code-examples-smoke.yml` | PR | Execute all tagged code blocks |
| `kpi-wall.yml` | Weekly | Quality score, staleness, gap count dashboard |
| `release-docs-pack.yml` | Release published | Generate documentation package for the release |
| `lifecycle-management.yml` | Weekly | Scan for stale/deprecated pages, create issues |
| `openapi-source-sync.yml` | Schedule | Resolve API spec (api-first or code-first strategy) |
| `algolia-index.yml` | Deploy | Upload search index to Algolia |

## Templates (31)

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

Plus four additional specialized templates in the `templates/` directory.

## Policy packs (5)

Policy packs adapt quality thresholds and enforcement rules to different team sizes and product strategies:

| Pack | Best for | Quality threshold | Max stale % |
| --- | --- | --- | --- |
| `minimal.yml` | New teams, pilot week | 75% | 20% |
| `api-first.yml` | OpenAPI-driven teams, SDK-heavy products | 82% | 12% |
| `monorepo.yml` | Multiple services in one repo | 80% | 15% |
| `multi-product.yml` | One docs system for multiple products | 80% | 15% |
| `plg.yml` | Product-led growth, self-serve activation | 85% | 10% |

## Workflows

### API-first workflow

For teams that start with an OpenAPI spec:

1. Write or update `api/openapi.yaml`.
1. OpenAPI Generator produces SDK stubs and reference scaffolds.
1. Prism mock server provides a sandbox for `Try it out` in docs.
1. `api-sdk-drift-gate.yml` blocks PRs if specs change without doc updates.

### Code-first workflow

For teams that start with code:

1. `npm run gaps:code` scans recent commits for interface changes.
1. Real endpoint testing validates documented behavior.
1. Gap detector produces prioritized backlog of missing docs.

### Doc layers validator

`scripts/doc_layers_validator.py` checks that every documented feature has the required layers (concept, how-to, reference) based on the active policy pack.

### Lifecycle management

Documents have four states: `active`, `deprecated`, `removed`, and draft. Deprecated and removed pages require `deprecated_since`, `removal_date`, and `replacement_url` in frontmatter. Removed pages get `noindex: true` to prevent search engine indexing.

## Variables system

All company-specific values live in `docs/_variables.yml`. Documents reference variables instead of hardcoding values:

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

## Site generator support

The pipeline supports two documentation site generators:

1. **MkDocs** (default): Uses `mkdocs.yml` with Material theme. Preview at `http://127.0.0.1:8000`.
1. **Docusaurus**: Uses `docusaurus.config.js`, React-based. Preview at `http://localhost:3000`.

Auto-detection based on which config file exists. Bidirectional Markdown conversion between formats.

### Algolia search integration

Optional Algolia integration for faceted search. Configure credentials in `mkdocs.yml` under `extra.algolia`. The `algolia-index.yml` workflow uploads the search index on deploy.

## Key npm commands

```bash
# Weekly consolidation (the main pipeline command)
npm run consolidate          # Run gaps + KPI + SLA + consolidate into one report
npm run consolidate:reports-only  # Consolidate existing reports without regenerating

# Gap detection
npm run gaps                 # Analyze documentation gaps
npm run gaps:full            # Full gap analysis with doc generation
npm run gaps:code            # Code-first gap detection
npm run gaps:community       # Community signal analysis

# Quality checks
npm run lint                 # Run all 6 linters (Vale, markdownlint, cspell, frontmatter, SEO/GEO, snippets)
npm run validate:minimal     # Core checks (markdownlint, frontmatter, SEO/GEO, code examples)
npm run validate:full        # All checks + e2e + golden tests + test suite

# Reporting
npm run kpi-wall             # Generate KPI dashboard
npm run kpi-sla              # Evaluate KPIs against SLA thresholds
npm run drift-check          # Check API/SDK drift
npm run badges               # Generate SVG badges from KPI data
npm run release-pack         # Generate release documentation package

# Build and serve
npm run build                # Build docs (auto-detects MkDocs or Docusaurus)
npm run serve                # Start local preview server

# Utilities
npm run new-doc              # Create new doc from template
npm run configurator         # Generate browser-based setup wizard
npm run generator:detect     # Check which site generator is active
```

## Test coverage

Automated tests across multiple test suites:

```bash
npm run docs-ops:test-suite  # Main test suite
npm run docs-ops:e2e         # End-to-end pipeline validation
npm run docs-ops:golden      # Golden report comparison tests
npm run test:adapter         # Docusaurus adapter tests
npm run test:configurator    # GUI configurator tests
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
