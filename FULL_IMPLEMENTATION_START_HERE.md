# Full implementation start here

This guide is the exact order of actions for deploying the Auto-Doc Pipeline to a production repository. It covers installation, configuration, CI setup, consolidated reporting, and team onboarding.

For deeper detail on each area, see:

1. `SETUP_GUIDE.md` for local installation and validation commands.
1. `USER_GUIDE.md` for daily contributor, reviewer, and maintainer workflows.
1. `OPERATOR_RUNBOOK.md` for the full operator delivery process.

## What full implementation means

A full implementation means:

1. The pipeline is installed in the target repository.
1. All four mandatory CI gates are active and passing.
1. The selected policy pack is wired into every workflow.
1. Templates, variables, and reporting are customized for the product.
1. The consolidated weekly report runs on schedule.
1. The team can operate the pipeline without the operator.

## Step 1: install the pipeline

If the repository does not have the pipeline yet, bootstrap it:

```bash
python3 /path/to/Auto-Doc\ Pipeline/scripts/init_pipeline.py \
  --product-name "Client Product" \
  --generator mkdocs \
  --target-dir .
```

If the pipeline is already present, create a working branch:

```bash
git checkout -b chore/docs-ops-full-rollout
```

Install dependencies (see `SETUP_GUIDE.md` for troubleshooting):

```bash
python3 -m pip install -r requirements.txt
npm install
```

## Step 2: configure variables

Open `docs/_variables.yml` and replace every placeholder with real values:

```yaml
product_name: "Client Product"
product_full_name: "Client Product platform"
company_name: "Client Company"
current_version: "3.2.1"
api_version: "v2"
cloud_url: "https://app.client.com"
docs_url: "https://docs.client.com"
api_url: "https://api.client.com"
github_url: "https://github.com/client/company-repo"
support_email: "support@client.com"
default_port: 8080
env_vars:
  port: "CLIENT_PORT"
  webhook_url: "CLIENT_WEBHOOK_URL"
```

Every hardcoded product value in docs must reference these variables using `{{ variable_name }}` syntax.

## Step 3: choose and apply a policy pack

Available packs in `policy_packs/`:

1. `api-first.yml` -- API-heavy products.
1. `plg.yml` -- self-serve or product-led growth products.
1. `monorepo.yml` -- multi-service repositories.
1. `multi-product.yml` -- multiple products in one docs system.

Update the policy pack path in these workflow files:

1. `.github/workflows/pr-dod-contract.yml`
1. `.github/workflows/api-sdk-drift-gate.yml`
1. `.github/workflows/kpi-wall.yml`

## Step 4: customize templates

Start with the templates the team will use first. Typical first wave:

1. `templates/quickstart.md`
1. `templates/how-to.md`
1. `templates/tutorial.md`
1. `templates/api-reference.md`
1. `templates/troubleshooting.md`

Additional templates available: `user-guide.md`, `admin-guide.md`, `upgrade-guide.md`, `api-endpoint.md`, and 20 more in the `templates/` directory.

## Step 5: enable all four mandatory CI gates

These workflow files must be active in the repository:

1. `.github/workflows/docs-check.yml` -- style and formatting.
1. `.github/workflows/pr-dod-contract.yml` -- definition of done enforcement.
1. `.github/workflows/api-sdk-drift-gate.yml` -- API/SDK drift detection.
1. `.github/workflows/code-examples-smoke.yml` -- code example execution.

## Step 6: configure GitHub Actions secrets and schedules

**Required secrets** (set in repository Settings > Secrets and variables > Actions):

1. `GITHUB_TOKEN` -- provided automatically by GitHub Actions.
1. `ALGOLIA_APP_ID` and `ALGOLIA_API_KEY` -- only if using Algolia search.

**Cron schedules** to review: `kpi-wall.yml` (weekly Monday 08:00 UTC), `weekly-consolidation.yml` (weekly Monday 09:00 UTC), `lifecycle-management.yml` (daily 06:00 UTC), `gap-detection.yml` (weekly Monday 07:00 UTC), `release-docs-pack.yml` (on release tag). Adjust cron expressions in each file to match the team's timezone.

## Step 7: validate locally

Run the full validation stack:

```bash
npm run validate:minimal
npm run lint
npm run validate:full
```

The `validate:full` pipeline includes `doc_layers_validator.py` for document layer consistency checks. Fix all errors and warnings before proceeding.

## Step 8: run the first consolidated report

Generate baseline reports:

```bash
python3 scripts/pilot_analysis.py --json > reports/current-analysis.json
python3 scripts/generate_kpi_wall.py --docs-dir docs --reports-dir reports --stale-days 90
python3 scripts/consolidate_reports.py --docs-dir docs --reports-dir reports
```

The consolidated report merges KPI data, gap analysis, staleness tracking (with `stale_files` list), and drift results into a single weekly summary. Review the output in `reports/` to establish your baseline.

## Step 9: enable supporting automation

After the four mandatory gates are stable, enable these workflows:

1. `weekly-consolidation.yml` -- consolidated weekly report.
1. `kpi-wall.yml` -- KPI dashboard with SVG badges and stale file tracking.
1. `lifecycle-management.yml` -- deprecated and removed doc guardrails.
1. `gap-detection.yml` -- coverage gap analysis.
1. `release-docs-pack.yml` -- auto-commit docs and create issues on release.

Optional workflows:

1. `algolia-index.yml` -- search indexing.
1. `openapi-source-sync.yml` -- API spec synchronization.
1. `api-first-scaffold.yml` -- API-first doc scaffolding.

## Step 10: choose and confirm the site generator

```bash
npm run generator:detect
```

For Docusaurus: `npm run convert:to-docusaurus && npm run build:docusaurus`

For MkDocs: `npm run build:mkdocs`

## Step 11: onboard the team

**Every team member must be able to:**

1. Create a new doc from a template (`cp templates/how-to.md docs/how-to/new-guide.md`).
1. Run local validation (`npm run validate:minimal` and `npm run lint`).
1. Understand CI gate failures and fix them without operator help.
1. Read KPI and consolidated reports in `reports/`.
1. Follow self-verification instructions in `CLAUDE.md` or `AGENTS.md` when using AI to generate docs.
1. Handle deprecated docs by setting `status: deprecated` with required fields.

**Recommended onboarding:** walk through `USER_GUIDE.md` (30 min), have each contributor create one doc from a template and push a PR, review CI output together, and show the KPI wall and consolidated report.

## Step 12: hand off

The handoff package includes:

1. The configured repository branch or merged implementation.
1. A list of enabled workflows and their cron schedules.
1. The chosen policy pack and any custom overrides.
1. The completed `docs/_variables.yml`.
1. Baseline KPI, gap, and consolidated reports from `reports/`.
1. A short operator note about any client-specific exceptions.

For ongoing operations, the maintainer should follow `OPERATOR_RUNBOOK.md`.

## Full implementation is complete when

1. All four mandatory CI gates are active and passing.
1. The chosen policy pack is referenced by every workflow.
1. Local validation works without operator help.
1. The consolidated weekly report runs on schedule.
1. The selected site generator builds without errors.
1. The team can create, validate, and merge new docs independently.
1. KPI, gap, lifecycle, and consolidated reporting are running or intentionally deferred.
