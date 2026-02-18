# Policy Packs

## Purpose

Policy packs let teams tune docs-automation behavior without changing Python code.
Use a policy pack to adapt gates for API-first, monorepo, or multi-product repositories.

## Available Packs

- `policy_packs/api-first.yml`
- `policy_packs/monorepo.yml`
- `policy_packs/multi-product.yml`

## Fields

### `docs_contract`

- `interface_patterns`: Changed files that imply documentation is required.
- `doc_patterns`: Files that satisfy the docs-update requirement.

### `drift`

- `openapi_patterns`: OpenAPI/spec-related change patterns.
- `sdk_patterns`: SDK/client change patterns.
- `reference_doc_patterns`: Reference docs paths that resolve drift.

### `kpi_sla`

- `min_quality_score`
- `max_stale_pct`
- `max_high_priority_gaps`
- `max_quality_score_drop`

## Usage Examples

```bash
python3 scripts/check_docs_contract.py \
  --base origin/main \
  --head HEAD \
  --policy-pack policy_packs/monorepo.yml
```

```bash
python3 scripts/check_api_sdk_drift.py \
  --base origin/main \
  --head HEAD \
  --policy-pack policy_packs/multi-product.yml
```

```bash
python3 scripts/evaluate_kpi_sla.py \
  --current reports/kpi-wall.json \
  --policy-pack policy_packs/api-first.yml
```
