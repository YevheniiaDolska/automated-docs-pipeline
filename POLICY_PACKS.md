# Policy packs

Policy packs let you adapt one pipeline to different companies without rewriting scripts.

## Available packs

1. `policy_packs/minimal.yml`
1. `policy_packs/api-first.yml`
1. `policy_packs/monorepo.yml`
1. `policy_packs/multi-product.yml`

## What a policy pack controls

1. Interface-to-docs contract patterns.
1. API/SDK drift detection patterns.
1. KPI SLA thresholds.

## How to run with a pack

Docs contract:

```bash
python3 scripts/check_docs_contract.py --base origin/main --head HEAD --policy-pack policy_packs/minimal.yml
```

Drift check:

```bash
python3 scripts/check_api_sdk_drift.py --base origin/main --head HEAD --policy-pack policy_packs/api-first.yml
```

KPI SLA:

```bash
python3 scripts/evaluate_kpi_sla.py --current reports/kpi-wall.json --policy-pack policy_packs/minimal.yml
```

## Recommendation for new clients

1. Start with `minimal.yml`.
1. Move to `api-first.yml` if API-driven.
1. Add stricter thresholds after baseline.
