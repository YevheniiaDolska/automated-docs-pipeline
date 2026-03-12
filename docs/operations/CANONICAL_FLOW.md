---
title: "Canonical Flow (Sales + Delivery)"
description: "Canonical sales and delivery flow for onboarding and operating client Auto-Doc Pipeline setups."
content_type: reference
product: both
last_reviewed: "2026-03-11"
tags:
  - Operations
  - Client Onboarding
---

# Canonical Flow (Sales + Delivery)

This is the single source of truth for how to sell and run the pipeline today.

## 1. Core promise

One-time setup, then smooth weekly automation:

\11. Generate/configure client profile.
\11. Provision bundle into client repo.
\11. Install scheduler.
\11. Weekly reports and checks run automatically.
\11. Human only reviews report + final docs.

## 2. One-time setup (you do this)

\11. Pick preset:

- `profiles/clients/presets/small.yml`
- `profiles/clients/presets/startup.yml`
- `profiles/clients/presets/enterprise.yml`

\11. Fastest path:

```bash
python3 scripts/onboard_client.py
```

\11. If you use manual mode, customize client profile:

- client identity
- repo paths (`docs_root`, `api_root`, `sdk_root`)
- output targets
- module toggles
- policy/plan strictness

\11. Choose delivery mode:

- Same machine mode (you can access client repo path directly): use provisioning.
- Different laptops mode: build bundle on your machine, then client installs scheduler locally.

\11. Provision (same machine mode):

```bash
python3 scripts/provision_client_repo.py \
  --client profiles/clients/<client>.client.yml \
  --client-repo /path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler linux
```

Windows:

```bash
python3 scripts/provision_client_repo.py \
  --client profiles/clients/<client>.client.yml \
  --client-repo C:/path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler windows
```

\11. Build + handoff (different laptops mode):

```bash
python3 scripts/build_client_bundle.py --client profiles/clients/<client>.client.yml
```

Client installs scheduler after copying bundle into `<client-repo>/docsops`:

```bash
bash docsops/ops/install_cron_weekly.sh
```

Windows:

```bash
powershell -ExecutionPolicy Bypass -File docsops/ops/install_windows_task.ps1
```

Scheduler timezone is local machine timezone. Monday schedule follows client local time when installed on client machine.

## 3. Weekly automation (no manual commands)

Scheduler runs:

- `docsops/scripts/run_weekly_gap_batch.py`

It executes:

- gap detection
- stale checks
- drift + docs contract (if enabled)
- KPI/SLA (if enabled)
- API-first flow (if enabled)
  - manual overrides apply (`apply_openapi_overrides.py`)
  - regression gate (`check_openapi_regression.py`)
- RAG/knowledge tasks:
  - `extract_knowledge_modules_from_docs.py`
  - `validate_knowledge_modules.py`
  - `generate_knowledge_retrieval_index.py`
  - `generate_knowledge_graph_jsonld.py`
  - `run_retrieval_evals.py` (Precision/Recall/Hallucination-rate)
- terminology governance:
  - `sync_project_glossary.py` (syncs glossary markers to `glossary.yml`)
- multi-language examples standard:
  - `generate_multilang_tabs.py`
  - `validate_multilang_examples.py`
  - `check_code_examples_smoke.py` (including `expected-output` comparison for tagged blocks)
- intent bundle assembly via `build_all_intent_experiences.py` when enabled in `runtime.custom_tasks.weekly`
- `custom_tasks.weekly` commands
- consolidated report generation

Output:

- `reports/consolidated_report.json`
- related reports are regenerated to the same filenames each run (no manual cleanup required)
- `reports/docsops_status.json` (quick freshness/status check for non-technical users)

Client repo `.gitignore` recommendation:

```gitignore
reports/docsops-weekly.log
```

## 4. Human role

\11. In file explorer, check Modified date of `reports/consolidated_report.json`.
\11. If date/time is fresh, ask local LLM to process the report.
\11. Review generated docs quickly.
\11. Publish/merge.

## 5. Operator manual checks after setup

\11. Check `<client-repo>/docsops/config/client_runtime.yml` for correct client values.
\11. Check `<client-repo>/docsops/policy_packs/selected.yml` for expected policy pack/overrides.
\11. Check `<client-repo>/docsops/ENV_CHECKLIST.md` and align secrets with client.
\11. Run one smoke weekly cycle and ensure `reports/consolidated_report.json` is refreshed.

## 6. Plan packaging

- Basic: essential quality + gaps + stale.
- Pro: adds drift/contract, KPI/SLA, RAG/knowledge, hybrid/API-first.
- Enterprise: strict policy, full automation surface, advanced verification.

Details: `docs/operations/PLAN_TIERS.md`.

## 7. What to say in sales calls

\11. "You get one-time setup, then weekly documentation ops on autopilot."
\11. "Your team stops doing doc plumbing and only reviews final output."
\11. "Quality is controlled by policy packs and automated gates."
\11. "RAG/knowledge is maintained automatically, so AI outputs stay grounded."

## 8. Compatibility mode

If needed, run equivalent weekly flow via GitHub Actions cron (`weekly-consolidation.yml` and companion workflows). Recommended mode remains local scheduler automation in client repo.

## 9. Deep references

- `SETUP_FOR_PROJECTS.md`
- `docs/operations/CENTRALIZED_CLIENT_BUNDLES.md`
- `docs/operations/UNIFIED_CLIENT_CONFIG.md`
- `docs/operations/PLAN_TIERS.md`
- `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md`

## Next steps

- [Documentation index](../index.md)
