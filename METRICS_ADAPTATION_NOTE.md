# How to adapt KPI metrics for different products

Each product has different documentation requirements. The VeriOps provides configurable policy packs, staleness thresholds, interface patterns, and quality score targets that you adjust to match your team and product.

## Customize policy packs

The pipeline ships with 5 built-in policy packs. Choose the one closest to your needs, then customize:

| Pack | Quality score | Stale % | Gaps | Best for |
| --- | --- | --- | --- | --- |
| `minimal.yml` | 75 | 20% | 10 | Pilots, new teams |
| `api-first.yml` | 82 | 12% | 6 | API-heavy products |
| `plg.yml` | 84 | 10% | 5 | Self-serve products |
| `monorepo.yml` | 80 | 15% | 8 | Multiple services |
| `multi-product.yml` | 80 | 15% | 8 | Multiple products |

To create a custom pack, copy the closest built-in pack and adjust the thresholds:

```bash
cp policy_packs/api-first.yml policy_packs/custom.yml
```

Edit `custom.yml` to match your targets:

```yaml
kpi_sla:
  min_quality_score: 80
  max_stale_pct: 15.0
  max_high_priority_gaps: 8
  max_quality_score_drop: 5
```

## Adjust stale_days threshold

The `stale_days` parameter controls how many days a document can go without updates before it is flagged as stale. Adjust based on your release cadence:

| Release cadence | Recommended stale_days |
| --- | --- |
| Weekly releases | 30 |
| Monthly releases | 60 |
| Quarterly releases | 90 |
| Stable product (rare changes) | 180 |

Set the value when running KPI generation:

```bash
python3 scripts/generate_kpi_wall.py \
  --docs-dir docs \
  --reports-dir reports \
  --stale-days 60
```

## Configure interface_patterns for drift detection

The `interface_patterns` setting determines which source code files trigger the "docs must update" requirement. Customize these patterns to match your project structure:

```yaml
docs_contract:
  interface_patterns:
    - '^src/api/'
    - '^src/controllers/'
    - 'openapi.*\.(ya?ml|json)$'
    - '^sdk/'
  doc_patterns:
    - '^docs/'
    - '^templates/'
```

If drift detection generates false positives, narrow the patterns. If it misses real drift, expand them.

## Set quality score targets based on team maturity

Start with achievable targets and tighten them as the team improves:

| Team maturity | Recommended min score | Max stale % |
| --- | --- | --- |
| First month (learning) | 70 | 25% |
| Months 2-3 (building habits) | 75 | 20% |
| Months 4-6 (consistent) | 80 | 15% |
| Months 6+ (mature) | 85 | 10% |

Update the policy pack thresholds as the team progresses. The `max_quality_score_drop` prevents regressions: set it to 8 for new teams and tighten to 3 for mature teams.

## Verify your custom configuration

After adjusting thresholds, run the full evaluation to confirm the settings work:

```bash
python3 scripts/evaluate_kpi_sla.py \
  --current reports/kpi-wall.json \
  --policy-pack policy_packs/custom.yml \
  --md-output reports/kpi-sla-report.md
```

Review the report. If every metric passes on the first run, the thresholds may be too lenient. If every metric fails, they are too strict. Aim for 1-2 metrics near the threshold to drive continuous improvement.

## Related guides

| Guide | What it covers |
| --- | --- |
| `POLICY_PACKS.md` | Full policy pack documentation |
| `CUSTOMIZATION_PER_COMPANY.md` | Per-company configuration steps |
| `PLG_PLAYBOOK.md` | PLG-specific thresholds and patterns |
