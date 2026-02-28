# Pilot week vs full implementation

This guide explains the two delivery modes for the Auto-Doc Pipeline: a one-week pilot and a full implementation. It covers what each mode includes, how to set them up, and whether you need separate repositories.

## Do you need two separate repositories?

**No.** You do not need two separate repositories. Both pilot and full implementation use the same codebase. The difference is which features you enable and which policy pack you select.

Think of it like this:

- **Pilot week** = same pipeline, but you enable only the core features (`minimal.yml` policy pack).
- **Full implementation** = same pipeline, but you enable all features and use a stricter policy pack (`api-first.yml`, `plg.yml`, or a custom pack).

The pipeline is designed to scale from pilot to full by changing configuration, not by switching repositories.

## Comparison table

| Aspect | Pilot week | Full implementation |
| --- | --- | --- |
| Duration | 5 business days | 2-4 weeks |
| Policy pack | `minimal.yml` | `api-first.yml`, `plg.yml`, or custom |
| CI gates enabled | docs-check only | All 4 mandatory gates |
| Gap detection | Baseline scan only | Full gap analysis with backlog |
| KPI reporting | Before/after snapshot | Weekly dashboard with trends |
| Templates | 3-5 core templates adapted | All 27 templates customized |
| Variables | Basic product info only | Full variable set |
| AI instructions | Standard CLAUDE.md | Customized with company style |
| Site generator | MkDocs default | MkDocs or Docusaurus (client choice) |
| API sandbox | Not included | Optional, if client has OpenAPI |
| Algolia search | Not included | Optional |
| Lifecycle management | Not enabled | Enabled with thresholds |
| Training | Self-serve guides | Hands-on walkthrough |

## Pilot week: step by step

The pilot week proves value on the client's real repository in five days. The goal is a measurable before/after comparison.

Before Day 1, determine which starting point you have:

1. **Fresh client repository**: the pipeline is not installed yet.
1. **Existing pipeline repository**: the repo already contains `scripts/`, `templates/`, `package.json`, and the workflow files.

If it is a fresh repository, bootstrap it first from the client repository root:

```bash
python3 /path/to/Auto-Doc\ Pipeline/scripts/init_pipeline.py \
  --product-name "Client Product" \
  --generator mkdocs \
  --target-dir .
```

### Day 1: Setup and baseline

**What you do:**

1. Fork or clone the client's documentation repository.
1. Create an implementation branch.
1. Install the pipeline dependencies if the repository already contains the pipeline files.

```bash
python3 -m pip install -r requirements.txt
npm install
```

1. Choose the `minimal.yml` policy pack (the most lenient profile).
1. Update workflow files that still point to `policy_packs/api-first.yml` if you want the repo to truly run in pilot mode:
   - `.github/workflows/pr-dod-contract.yml`
   - `.github/workflows/api-sdk-drift-gate.yml`
   - `.github/workflows/kpi-wall.yml`

1. Run baseline measurement:

```bash
python3 scripts/pilot_analysis.py --json > reports/pilot-baseline.json
python3 scripts/generate_kpi_wall.py --docs-dir docs --reports-dir reports --stale-days 90
python3 scripts/evaluate_kpi_sla.py \
  --current reports/kpi-wall.json \
  --policy-pack policy_packs/minimal.yml \
  --json-output reports/kpi-sla-report.json \
  --md-output reports/kpi-sla-report.md
```

1. Save baseline numbers: quality score, stale docs count, gap count.

**What you configure in `docs/_variables.yml`:**

```yaml
product_name: "Client Product Name"
product_full_name: "Client Product full description"
current_version: "1.0.0"
cloud_url: "https://app.client-product.com"
docs_url: "https://docs.client-product.com"
default_port: 8080
support_email: "support@client.com"
```

### Day 2: Enable core quality gate

**What you do:**

1. Enable the `docs-check.yml` workflow (the only mandatory gate for pilot).
1. Fix the most critical formatting and frontmatter issues across existing docs.
1. Run validation:

```bash
npm run validate:minimal
npm run lint
```

1. Adapt 3-5 templates to the client's product context:
   - `quickstart.md` (their onboarding flow)
   - `how-to.md` (their most common task)
   - `troubleshooting.md` (their top support issue)
   - `api-reference.md` (if they have an API)
   - `tutorial.md` (if they have a getting-started guide)

1. Copy each template to the appropriate docs folder:

```bash
cp templates/quickstart.md docs/getting-started/quickstart.md
cp templates/how-to.md docs/how-to/common-task.md
```

1. Edit each copied template: replace placeholder text with actual product content. Use variables from `_variables.yml`.

### Day 3: Generate sample docs with AI

**What you do:**

1. Use Claude or Codex with the `CLAUDE.md`/`AGENTS.md` instructions to generate 2-3 documents.
1. The AI follows the instructions automatically: selects template, uses variables, verifies code examples, fact-checks assertions.
1. Run validation on generated docs:

```bash
npm run validate:minimal
```

1. Review AI-generated content for factual accuracy (the AI self-verifies, but human review is still recommended for the pilot).

### Day 4: Run gap detection and fix issues

**What you do:**

1. Run gap detection to identify missing documentation:

```bash
npm run gaps
```

1. Review the gap report. Prioritize by severity.
1. Fix the top 3-5 gaps using templates.
1. Run fuller validation:

```bash
npm run validate:full
```

If that is too heavy for a five-day pilot, the minimum acceptable report set is:

```bash
npm run validate:minimal
npm run gaps
npm run kpi-wall
```

### Day 5: Generate final report and deliver

**What you do:**

1. Run the same measurements as Day 1:

```bash
python3 scripts/pilot_analysis.py --json > reports/pilot-final.json
python3 scripts/generate_kpi_wall.py --docs-dir docs --reports-dir reports --stale-days 90
npm run kpi-full
```

1. Compare baseline vs final numbers.
1. Generate KPI badges:

```bash
npm run badges
```

1. Prepare executive summary with:
   - Quality score: before vs after.
   - Stale docs: before vs after.
   - Gaps found and resolved.
   - Documents generated by AI vs time spent.
   - Recommendation for full implementation.

### Pilot week deliverables

1. Before/after KPI comparison.
1. 3-5 adapted templates.
1. 2-3 AI-generated documents.
1. Gap backlog with priorities.
1. Executive summary report.
1. Recommendation for full implementation scope.

### Pilot definition of done

The pilot is complete when:

1. Core quality gates run in CI for target docs paths.
1. Team can generate new docs from templates in minutes.
1. Metadata and frontmatter validation are active and passing.
1. SEO/GEO report is generated with prioritized recommendations.
1. Gap detection produces actionable, ranked backlog items.
1. At least one before/after KPI is documented and reviewed with the client.

## Full implementation: step by step

The full implementation builds on the pilot. It enables all pipeline features and customizes them for the client's workflow.

### Week 1: Foundation (same as pilot, but thorough)

1. Complete all pilot steps.
1. Enable all four mandatory CI gates:
   - `docs-check.yml`
   - `pr-dod-contract.yml`
   - `api-sdk-drift-gate.yml`
   - `code-examples-smoke.yml`

1. Choose the appropriate policy pack:
   - API-heavy product: `api-first.yml`
   - Self-serve product: `plg.yml`
   - Multiple services: `monorepo.yml`
   - Multiple products: `multi-product.yml`

1. Or create a custom policy pack (see `CUSTOMIZATION_PER_COMPANY.md`).
1. Update workflow files so they reference the chosen policy pack instead of the default `policy_packs/api-first.yml` where applicable.

### Week 2: Templates and variables

1. Customize all 27 templates to the client's product.
1. Build the full `docs/_variables.yml` with all product-specific values:

```yaml
# Product identity
product_name: "Client Product"
product_full_name: "Client Product - Enterprise Automation Platform"
product_tagline: "Automate everything"
company_name: "Client Corp"

# Versions
current_version: "3.2.1"
min_supported_version: "2.8.0"
api_version: "v2"

# URLs
cloud_url: "https://app.clientproduct.com"
docs_url: "https://docs.clientproduct.com"
github_url: "https://github.com/clientcorp/clientproduct"
status_page_url: "https://status.clientproduct.com"
community_url: "https://community.clientproduct.com"

# Support
support_email: "support@clientcorp.com"
sales_email: "sales@clientcorp.com"

# Technical defaults
default_port: 8080
default_data_folder: "~/.clientproduct"

# Environment variables
env_vars:
  port: "CLIENT_PORT"
  webhook_url: "CLIENT_WEBHOOK_URL"
  api_key: "CLIENT_API_KEY"
  database_url: "CLIENT_DATABASE_URL"

# Limits
max_payload_size_mb: 32
rate_limit_requests_per_minute: 120

# Branding
copyright_year: 2026
```

1. Update `CLAUDE.md` and `AGENTS.md` with client-specific style rules if needed.

### Week 3: Automation and reporting

1. Enable supporting workflows:
   - KPI wall (weekly schedule).
   - Lifecycle management (weekly scan).
   - Gap detection (weekly).
   - Release docs pack (on release).

1. Configure Algolia search (optional):
   - Set up Algolia account.
   - Add API keys to repository secrets.
   - Enable `algolia-index.yml` workflow.

1. Configure API sandbox (optional):
   - Add OpenAPI spec to the repository.
   - Enable `openapi-source-sync.yml`.
   - Configure API playground in `mkdocs.yml`.

1. Set up KPI SLA thresholds in the policy pack.
1. Confirm the policy pack used by `.github/workflows/kpi-wall.yml`.

### Week 4: Training and handoff

1. Train the team on daily workflow:
   - How to create docs from templates.
   - How to run local validation.
   - How to read gap reports.
   - How to interpret KPI dashboards.

1. Train AI workflow:
   - How Claude/Codex uses `CLAUDE.md`/`AGENTS.md`.
   - How self-verification works.
   - How to review AI-generated content.

1. Generate final KPI dashboard and comparison report.
1. Document the client-specific configuration for future reference.

### Full implementation deliverables

1. All 4 mandatory CI gates active.
1. Full variable set in `_variables.yml`.
1. All relevant templates customized.
1. Supporting automation enabled (KPI, lifecycle, gaps).
1. Client-specific policy pack (or adapted built-in pack).
1. Team training completed.
1. KPI baseline and current comparison.
1. Optional: Algolia search, API sandbox, PLG docs.

### Full implementation definition of done

1. All mandatory CI gates pass on PRs.
1. Team can run local validation without operator support.
1. Site generator is chosen and builds in strict mode.
1. Baseline and current KPI reports are generated.
1. GUI configurator is delivered to the client.
1. Security operations checklist is adopted.
1. At least 10 documents have been generated using templates.
1. Gap backlog is under active management.

## How to switch from pilot to full

After a successful pilot, converting to full implementation requires:

1. **Change policy pack** from `minimal.yml` to the appropriate pack.
1. **Update workflow references** so the selected pack is actually used.
1. **Enable remaining CI gates** (DoD contract, drift, smoke).
1. **Expand variables** from basic to full set.
1. **Customize remaining templates** for the product.
1. **Enable scheduled workflows** (KPI, lifecycle, gaps).

No data loss or migration is needed. The pilot configuration is a subset of the full configuration.

## Pricing model reference

| Service | Scope | Typical duration |
| --- | --- | --- |
| Pilot week | Prove value on real repo, before/after KPI, 3-5 templates | 5 business days |
| Full implementation | Complete system rollout, all gates, all templates, training | 2-4 weeks |
| Ongoing retainer | Continuous optimization, reporting, governance support | Monthly |
