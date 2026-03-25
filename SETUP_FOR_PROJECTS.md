---
title: "Set up pipeline for client projects"
description: "Operator and client setup guide for building, handing off, and running the docsops bundle with weekly automation."
content_type: reference
product: both
tags:
  - Reference
  - VeriOps
  - Setup
last_reviewed: "2026-03-17"
---

# Set up this pipeline for client projects

## Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.


This document is split into two different flows:

1. Operator flow (your laptop): you collect inputs, build/configure bundle, and hand off.
1. Client flow (client laptop/repo): client installs and runs the bundle with minimal actions.

Most custom configuration should happen on your side.

Wizard note:

`scripts/provision_client_repo.py --interactive --generate-profile` now supports full pre-bundle configuration (modules, integrations, style guide, publish targets, include paths, weekly tasks, API-first switches, and governance toggles).
For preset `pilot-evidence`, wizard defaults to a shorter setup path (advanced section is optional and default-off).
Preset also selects matching LLM instruction files automatically (pilot/basic/pro/enterprise variants).
Wizard now also asks whether finalize gate should require interactive commit confirmation (`runtime.finalize_gate.ask_commit_confirmation`).


## Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

## Pilot vs Full (intentional scope difference)

Pilot is intentionally limited so full implementation clearly unlocks much more value.

Pilot default scope (`pilot-evidence`):

1. Core docs ops only: gaps/drift/docs-contract, KPI/SLA, normalization, snippet lint, smoke/self-check, SEO/GEO.
1. API-first baseline: notes -> OpenAPI -> docs sync + local prism sandbox + test asset generation.
1. No advanced integrations by default: no Algolia, no Ask AI, no PR auto-fix, no external mock auto-prepare.
1. No advanced knowledge automation by default: RAG index/graph/retrieval evals off.
1. No i18n/lifecycle/release-pack automation in pilot.

Full implementation scope (Pro/Enterprise level presets + advanced wizard):

1. Full knowledge/RAG contour: extraction, retrieval index, JSON-LD graph, retrieval eval gates.
1. Full integration contour: external mock automation, TestRail/Zephyr upload, Algolia, Ask AI.
1. Full automation contour: advanced custom weekly tasks, lifecycle management, i18n, release pack.
1. Optional PR auto-fix workflow and governance controls.

## Value-first outreach flow (automated audit before pilot)

Use this pre-sales sequence:

1. Public docs audit (no repo access required).
1. Readout with concrete findings (numbers + examples).
1. Offer pilot scope tied to top findings.
1. Upgrade to full implementation after pilot proof.

### Public docs audit command

Single docs site:

```bash
python3 scripts/generate_public_docs_audit.py \
  --site-url https://docs.company.com
```

Wizard mode (asks inputs interactively):

```bash
npm run audit:public:wizard
```

Wizard behavior:

1. Asks URL #1, URL #2, URL #3, and so on, one by one.
1. You just paste links and press Enter.
1. Empty Enter finishes URL input and starts audit.
1. Wizard can also enable Claude Sonnet executive analysis (optional).

Multiple docs sites (same product, fragmentation is a risk):

```bash
python3 scripts/generate_public_docs_audit.py \
  --site-url https://docs.company.com \
  --site-url https://developer.company.com \
  --topology-mode single-product
```

Multiple docs sites (different unrelated products/projects):

```bash
python3 scripts/generate_public_docs_audit.py \
  --site-url https://docs.product-a.com \
  --site-url https://docs.product-b.com \
  --topology-mode multi-project
```

If you want a public report URL in output, pass:

```bash
python3 scripts/generate_public_docs_audit.py \
  --site-url https://docs.company.com \
  --report-url-base https://your-host/reports
```

If you want deterministic metrics + Claude Sonnet 4.5 executive analysis together:

```bash
python3 scripts/generate_public_docs_audit.py \
  --site-url https://docs.company.com \
  --llm-enabled \
  --llm-model claude-sonnet-4-5 \
  --llm-env-file /mnt/c/Users/Kroha/Documents/development/forge-marketing/.env \
  --llm-api-key-env-name ANTHROPIC_API_KEY
```

LLM output is added into:

1. `reports/public_docs_audit_llm_summary.json`
1. `reports/public_docs_audit.html` (LLM section is embedded)

Outputs:

1. `reports/public_docs_audit.json`
1. `reports/public_docs_audit.html`
1. optional LLM: `reports/public_docs_audit_llm_summary.json`

### Internal repo audit command (when access is provided)

```bash
python3 scripts/generate_audit_scorecard.py \
  --docs-dir docs \
  --reports-dir reports \
  --spec-path api/openapi.yaml \
  --policy-pack policy_packs/api-first.yml \
  --glossary-path glossary.yml \
  --stale-days 180 \
  --auto-run-smoke \
  --json-output reports/audit_scorecard.json \
  --html-output reports/audit_scorecard.html
```

Outputs:

1. `reports/audit_scorecard.json`
1. `reports/audit_scorecard.html`

Scorecard now includes:

1. Per-finding matrix: `finding -> capability_id -> pipeline_modules -> pilot/full fixability`.
1. Per-finding estimates in `low/base/high` format:
   - effort hours,
   - remediation cost (USD),
   - estimated monthly loss (USD).
1. Totals in `findings_totals`:
   - summed remediation cost (`low/base/high`),
   - summed monthly loss (`low/base/high`),
   - pilot-fixable and full-fixable counts.
1. `capability_matrix` section so coverage is explicit and limited to real pipeline capabilities.

### Executive one-page PDF (deterministic + LLM consolidated)

```bash
python3 scripts/generate_executive_audit_pdf.py \
  --scorecard-json reports/audit_scorecard.json \
  --public-audit-json reports/public_docs_audit.json \
  --llm-summary-json reports/public_docs_audit_llm_summary.json \
  --company-name "Client Name" \
  --output reports/executive_audit_one_pager.pdf
```

Output:

1. `reports/executive_audit_one_pager.pdf`

### How to pick top-3 gaps for recap demo

Use:

1. `reports/public_docs_audit.json` for external stage findings.
1. `reports/audit_scorecard.json` -> `top_3_gaps` for internal stage findings.

These two files are the source of truth for your readout and recap offer.

## What key scripts mean (simple)

- `scripts/provision_client_repo.py` (`one-shot provisioning`):
  - one command that builds bundle, copies it into client repo, writes runtime config/policy, generates env checklist, and can install scheduler.
- `scripts/apply_openapi_overrides.py`:
  - applies your manual OpenAPI fixes/overrides after generation from notes.
- `scripts/check_openapi_regression.py`:
  - compares current OpenAPI with baseline snapshot and reports unexpected contract changes.
- `templates/legal/LICENSE-COMMERCIAL.template.md` and `templates/legal/NOTICE.template.md`:
  - legal templates for commercial delivery/license notices in client package.

## Confluence migration (one-click for client)

If client has a Confluence export ZIP, they can migrate pages in one command:

```bash
npm run confluence:migrate -- --export-zip /path/to/confluence-export.zip
```

What this command does:

1. Imports pages from `entities.xml` into Markdown docs.
1. Writes docs to `docs/imported/confluence/<timestamp>/` (default path).
1. Runs veriops post-checks automatically:
   - normalization check/fix,
   - SEO/GEO check/fix,
   - code examples smoke check.
1. Generates migration report files:
   - `reports/confluence_migration_report.json`,
   - `reports/confluence_migration_report.md`.

If client only wants raw import without post-checks:

```bash
npm run confluence:migrate -- --export-zip /path/to/confluence-export.zip --skip-post-checks
```

## Operator flow (you)

### Goal

You prepare everything once. Client only installs and runs.

### Step 1: Collect client inputs (single questionnaire, English)

Use this exact question list with the client:

1. Company and project identifiers:
   - Company name, product name, `client_id`.
1. Repository and paths:
   - Repository URL, default branch, docs root, API spec root, SDK root.
1. Docs platform:
   - Generator (`mkdocs`/`docusaurus`/`sphinx`/`hugo`/`jekyll`), publish targets.
1. API mode:
   - `code-first`, `api-first`, or `hybrid`.
1. API sandbox:
   - backend mode (`docker`, `prism`, `external`), public mock base URL if external.
1. External mock provider (if external mode):
   - Postman workspace ID, API key owner, existing collection/mock server IDs (if any).
1. Test management (optional):
   - TestRail and/or Zephyr usage, target project/section/folder IDs.
1. Search/AI integrations (optional):
   - Algolia usage, Ask AI usage.
1. Scheduling:
   - weekly run day/time/timezone (default Monday 10:00 local).
1. Security and governance:
   - who manages secrets, whether PR auto-fix is allowed, who approves bot commits.

For full copy-paste questionnaire, use:

- `OPERATOR_QUESTIONNAIRE.md`

Clarifications:

1. `client_id` is a slug id. In wizard mode it is auto-suggested from company name, then you can edit it.
1. For repo URL/paths, links and correct path values are enough for profile creation. Access is only needed later for install/run.
1. `publish target(s)` means final publication channels (for example `mkdocs`, `readme`, `github`, `sphinx`).
1. For Postman, the required credential is API key value. "Owner" means who in client org rotates/manages that key.

### Full questionnaire (exhaustive, operator checklist)

Use this when you want one interview and no follow-up questions.

1. Identity and ownership:
   - company legal name, product name, `client_id`, primary docs owner email, technical fallback contact.
1. Repository model:
   - git host (`github/gitlab/bitbucket`), repo URL, default branch, monorepo yes/no, required access model.
1. Content roots:
   - docs root, API spec root, SDK root, notes/planning docs root, localization root.
1. Generator and publish:
   - site generator, hosting target, publish channels (`mkdocs`, `readme`, `github`, etc.), preview URL pattern.
1. Style and terminology:
   - style guide profile (`google`, `microsoft`, `hybrid`), company terminology source, banned terms, naming rules.
1. Policy and strictness:
   - base policy pack, required quality threshold, stale-day threshold, warning policy (warn vs block).
1. Automation schedule:
   - day/time/timezone, local scheduler vs CI compatibility mode, retry policy expectations.
1. Docs flow mode:
   - `code-first`, `api-first`, or `hybrid`; whether API-first runs every week or only on demand.
1. API sandbox:
   - backend mode (`docker`, `prism`, `external`), public mock URL, CORS/HTTPS constraints.
1. External mock details (if `external`):
   - provider, workspace/project IDs, auto-create allowed yes/no, reuse existing mock yes/no.
1. API-first controls:
   - OpenAPI version target, manual overrides path, regression snapshot policy.
1. QA integration:
   - generate test assets yes/no, upload to TestRail and/or Zephyr yes/no, target section/suite/folder mapping.
1. Search and AI integrations:
   - Algolia enabled yes/no, Ask AI enabled yes/no, provider/model/billing mode constraints.
1. RAG/knowledge:
   - knowledge modules enabled yes/no, retrieval eval thresholds, JSON-LD graph enabled yes/no.
1. i18n:
   - locales, translation mode (manual/assisted/auto), stale translation policy.
1. Security:
   - secret owner, secret rotation policy, whether operator sees secrets (usually no), approved env names.
1. PR governance:
   - PR auto-fix enabled yes/no, label requirement, auto-merge allowed yes/no, approver roles.
1. Legal/compliance:
   - retention requirements, noindex/deprecation policy, legal notice/license text requirements.
1. Delivery model:
   - pilot vs full implementation scope, included modules, excluded modules.
1. Success metrics:
   - baseline time-to-publish, defect rate target, support-ticket target, reporting cadence.

### Step 2: Run onboarding/build on your machine

Recommended:

```bash
python3 scripts/onboard_client.py
```

Output:

1. `profiles/clients/generated/<client_id>.client.yml`
1. `generated/client_bundles/<client_id>/`

Manual alternative:

```bash
python3 scripts/build_client_bundle.py --client profiles/clients/<client>.client.yml
```

### Step 3: Hand off bundle

If you do not have direct repo access, send `generated/client_bundles/<client_id>/` to client.

If you do have access, run provisioning directly:

```bash
python3 scripts/provision_client_repo.py \
  --client profiles/clients/<client>.client.yml \
  --client-repo /path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler linux
```

Windows scheduler install:

```bash
python3 scripts/provision_client_repo.py \
  --client profiles/clients/<client>.client.yml \
  --client-repo C:/path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler windows
```

Clarification:

1. One-shot provisioning is one command only when run on a machine that has access to both repos.
1. If machines are different, use two-stage mode: build bundle on your machine, client installs on theirs.

## Client flow (client)

### Goal

Install bundle and run smooth automation with minimal setup.

### Step 1: Put bundle into repo

Copy received folder as:

```text
<client-repo>/docsops/
```

### Step 2: Configure secrets locally (not in git)

1. Copy generated template:
   - `docsops/.env.docsops.local.template` -> `/.env.docsops.local`
1. Create local secrets file in repo root:
   - `/.env.docsops.local`
1. Add this file to `.gitignore`:

```gitignore
/.env.docsops.local
reports/docsops-weekly.log
```

1. Fill values listed in `docsops/ENV_CHECKLIST.md`.

### Step 3: Install scheduler

Before installing scheduler, verify git access for this repo under the same user account that will run `cron`/Task Scheduler:

1. SSH key or credential helper/PAT is configured for that user.
1. `git pull` works from repository root in terminal.

If this is not configured, weekly run will fail during pre-sync.

Linux/macOS:

```bash
bash docsops/ops/install_cron_weekly.sh
```

Windows:

```bash
powershell -ExecutionPolicy Bypass -File docsops/ops/install_windows_task.ps1
```

This runs locally on client machine timezone (default Monday 10:00 local).

## Upgrade path: Pilot -> Full (safe, no scheduler conflicts)

Use this flow after pilot is accepted.

1. Build a new full bundle on operator side (for example Pro or Enterprise preset).
1. On client repo, replace `docsops/` with the new bundle (overwrite old files).
1. Keep the same `client_id` from pilot profile.
1. Update local secrets from new template:
   - `docsops/.env.docsops.local.template` -> `/.env.docsops.local`
1. Re-run scheduler installer once:
   - Linux/macOS: `bash docsops/ops/install_cron_weekly.sh`
   - Windows: `powershell -ExecutionPolicy Bypass -File docsops/ops/install_windows_task.ps1`
1. Run one smoke cycle:
   - `python3 docsops/scripts/run_weekly_gap_batch.py --docsops-root docsops --reports-dir reports --since 7`

Important scheduler note:

1. Cron installer uses marker `# docsops-weekly-<client_id>` and replaces old line automatically.
1. Windows installer re-registers the same task name with `-Force`.
1. If `client_id` changes, you can get a second scheduler entry. Keep `client_id` stable for clean upgrade.

## What goes to GitHub, what stays local

By default, `docsops/` is part of repository files, so it can be committed and pushed.

- If you want `docsops/` in GitHub: keep it tracked (recommended for shared visibility and reproducibility).
- If you want only local scheduler automation and no bundle files in GitHub: add `docsops/` to `.gitignore` and do not commit it.
- Reports can be either tracked or local-only by your process policy.

Important:

1. Gap/drift checks still work in local-only mode because they read the same repository commits/diffs locally.
1. Keeping `docsops/` in git is still recommended for team transparency and reproducibility.

## GitHub Actions "Read and write permissions" (simple)

This setting only matters if PR auto-fix workflow is enabled.

- Meaning: GitHub Actions bot is allowed to commit docs fixes to PR branches.
- It does not modify code logic by itself; it only pushes generated file changes from workflow steps.
- If disabled, workflow can still run checks but cannot push bot commits.

## Who should run `init_pipeline.py`

For client-delivery model, normally you (operator) do not need `init_pipeline.py` in client repo.

- Use bundle/provisioning flow above.
- `init_pipeline.py` is for self-install into a repo when someone wants to bootstrap pipeline directly from source.

Simple explanation:

- `init_pipeline.py` is an installer from source files.
- It copies the pipeline into a target repository directly.
- In your bundle delivery model, you usually do not need it.

## Variables policy

`docs/_variables.yml` should contain all reusable, change-prone values:

- product, URLs, versions, ports, env var names, limits, paths, endpoints, support links, legal contacts.
- any recurring numeric values (timeouts, retries, quotas, thresholds, retention days, limits, capacities).

Do not hardcode recurring values in docs pages.

## After setup (operator manual commands, optional)

| Task | Command |
| --- | --- |
| Daily validation | `npm run validate:minimal` |
| Full validation with tests | `npm run validate:full` |
| Generate KPI dashboard | `npm run kpi-wall` |
| Detect documentation drift | `npm run drift-check` |
| Run gap analysis | `npm run gaps` |
| Browser-based setup wizard | `npm run configurator` |

These are manual fallback commands. Regular operation is automated by weekly scheduler.

## Finalize gate flow (simple)

Before `Yes`:

1. Pipeline runs finalize loop: `lint -> auto-fix -> lint`.
1. This stage fixes linter-detected issues before user approval.

After `Yes` (user reviewed docs and optionally edited manually):

1. Pipeline runs pre-commit loop: `pre-commit -> auto-fix -> pre-commit`.
1. This catches/fixes issues introduced by manual edits after initial generation.
1. Then commit/push can run (if enabled), CI repeats checks, and docs build/deploy flow proceeds.

## Weekly smooth automation (regular docs and API docs)

When provisioning is done, scheduler runs weekly batch automatically:

1. Gap detection for last 7 days.
1. Weekly stale-doc check (documents unchanged for 180 days by default).
1. Regular documentation updates (concept/how-to/reference/troubleshooting) based on gaps and checks.
1. Optional KPI/SLA checks (if scripts are included).
1. Optional API-first flow (if client flow mode is `api-first` or `hybrid`).
1. API sandbox mode can be `docker`, `prism` (no Docker), or `external` (public HTTPS URL).
1. If `runtime.api_first.sync_playground_endpoint=true`, the pipeline auto-updates playground sandbox URL in `mkdocs.yml`.
1. Optional OpenAPI manual overrides and regression gate (when configured in `runtime.api_first`).
1. Optional custom tasks (`runtime.custom_tasks.weekly`) for any extra capability.
1. Finalize gate (`scripts/finalize_docs_gate.py`): lint -> auto-fix -> lint loop after generation/refinement tasks.
1. Consolidated report generation.

For automated intent bundle generation, operator keeps these enabled in profile before bundle build:

1. `bundle.include_scripts` includes `scripts/build_all_intent_experiences.py`.
1. `runtime.custom_tasks.weekly` includes command `python3 docsops/scripts/build_all_intent_experiences.py`.
1. `bundle.include_paths` includes `knowledge_modules` (or client repo already contains `knowledge_modules`).

Report rotation behavior:

- weekly reports are regenerated to the same filenames
- old report files are overwritten by new run output
- manual cleanup is not required

Client check (minimum manual effort):

1. In file explorer, find `reports/consolidated_report.json`.
1. Check file Modified date/time.
1. If Modified is fresh (after scheduled run window), report is new and ready for local LLM.

That is enough. No extra files need to be opened.

Operator post-provision manual checks (recommended):

1. Open `<client-repo>/docsops/config/client_runtime.yml` and confirm client values.
1. Open `<client-repo>/docsops/policy_packs/selected.yml` and confirm policy pack/overrides applied.
1. Open `<client-repo>/docsops/ENV_CHECKLIST.md` and verify required secrets/env vars with the client.
1. Run one smoke cycle: `python3 docsops/scripts/run_weekly_gap_batch.py --docsops-root docsops --reports-dir reports --since 7`.
1. Confirm `reports/consolidated_report.json` was refreshed.

Optional technical markers (not required for clients):

- `reports/READY_FOR_REVIEW.txt`
- `reports/docsops_status.json`

Default stale threshold is 180 days and can be customized per client in:

- `profiles/clients/<client>.client.yml` -> `private_tuning.weekly_stale_days`

For all other capabilities (SEO/GEO, RAG/knowledge index, retrieval evals, JSON-LD graph, terminology sync, interactive diagrams, i18n, Algolia, Ask AI, sandbox flows), operator configures:

1. `runtime.custom_tasks.weekly` for command-based automation.
1. `runtime.integrations` for centralized Algolia + Ask AI configuration.
1. `bundle.include_paths` for extra assets/modules (for example `templates/interactive-diagram.html`, `knowledge_modules`).

See:

- `docs/operations/UNIFIED_CLIENT_CONFIG.md`
- `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md`
- `docs/operations/PLAN_TIERS.md`
- `docs/operations/CANONICAL_FLOW.md`

Important framing:

- API-first is one branch of the pipeline.
- Core product value is full docs-ops automation for all doc types and channels (quality gates, drift/stale/gaps, SEO/GEO, RAG/knowledge, terminology governance, and publication workflows).
- Self-check and fact/style-check baseline is enabled by default in the client profile template.

Public API sandbox quick profile (recommended):

```yaml
runtime:
  api_first:
    sandbox_backend: "external"
    mock_service: "custom"
    mock_base_url: "https://<your-real-public-mock-url>/v1"
    sync_playground_endpoint: true
    generate_test_assets: true
    upload_test_assets: true
    upload_test_assets_strict: false
    test_management:
      testrail:
        enabled_env: "TESTRAIL_UPLOAD_ENABLED"
        base_url_env: "TESTRAIL_BASE_URL"
        email_env: "TESTRAIL_EMAIL"
        api_key_env: "TESTRAIL_API_KEY"
        section_id_env: "TESTRAIL_SECTION_ID"
        suite_id_env: "TESTRAIL_SUITE_ID"
      zephyr_scale:
        enabled_env: "ZEPHYR_UPLOAD_ENABLED"
        base_url_env: "ZEPHYR_SCALE_BASE_URL"
        api_token_env: "ZEPHYR_SCALE_API_TOKEN"
        project_key_env: "ZEPHYR_SCALE_PROJECT_KEY"
        folder_id_env: "ZEPHYR_SCALE_FOLDER_ID"
    external_mock:
      enabled: true
      provider: "postman"
      base_path: "/v1"
      postman:
        api_key_env: "POSTMAN_API_KEY"
        workspace_id_env: "POSTMAN_WORKSPACE_ID"
        collection_uid_env: "POSTMAN_COLLECTION_UID"
        mock_server_id_env: "POSTMAN_MOCK_SERVER_ID"
```

What client fills into `.env.docsops.local` (one-time):

1. `POSTMAN_API_KEY`
1. `POSTMAN_WORKSPACE_ID`
1. optional `POSTMAN_COLLECTION_UID` (if missing, pipeline imports collection from generated OpenAPI)
1. Optional `POSTMAN_MOCK_SERVER_ID` (reuse existing mock)
1. Optional TestRail upload inputs:
   `TESTRAIL_UPLOAD_ENABLED`, `TESTRAIL_BASE_URL`, `TESTRAIL_EMAIL`, `TESTRAIL_API_KEY`, `TESTRAIL_SECTION_ID`, optional `TESTRAIL_SUITE_ID`
1. Optional Zephyr upload inputs:
   `ZEPHYR_UPLOAD_ENABLED`, `ZEPHYR_SCALE_API_TOKEN`, `ZEPHYR_SCALE_PROJECT_KEY`, optional `ZEPHYR_SCALE_BASE_URL`, optional `ZEPHYR_SCALE_FOLDER_ID`

After that, weekly/API-first flow prepares external mock automatically, generates API test assets from OpenAPI, and (if enabled) uploads test assets to TestRail/Zephyr.

Client does not need to share these secrets with operator.

## Pilot scope that proves full value (not API-only)

Use `profiles/clients/presets/pilot-evidence.yml` when you need a one-week pilot that demonstrates business value across the full docs lifecycle.

Pilot acceptance criteria:

1. Publish: at least one docs release goes live with working pages and API sandbox.
1. Quality gates: at least one issue is caught by gates before release (format/style/fact/example/API drift).
1. QA sync: API test assets are generated from OpenAPI and exported/uploaded to TestRail/Zephyr.
1. Knowledge quality: retrieval reports are generated (`Precision`, `Recall`, `Hallucination-rate`) and attached to pilot summary.
1. Throughput: measured before/after for one real update cycle (from code change to docs-ready PR).

Pilot outputs to show buyer:

1. `reports/consolidated_report.json`
1. `reports/retrieval_evals_report.json`
1. `docs/assets/knowledge-retrieval-index.json`
1. `docs/assets/knowledge-graph.jsonld`
1. `reports/api-test-assets/` (generated assets + upload report)

Output target:

- `reports/consolidated_report.json`

Client workflow becomes:

1. Open the weekly consolidated report.
1. Give report to local LLM batch workflow.
1. Quickly review final generated docs.

### RAG/knowledge base: fully automated mode (no manual commands)

How this works in the current pipeline:

1. Configure client profile once (`*.client.yml`):

- `runtime.modules.knowledge_validation: true`
- `runtime.modules.rag_optimization: true`
- `runtime.custom_tasks.weekly` with RAG tasks (for example intent builds)
- `bundle.include_paths: ["knowledge_modules"]`

1. Provision once:

- `provision_client_repo.py` installs `docsops/` into the client repo
- scheduler is installed immediately (`cron` or `Task Scheduler`)

1. Weekly job runs automatically:

- scheduled `run_weekly_gap_batch.py`
- runs:
  - `extract_knowledge_modules_from_docs.py`
  - `validate_knowledge_modules.py`
  - `generate_knowledge_retrieval_index.py`
  - any `custom_tasks.weekly` commands (for example `build_all_intent_experiences.py`)
- generates reports automatically

Result:

- no manual command execution by the client team
- human role is only to review weekly report and do a quick final docs sanity check

## Related guides

| Guide | What it covers |
| --- | --- |
| `CLIENT_HANDOFF.md` | Minimal client-side installation in 3 steps |
| `CUSTOMIZATION_PER_COMPANY.md` | Variables, policy packs, branding |
| `docs/operations/CENTRALIZED_CLIENT_BUNDLES.md` | Client profiles, bundles, scheduler setup |
| `docs/operations/UNIFIED_CLIENT_CONFIG.md` | Full client config keys with examples |
| `docs/operations/CANONICAL_FLOW.md` | One-page sales + delivery flow |
| `docs/operations/PLAN_TIERS.md` | Plan matrix and default presets (Basic/Pro/Enterprise) |
| `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md` | Complete list of available pipeline commands |
| `ALGOLIA_SETUP.md` | Full Algolia search integration |
| `SECURITY_OPERATIONS.md` | Secrets handling and permissions |
| `OPERATOR_RUNBOOK.md` | Delivery execution for operators |

## Next steps

- [Documentation index](../index.md)

## Implementation status (2026-03-25)

This document is aligned to the current production implementation baseline.

Current baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` flows.
1. REST and non-REST protocols are supported in one automation model: REST, GraphQL, gRPC, AsyncAPI, and WebSocket.
1. Non-REST automation includes server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated into the smooth autopipeline, including Postman-supported auto-prepare mode.
1. Contract test assets are generated automatically and merged with smart-merge rules so manual/customized cases are preserved.
1. Knowledge/RAG tasks run as part of automation when enabled (module extraction, validation, retrieval index, graph, evals).
1. Plan gating is enforced by configuration and policy packs; advanced non-REST automation is reserved for higher plans.

Canonical execution order reference:

- `docs/operations/CANONICAL_FLOW.md`
- `docs/operations/UNIFIED_CLIENT_CONFIG.md`
- `README.md`

Commercial note:

- Where commercial packaging is discussed, recurring service terms (retainer/licensing) are part of the active go-to-market model.
