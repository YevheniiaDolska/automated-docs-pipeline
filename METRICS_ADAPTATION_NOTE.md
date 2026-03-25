# How to adapt KPI metrics for different products

## Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.


Each product has different documentation requirements. The VeriOps provides configurable policy packs, staleness thresholds, interface patterns, and quality score targets that you adjust to match your team and product.


## Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

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
