# Auto-Doc Pipeline

An automated documentation operations system for technical products.

Install it into a company repository. It enforces documentation quality, detects when docs fall behind code, generates consolidated reports, and enables LLM assistants (Claude Code, Codex) to produce high-quality documentation from the first draft with built-in self-verification.

## How the pipeline works

```text
One-time setup:
  onboard_client.py (or provision_client_repo.py) -> profile + bundle + install + scheduler
        |
        v
Weekly scheduler runs:
  docsops/scripts/run_weekly_gap_batch.py
    -> gaps, drift, KPI/SLA, stale checks
    -> knowledge validation + retrieval index
    -> optional api-first flow + custom weekly tasks
        |
        v
reports/consolidated_report.json
        |
        v
LLM: "Process reports/consolidated_report.json"
        |
        v
LLM prioritizes (3 tiers), creates/updates docs, self-verifies, lints
        |
        v
User: reviews diffs (git diff), commits
```

Compatibility mode:
- You can still run the same weekly flow via GitHub Actions cron (`weekly-consolidation.yml` and related workflows).

### Consolidated weekly report

`scripts/consolidate_reports.py` merges source reports into `reports/consolidated_report.json`.

In recommended mode, this is executed by scheduled `docsops/scripts/run_weekly_gap_batch.py` in the client repo.
In compatibility mode, this can also be executed by `weekly-consolidation.yml` in GitHub Actions.

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
1. Selects the matching template from `templates/`.
1. If a required doc type has no template yet, creates a new Stripe-quality template in the same project format, then generates docs from that template.
1. Uses variables from `docs/_variables.yml` for product-specific values.
1. Adds missing variable keys to `docs/_variables.yml` when needed (instead of hardcoding values in pages).
1. Updates navigation when adding new pages (`mkdocs.yml` or target provider equivalent).
1. Handles multilingual flow through English-source-first content, then i18n sync/translate workflow for target locales.
1. Follows Vale style rules (American English, active voice, no weasel words).
1. Runs SEO/GEO optimization checks and applies fixes where possible.
1. Runs RAG/knowledge steps when enabled (`validate_knowledge_modules.py`, `generate_knowledge_retrieval_index.py`, intent assembly tasks).
1. Self-verifies: executes all code examples, checks shell commands, fact-checks assertions (versions, ports, paths, counts).
1. Auto-corrects any mismatches found during verification.
1. Runs lint/validation locally before commit (pre-commit and explicit lint commands).
1. Runs the same checks again in CI on pull request; publish/merge stays blocked until green.
1. Publishes/syncs to configured targets (Sphinx, ReadMe, GitHub docs, optional adapters) according to client profile.

Instructions live in `CLAUDE.md` (for Claude Code) and `AGENTS.md` (for Codex).

## Intelligent knowledge system layer

The pipeline includes an AI-native knowledge layer that keeps docs readable while enabling structured retrieval and dynamic assembly.

| Artifact | Purpose |
| --- | --- |
| `knowledge_modules/*.yml` | Modular knowledge units with intent, audience, channel, and dependency metadata |
| `knowledge-module-schema.yml` | Contract for module structure and metadata integrity |
| `scripts/extract_knowledge_modules_from_docs.py` | Auto-splits docs into audience/intent-ready knowledge modules with metadata |
| `scripts/validate_knowledge_modules.py` | Quality gate for module schema, dependencies, and cycle safety |
| `scripts/assemble_intent_experience.py` | Assembles intent experiences into docs pages and channel bundles |
| `scripts/generate_knowledge_retrieval_index.py` | Builds a module-level retrieval index for assistants and search |
| `scripts/sync_project_glossary.py` | Syncs glossary markers into `glossary.yml` for terminology governance |

```bash
npm run lint:knowledge
npm run build:intent -- --intent configure --audience operator --channel docs
npm run build:knowledge-index
```

## Quality gates

### CI/CD: docs-check.yml (7 parallel checks + build)

Every pull request that touches `docs/` triggers seven parallel checks:

| Check | Tool | What it validates |
| --- | --- | --- |
| Style | Vale | American English + selected style profile (`google`/`microsoft`/`hybrid`) + write-good |
| Formatting | markdownlint | Markdown structure, blank lines, heading hierarchy |
| Spelling | cspell | Technical terms, product names, code identifiers |
| Frontmatter | `validate_frontmatter.py` | Required metadata fields, character limits, schema for Markdown docs frontmatter (`docs/**/*.md`) |
| SEO/GEO | `seo_geo_optimizer.py` | 24 automated checks (8 GEO + 16 SEO) for search and LLM optimization |
| Code examples | `check_code_examples_smoke.py` | Executes tagged code blocks in 8 languages |
| API specs | Spectral | OpenAPI/Swagger spec validation |

All seven checks must pass before the `build-docs` job runs (`mkdocs build --strict` or `npx docusaurus build`).

`knowledge_modules/*.yml` do not go through `validate_frontmatter.py`; they are validated separately by `validate_knowledge_modules.py` (schema, dependencies, cycle safety).

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
| `admin-guide.md` | Admin and operations procedures |
| `api-endpoint.md` | Single-endpoint API documentation |
| `upgrade-guide.md` | Upgrade and compatibility guidance |
| `user-guide.md` | End-user product usage guide |

## Policy packs (5)

Policy packs adapt quality thresholds and enforcement rules to different team sizes and product strategies:

| Pack | Best for | Quality threshold | Max stale % |
| --- | --- | --- | --- |
| `minimal.yml` | New teams, pilot week | 75% | 20% |
| `api-first.yml` | OpenAPI-driven teams, SDK-heavy products | 82% | 12% |
| `monorepo.yml` | Multiple services in one repo | 80% | 15% |
| `multi-product.yml` | One docs system for multiple products | 84% | 10% |
| `plg.yml` | Product-led growth, self-serve activation | 84% | 10% |

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

`scripts/doc_layers_validator.py` checks that every documented feature has the required layers (concept, how-to, reference) from the active policy pack (`policy_packs/selected.yml` in client bundles).

### Lifecycle management

Documents have four states: `active`, `deprecated`, `removed`, and `draft`.
`validate_frontmatter.py` enforces lifecycle rules automatically:
- `deprecated` and `removed` pages must include `deprecated_since`, `removal_date`, and `replacement_url`.
- `removed` pages must include `noindex: true` to prevent search engine indexing.
Weekly automation also runs `lifecycle_manager.py` to generate lifecycle reports and redirect/cleanup guidance.

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

The pipeline supports the most widely used docs site generators out of the box:

1. **MkDocs** (default): Uses `mkdocs.yml` with Material theme. Preview at `http://127.0.0.1:8000`.
1. **Docusaurus**: Uses `docusaurus.config.js`, React-based. Preview at `http://localhost:3000`.
1. **Sphinx**: Uses `conf.py`. Build output at `_build/html`; preview with local server at `http://127.0.0.1:8000`.
1. **Hugo**: Uses `hugo.toml` (or `config.toml/yaml`). Preview at `http://localhost:1313`.
1. **Jekyll**: Uses `_config.yml`. Preview at `http://127.0.0.1:4000`.

In addition, client profiles can target multiple publication channels via `runtime.output_targets`
(for example `sphinx`, `readme`, `github`) while keeping one shared docs-ops workflow.
Those targets are configured in client runtime/policy and executed by the corresponding project adapters/tasks.

Auto-detection based on which config file exists. Bidirectional Markdown conversion between formats.

### Algolia search integration

Algolia integration is generator-agnostic (MkDocs, Docusaurus, Sphinx, Hugo, Jekyll):
- records are generated from docs frontmatter/content via pipeline scripts
- upload is handled by `upload_to_algolia.py`
- configuration lives in one place: `runtime.integrations.algolia` in the client profile

No generator-specific `mkdocs.yml` edits are required for pipeline indexing/upload.

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
npm run build                # Build docs (auto-detects supported generators)
npm run serve                # Start local preview server

# Utilities
npm run onboard:client       # One-command client onboarding wizard (profile + bundle + install)
npm run new-doc              # Create new doc from template
npm run configurator         # Generate browser-based setup wizard
npm run generator:detect     # Check which site generator is active
npm run askai:status         # Show Ask AI module config
npm run askai:enable         # Enable Ask AI with current config
npm run askai:disable        # Disable Ask AI
npm run askai:configure -- --provider openai --billing-mode user-subscription
npm run askai:runtime:install # Install optional Ask AI runtime pack (API + widget)
```

Operator verification after onboarding:
1. Check generated profile: `profiles/clients/generated/<client_id>.client.yml`.
1. Check installed runtime config: `<client-repo>/docsops/config/client_runtime.yml`.
1. Check installed policy: `<client-repo>/docsops/policy_packs/selected.yml`.
1. Check env checklist: `<client-repo>/docsops/ENV_CHECKLIST.md`.

Ask AI is optional and disabled by default.
For client bundles, configure it centrally in `runtime.integrations.ask_ai` (client profile):
- provisioning auto-applies `config/ask-ai.yml`
- optional runtime pack install is controlled by `install_runtime_pack`

Manual CLI setup remains available with `npm run askai:configure -- --help`.

## Test coverage

Automated tests across multiple test suites:

```bash
npm run docs-ops:test-suite  # Main test suite
npm run docs-ops:e2e         # End-to-end pipeline validation
npm run docs-ops:golden      # Golden report comparison tests
npm run test:adapter         # Docusaurus adapter tests
npm run test:configurator    # GUI configurator tests
npm run test:all             # Full pytest suite (standardized invocation)
```

Use `python3 -m pytest ...` (or `npm run test:all`) instead of bare `pytest ...` to avoid environment-specific import edge cases.

## Start here

| Your situation | Read this first |
| --- | --- |
| Never used this before | `quick-start.md` |
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
