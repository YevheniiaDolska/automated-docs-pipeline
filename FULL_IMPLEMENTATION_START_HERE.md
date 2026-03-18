# Full implementation start here

This guide is the exact order of actions for deploying the VeriOps to a production repository. It covers installation, client profile provisioning, automation scheduling, CI setup (optional compatibility), consolidated reporting, and team onboarding.

For deeper detail on each area, see:

\11. `SETUP_GUIDE.md` for local installation and validation commands.
\11. `USER_GUIDE.md` for daily contributor, reviewer, and maintainer workflows.
\11. `OPERATOR_RUNBOOK.md` for the full operator delivery process.

## What full implementation means

A full implementation means:

\11. The pipeline is installed in the target repository.
\11. Client profile + bundle provisioning are configured.
\11. Weekly scheduler automation is installed and verified.
\11. All four mandatory CI gates are active and passing.
\11. The selected policy pack is wired into every workflow.
\11. Templates, variables, and reporting are customized for the product.
\11. The consolidated weekly report runs on schedule (local scheduler recommended; CI mode optional).
\11. The team can operate the pipeline without the operator.

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

## Step 3: choose plan tier + policy baseline

Start from a plan preset:

\11. `profiles/clients/examples/basic.client.yml`
\11. `profiles/clients/examples/pro.client.yml`
\11. `profiles/clients/examples/enterprise.client.yml`

Then tune policy and modules in `profiles/clients/<client>.client.yml`.

References:

\11. `docs/operations/PLAN_TIERS.md`
\11. `docs/operations/UNIFIED_CLIENT_CONFIG.md`

## Step 4: provision the client repository (recommended automation mode)

```bash
python3 scripts/provision_client_repo.py \
  --client profiles/clients/<client>.client.yml \
  --client-repo /path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler linux
```

This installs `docsops/` and scheduler, then weekly automation runs via `docsops/scripts/run_weekly_gap_batch.py`.

## Step 5: choose and apply a policy pack (if using CI compatibility mode)

Available packs in `policy_packs/`:

\11. `api-first.yml` -- API-heavy products.
\11. `plg.yml` -- self-serve or product-led growth products.
\11. `monorepo.yml` -- multi-service repositories.
\11. `multi-product.yml` -- multiple products in one docs system.

Update the policy pack path in these workflow files:

\11. `.github/workflows/pr-dod-contract.yml`
\11. `.github/workflows/api-sdk-drift-gate.yml`
\11. `.github/workflows/kpi-wall.yml`

## Step 6: customize templates

Start with the templates the team will use first. Typical first wave:

\11. `templates/quickstart.md`
\11. `templates/how-to.md`
\11. `templates/tutorial.md`
\11. `templates/api-reference.md`
\11. `templates/troubleshooting.md`

Additional templates available: `user-guide.md`, `admin-guide.md`, `upgrade-guide.md`, `api-endpoint.md`, and 20 more in the `templates/` directory.

## Step 7: enable all four mandatory CI gates (CI compatibility mode)

These workflow files must be active in the repository:

\11. `.github/workflows/docs-check.yml` -- style and formatting.
\11. `.github/workflows/pr-dod-contract.yml` -- definition of done enforcement.
\11. `.github/workflows/api-sdk-drift-gate.yml` -- API/SDK drift detection.
\11. `.github/workflows/code-examples-smoke.yml` -- code example execution.

## Step 8: configure GitHub Actions secrets and schedules (CI compatibility mode)

**Required secrets** (set in repository Settings > Secrets and variables > Actions):

\11. `GITHUB_TOKEN` -- provided automatically by GitHub Actions.
\11. `ALGOLIA_APP_ID` and `ALGOLIA_ADMIN_KEY` -- only if using Algolia search.

**CI compatibility cron schedules** to review (if CI mode is used): `kpi-wall.yml` (weekly Monday 08:00 UTC), `weekly-consolidation.yml` (weekly Monday 09:00 UTC), `lifecycle-management.yml` (daily 06:00 UTC), `gap-detection.yml` (weekly Monday 07:00 UTC), `release-docs-pack.yml` (on release tag). Adjust cron expressions in each file to match the team's timezone.

## Step 9: validate locally

Run the full validation stack:

```bash
npm run validate:minimal
npm run lint
npm run validate:full
```

The `validate:full` pipeline includes `doc_layers_validator.py` for document layer consistency checks. Fix all errors and warnings before proceeding.

## Step 10: run the first consolidated report

Generate baseline reports:

```bash
python3 scripts/pilot_analysis.py --json > reports/current-analysis.json
python3 scripts/generate_kpi_wall.py --docs-dir docs --reports-dir reports --stale-days 90
python3 scripts/consolidate_reports.py --docs-dir docs --reports-dir reports
```

The consolidated report merges KPI data, gap analysis, staleness tracking (with `stale_files` list), and drift results into a single weekly summary. Review the output in `reports/` to establish your baseline.

## Step 11: enable supporting automation (CI compatibility mode)

After the four mandatory gates are stable, enable weekly automation:

\11. Recommended mode: scheduler-driven `docsops/scripts/run_weekly_gap_batch.py`.
\11. CI compatibility mode: `weekly-consolidation.yml`.
\11. Optional CI companion workflows: `kpi-wall.yml`, `lifecycle-management.yml`, `gap-detection.yml`, `release-docs-pack.yml`.

Optional workflows:

\11. `algolia-index.yml` -- search indexing.
\11. `openapi-source-sync.yml` -- API spec synchronization.
\11. `api-first-scaffold.yml` -- API-first doc scaffolding.

## Step 12: choose and confirm the site generator

```bash
npm run generator:detect
```

For Docusaurus: `npm run convert:to-docusaurus && npm run build:docusaurus`

For MkDocs: `npm run build:mkdocs`

## Step 13: onboard the team

**Every team member must be able to:**

\11. Create a new doc from a template (`cp templates/how-to.md docs/how-to/new-guide.md`).
\11. Run local validation (`npm run validate:minimal` and `npm run lint`).
\11. Understand CI gate failures and fix them without operator help.
\11. Read KPI and consolidated reports in `reports/`.
\11. Follow self-verification instructions in `CLAUDE.md` or `AGENTS.md` when using AI to generate docs.
\11. Handle deprecated docs by setting `status: deprecated` with required fields.

**Recommended onboarding:** walk through `USER_GUIDE.md` (30 min), have each contributor create one doc from a template and push a PR, review CI output together, and show the KPI wall and consolidated report.

## Step 14: hand off

The handoff package includes:

\11. The configured repository branch or merged implementation.
\11. A list of enabled workflows and their cron schedules.
\11. The chosen policy pack and any custom overrides.
\11. The completed `docs/_variables.yml`.
\11. Baseline KPI, gap, and consolidated reports from `reports/`.
\11. A short operator note about any client-specific exceptions.

For ongoing operations, the maintainer should follow `OPERATOR_RUNBOOK.md`.

## Full implementation is complete when

\11. All four mandatory CI gates are active and passing.
\11. The chosen policy pack is referenced by every workflow.
\11. Local validation works without operator help.
\11. The consolidated weekly report runs on schedule.
\11. The selected site generator builds without errors.
\11. The team can create, validate, and merge new docs independently.
\11. KPI, gap, lifecycle, and consolidated reporting are running or intentionally deferred.
