# Full implementation start here

This guide is the exact order of actions for a full implementation of the Auto-Doc Pipeline after a successful pilot or as a direct rollout.

## What full implementation means

A full implementation means:

1. The pipeline is fully installed in the client's repository.
1. All four mandatory CI gates are active.
1. The selected policy pack is wired into the workflows.
1. Templates, variables, and reporting are customized for the client.
1. The client team can operate the pipeline without you.

## Step 1: start from the client repository

If the client repository does not have the pipeline yet, install it first from the client repository root:

```bash
python3 /path/to/Auto-Doc\ Pipeline/scripts/init_pipeline.py \
  --product-name "Client Product" \
  --generator mkdocs \
  --target-dir .
```

If the pipeline is already present, open the repository and create a working branch:

```bash
git checkout -b chore/docs-ops-full-rollout
```

## Step 2: install dependencies

```bash
python3 -m pip install -r requirements.txt
npm install
```

## Step 3: choose the correct policy pack

Use one of these:

1. `policy_packs/api-first.yml` for API-heavy products.
1. `policy_packs/plg.yml` for self-serve or PLG products.
1. `policy_packs/monorepo.yml` for multi-service repositories.
1. `policy_packs/multi-product.yml` for multiple products in one docs system.
1. A custom pack if the client has unusual requirements.

## Step 4: update workflow files to use that policy pack

This step is mandatory. The workflows do not fully auto-switch policy packs for you.

Check and update these files:

1. `.github/workflows/pr-dod-contract.yml`
1. `.github/workflows/api-sdk-drift-gate.yml`
1. `.github/workflows/kpi-wall.yml`

Replace any old pack path with the chosen one.

## Step 5: build the full variables file

Open `docs/_variables.yml` and fill in the client's real values.

Minimum recommended fields:

```yaml
product_name: "Client Product"
product_full_name: "Client Product platform"
company_name: "Client Company"
current_version: "3.2.1"
api_version: "v2"
cloud_url: "https://app.client.com"
docs_url: "https://docs.client.com"
github_url: "https://github.com/client/company-repo"
support_email: "support@client.com"
sales_email: "sales@client.com"
default_port: 8080
default_data_folder: "~/.client-product"
env_vars:
  port: "CLIENT_PORT"
  webhook_url: "CLIENT_WEBHOOK_URL"
```

## Step 6: enable all four mandatory gates

These files must be active in the repository:

1. `.github/workflows/docs-check.yml`
1. `.github/workflows/pr-dod-contract.yml`
1. `.github/workflows/api-sdk-drift-gate.yml`
1. `.github/workflows/code-examples-smoke.yml`

## Step 7: confirm the local commands work

Run:

```bash
npm run validate:minimal
npm run lint
npm run validate:full
```

If the repository uses a non-standard default branch, also check the contract and drift commands manually with the correct base ref.

## Step 8: choose and confirm the site generator

Check the active generator:

```bash
npm run generator:detect
```

If the client wants Docusaurus:

```bash
npm run convert:to-docusaurus
npm run build:docusaurus
```

If the client stays on MkDocs:

```bash
npm run build:mkdocs
```

## Step 9: customize the templates

Do not customize all templates blindly. Start with the ones the client will use first, then expand.

Typical first wave:

1. `quickstart.md`
1. `how-to.md`
1. `tutorial.md`
1. `troubleshooting.md`
1. `api-reference.md`
1. `security-guide.md`
1. `deployment-guide.md`

## Step 10: enable supporting automation

Recommended workflows after the core gates are stable:

1. `kpi-wall.yml`
1. `lifecycle-management.yml`
1. `gap-detection.yml`
1. `release-docs-pack.yml`

Optional workflows:

1. `algolia-index.yml`
1. `openapi-source-sync.yml`
1. `api-first-scaffold.yml`

## Step 11: configure optional search and API features

If the client wants Algolia:

1. Add the Algolia configuration to `mkdocs.yml`.
1. Add the required secrets to the repository.
1. Enable `algolia-index.yml`.

If the client wants API sandbox controls:

1. Add an OpenAPI file at the expected path.
1. Use `docker-compose.api-sandbox.yml` if needed.
1. Configure the API playground settings in `mkdocs.yml`.

## Step 12: capture baseline and current KPI reports

Generate the reporting set:

```bash
python3 scripts/pilot_analysis.py --json > reports/current-analysis.json
python3 scripts/generate_kpi_wall.py --docs-dir docs --reports-dir reports --stale-days 90
npm run kpi-full
npm run kpi-sla
npm run gaps
```

## Step 13: train the client team

The team must learn these tasks:

1. Create a doc from a template.
1. Run `npm run validate:minimal`.
1. Run `npm run lint`.
1. Understand CI gate failures.
1. Read KPI reports.
1. Use `CLAUDE.md` or `AGENTS.md` safely.

## Step 14: hand off the implementation

The handoff package should include:

1. The configured repository branch or merged implementation.
1. A list of enabled workflows.
1. The chosen policy pack.
1. The completed `docs/_variables.yml`.
1. KPI and gap reports from `reports/`.
1. A short operator note about any client-specific exceptions.

## Full implementation is complete when

1. All four mandatory CI gates are active.
1. The chosen policy pack is actually referenced by the workflows.
1. Local validation works without operator help.
1. The selected site generator builds successfully.
1. The team can create and validate new docs on their own.
1. KPI, gap, and lifecycle reporting are running or intentionally deferred.
