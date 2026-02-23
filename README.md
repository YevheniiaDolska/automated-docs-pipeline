# Auto-Doc Pipeline

A documentation operations pipeline for Docs as Code teams.

It combines quality gates, contract checks, drift detection, smoke tests,
reporting, and optional Algolia search indexing.

## What is included

1. Quality gates for Markdown, spelling, style, frontmatter, and SEO/GEO.
1. PR Definition of Done contract checks.
1. API and SDK drift gate with issue creation on drift.
1. Continuous documentation gap detection from code, docs signals, and policy rules.
1. Prioritized gap reports for planning and execution (`JSON`, `CSV`, `XLSX`, markdown reports).
1. Smoke execution for tagged code examples in docs and templates.
1. KPI wall and KPI SLA evaluation reports.
1. Release docs pack generation for releases.
1. Optional Algolia indexing workflow.
1. Policy packs for different rollout profiles.
1. API-first scaffold workflow to generate server stubs and client SDKs from OpenAPI.
1. AI drafting workflow support with strict quality prompts and template/snippet grounding.
1. Searchable and browsable documentation architecture with faceted search support.
1. Structured and manageable docs metadata via frontmatter schema validation.
1. Lifecycle visibility for draft, active, deprecated, and archived content.
1. Automated lifecycle loop with guardrails: scheduled scan, report, auto-issue, and draft PR.
1. Optional PLG API playground with Swagger UI or Redoc, including `Try it out` controls.
1. Value-first PLG documentation patterns: persona guides, use-case pages, ROI framing, and activation paths.

## Operating model and value

After implementation, the system runs continuously in CI.

1. The pipeline detects quality issues, drift, and documentation gaps automatically.
1. It produces reports and prioritized work items for the team.
1. Drafting can be delegated to AI using templates, snippets, reports, and strict prompt instructions.
1. Humans orchestrate the process, validate factual correctness, and approve final content.
1. Quality target is Stripe-level documentation quality from the first draft.

AI assistance model:

1. The local AI assistant works from repository structure and changed files.
1. It maps code and API changes to required documentation updates.
1. It proposes adds and edits in the right docs paths instead of random text generation.

This is why the model saves time: people stop doing repetitive checks manually and focus on factual accuracy and decisions.

## Core workflows

1. `.github/workflows/docs-check.yml`
1. `.github/workflows/pr-dod-contract.yml`
1. `.github/workflows/api-sdk-drift-gate.yml`
1. `.github/workflows/code-examples-smoke.yml`
1. `.github/workflows/ci-documentation.yml`
1. `.github/workflows/kpi-wall.yml`
1. `.github/workflows/release-docs-pack.yml`
1. `.github/workflows/algolia-index.yml` (optional)
1. `.github/workflows/lifecycle-management.yml`
1. `.github/workflows/openapi-source-sync.yml` (api-first and code-first support)

## Code examples smoke coverage

Smoke checks execute fenced code blocks tagged with `smoke` for supported languages:

1. `python`
1. `bash` or `sh`
1. `javascript` or `js`
1. `typescript` or `ts` (compile check with `tsc`)
1. `go` (build check with `go build`)
1. `curl` (syntax by default, execution only with `network` tag and `--allow-network`)
1. `json`
1. `yaml` or `yml`

## Local commands

If `make` is available:

```bash
make install
make validate-minimal
make validate-full
make test
make docs-serve
```

Cross-platform fallback (without `make`):

```bash
python3 -m pip install -r requirements.txt
npm install
npm run validate:minimal
npm run validate:full
npm run docs-ops:test-suite
npm run serve
npm run api:sandbox:mock
npm run api:sandbox:stop
```

## Modes

1. Minimal mode: `policy_packs/minimal.yml`
1. API-first mode: `policy_packs/api-first.yml`
1. PLG mode: `policy_packs/plg.yml`

Minimal mode is best for first rollout in restricted environments.

## Optional search stack

Algolia support is integrated.

1. Generate records from docs with `scripts/seo_geo_optimizer.py --algolia`.
1. Upload/index via `.github/workflows/algolia-index.yml`.
1. Use faceted client UI from `docs/assets/javascripts/faceted-search.js`.

## Optional API sandbox stack

1. Embed API playground in docs using `docs/assets/javascripts/api-playground.js`.
1. Choose provider: Swagger UI or Redoc.
1. Disable or enable `Try it out` for Swagger UI.
1. Route requests to sandbox base URL for safe testing.
1. Generate mock sandbox from OpenAPI with `docker-compose.api-sandbox.yml`.
1. Resolve OpenAPI source from api-first or code-first strategy with `openapi-source-sync.yml`.

## PLG documentation layer (not only API docs)

The pipeline also supports value-first documentation patterns for self-serve growth:

1. Persona entry pages focused on user outcomes.
1. Use-case pages with setup-time and savings framing.
1. Activation-oriented quickstarts and checklists.
1. Before/after and ROI sections for adoption decisions.
1. Stack or bundle guides that combine multiple templates into one workflow.

## Start here

1. `README_SETUP.md` for local setup.
1. `SETUP_FOR_PROJECTS.md` for installing into another repository.
1. `PRIVATE_REPO_SETUP.md` for private repository usage.
1. `PLG_PLAYBOOK.md` for value-first, activation-oriented docs patterns.
1. `USER_GUIDE.md` for team usage.
1. `OPERATOR_RUNBOOK.md` for implementation delivery.

## Security

Read `SECURITY_OPERATIONS.md` before enabling automation in a company
repository.
