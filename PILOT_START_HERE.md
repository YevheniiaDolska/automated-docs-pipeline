# Pilot start here

This guide is the exact order of actions for a five-day pilot of the Auto-Doc Pipeline. It is written for a person who has never launched a project before.

## What the pilot should achieve

By the end of the pilot, you should have:

1. The pipeline installed in the client's repository.
1. One working CI quality gate.
1. Baseline and final KPI reports.
1. A small set of adapted templates.
1. A short executive summary that shows before vs after improvement.

## Before you start

You need:

1. A local copy of this repository: `Auto-Doc Pipeline`.
1. Access to the client's repository.
1. Git, Node.js 18+, Python 3.10+, and npm installed.

Check your tools:

```bash
git --version
node --version
npm --version
python3 --version
```

On Windows, if `python3` does not work, use:

```bash
py -3 --version
```

## Day 1: install the pipeline in the client repository

### Step 1: clone the client repository

```bash
git clone <client-repo-url>
cd <client-repo-folder>
git checkout -b chore/docs-ops-pilot
```

### Step 2: install the pipeline into that repository

Run this command from the **client repository root**:

```bash
python3 /path/to/Auto-Doc\ Pipeline/scripts/init_pipeline.py \
  --product-name "Client Product" \
  --generator mkdocs \
  --target-dir .
```

On Windows:

```bash
py -3 "C:\path\to\Auto-Doc Pipeline\scripts\init_pipeline.py" ^
  --product-name "Client Product" ^
  --generator mkdocs ^
  --target-dir .
```

### Step 3: confirm the install worked

Run:

```bash
npm run validate:minimal
```

Then run:

```bash
npm run generator:detect
```

Expected result:

1. `validate:minimal` completes, even if it reports documentation issues.
1. `generator:detect` prints `mkdocs` unless you intentionally chose Docusaurus.

### Step 4: fill in the basic product variables

Open `docs/_variables.yml` in the client repository and update these values:

```yaml
product_name: "Client Product"
product_full_name: "Client Product platform"
current_version: "1.0.0"
cloud_url: "https://app.client.com"
docs_url: "https://docs.client.com"
support_email: "support@client.com"
default_port: 8080
```

### Step 5: capture baseline reports

```bash
python3 scripts/pilot_analysis.py --json > reports/pilot-baseline.json
python3 scripts/generate_kpi_wall.py --docs-dir docs --reports-dir reports --stale-days 90
python3 scripts/evaluate_kpi_sla.py \
  --current reports/kpi-wall.json \
  --policy-pack policy_packs/minimal.yml \
  --json-output reports/kpi-sla-report.json \
  --md-output reports/kpi-sla-report.md
npm run gaps
```

Save these outputs:

1. `reports/pilot-baseline.json`
1. `reports/kpi-wall.json`
1. `reports/kpi-sla-report.md`
1. Gap report outputs in `reports/`

## Day 2: enable only the pilot-safe gate

For a pilot, use only the core quality gate first:

1. Keep `.github/workflows/docs-check.yml`.
1. Do not require the other three gates yet unless the client explicitly wants them.

Important:

1. Some workflow files still reference `policy_packs/api-first.yml` by default.
1. For a pilot, keep the repo aligned with `policy_packs/minimal.yml` where you actively use KPI or contract checks.

Run:

```bash
npm run validate:minimal
npm run lint
```

Fix the most obvious problems first:

1. Missing frontmatter.
1. Broken headings or lists.
1. Bad first paragraphs.
1. Broken `smoke` code blocks.

## Day 3: adapt a few templates

Pick only 3 to 5 templates that matter most for the client.

Recommended set:

1. `templates/quickstart.md`
1. `templates/how-to.md`
1. `templates/troubleshooting.md`
1. `templates/api-reference.md` if the client has an API
1. `templates/tutorial.md` if they need onboarding

Copy them into the client docs tree:

```bash
cp templates/quickstart.md docs/getting-started/quickstart.md
cp templates/how-to.md docs/how-to/common-task.md
cp templates/troubleshooting.md docs/troubleshooting/common-issue.md
```

Then edit them:

1. Replace placeholder text with real client information.
1. Use variables from `docs/_variables.yml`.
1. Keep code examples complete.

Validate again:

```bash
npm run validate:minimal
```

## Day 4: generate and fix a small batch of docs

Use Claude or Codex with the repository instructions:

1. `CLAUDE.md`
1. `AGENTS.md`

Generate 2 to 3 real documents, not more.

After each batch, run:

```bash
npm run validate:minimal
npm run gaps
```

Fix:

1. Any failed smoke examples.
1. Missing metadata.
1. The highest-priority documentation gaps.

## Day 5: create the before vs after report

Run the final measurement:

```bash
python3 scripts/pilot_analysis.py --json > reports/pilot-final.json
python3 scripts/generate_kpi_wall.py --docs-dir docs --reports-dir reports --stale-days 90
npm run kpi-full
npm run kpi-sla
```

Create badges:

```bash
npm run badges
```

## What you send to the client

Send these artifacts:

1. `reports/pilot-baseline.json`
1. `reports/pilot-final.json`
1. `reports/kpi-sla-report.md`
1. SVG badges from `reports/`
1. The adapted template files
1. The short executive summary

## What to write in the executive summary

Keep it short. Include:

1. Quality score before vs after.
1. Stale docs trend before vs after.
1. Number of gaps found and number fixed.
1. Number of docs drafted during the pilot.
1. Recommendation: stop, extend pilot, or move to full implementation.

## The pilot is successful when

1. The client repository can run `npm run validate:minimal`.
1. At least one CI quality gate is active.
1. Baseline and final KPI outputs exist.
1. The team can create a new page from a template.
1. You can clearly show before vs after movement in at least one KPI.
