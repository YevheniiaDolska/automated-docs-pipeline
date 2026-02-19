# Policy packs (beginner-friendly)

Policy packs help you adapt one docs pipeline to different companies.

Think of a policy pack as a rules profile.

You choose a profile, then run checks with that profile.

## What a policy pack controls

A pack defines:

1. Which files count as interface changes.
1. Which docs files must be updated when interface changes.
1. Which files count as API or SDK drift signals.
1. KPI SLA thresholds for reporting.

## Available packs in this repository

1. `policy_packs/minimal.yml`
1. `policy_packs/api-first.yml`
1. `policy_packs/monorepo.yml`
1. `policy_packs/multi-product.yml`

## Which pack to choose

### Choose `minimal.yml` when

1. Team is new to the pipeline.
1. Company has strict security restrictions.
1. You need fastest pilot onboarding.

### Choose `api-first.yml` when

1. OpenAPI is a core source of truth.
1. API and SDK changes happen often.
1. Drift prevention is high priority.

### Choose `monorepo.yml` when

1. Multiple services live in one repository.
1. Docs and code are split across many folders.

### Choose `multi-product.yml` when

1. One docs system supports multiple products.
1. You need stricter boundaries by product area.

## First run (recommended for beginners)

Start with `minimal.yml`.

Run:

```bash
python3 scripts/check_docs_contract.py --base origin/main --head HEAD --policy-pack policy_packs/minimal.yml
python3 scripts/check_api_sdk_drift.py --base origin/main --head HEAD --policy-pack policy_packs/minimal.yml --json-output reports/api_sdk_drift_report.json --md-output reports/api_sdk_drift_report.md
python3 scripts/evaluate_kpi_sla.py --current reports/kpi-wall.json --policy-pack policy_packs/minimal.yml --json-output reports/kpi-sla-report.json --md-output reports/kpi-sla-report.md
```

## Same checks with API-first pack

```bash
python3 scripts/check_docs_contract.py --base origin/main --head HEAD --policy-pack policy_packs/api-first.yml
python3 scripts/check_api_sdk_drift.py --base origin/main --head HEAD --policy-pack policy_packs/api-first.yml --json-output reports/api_sdk_drift_report.json --md-output reports/api_sdk_drift_report.md
python3 scripts/evaluate_kpi_sla.py --current reports/kpi-wall.json --policy-pack policy_packs/api-first.yml --json-output reports/kpi-sla-report.json --md-output reports/kpi-sla-report.md
```

## How to customize a pack safely

1. Copy an existing pack file.
1. Rename it, for example `policy_packs/client-acme.yml`.
1. Change only patterns and thresholds first.
1. Run checks locally.
1. Enable in workflow after local pass.

## Common mistakes

1. Making patterns too broad, which creates noise.
1. Making patterns too narrow, which misses real drift.
1. Setting SLA thresholds with no baseline data.

## Recommended rollout path

1. Week 1: `minimal.yml`
1. Week 2: tighten thresholds using baseline reports.
1. Week 3+: move to `api-first.yml` or custom client pack.

## Definition of done for policy pack rollout

A policy pack rollout is done when:

1. Local checks pass with the selected pack.
1. PR checks pass with the selected pack.
1. Team understands why failures happen and how to fix them.
1. Baseline and target thresholds are documented.
