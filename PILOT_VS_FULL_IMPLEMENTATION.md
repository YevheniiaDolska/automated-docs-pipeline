# Pilot vs full implementation

This document compares the two delivery modes for the Auto-Doc Pipeline. Both use the same codebase. The difference is configuration scope and team involvement.

## Comparison table

| Aspect | Pilot (10-14 days) | Full implementation (ongoing) |
| --- | --- | --- |
| **Duration** | 10-14 calendar days (typically 5-10 business days) | 3-6 weeks initial, then continuous |
| **Policy pack** | `minimal.yml` | `api-first.yml`, `plg.yml`, or custom |
| **Quality score threshold** | 75 | 82-84 |
| **Max stale percentage** | 20% | 10-12% |
| **Max high-priority gaps** | 10 | 5-6 |
| **Documents generated** | 5-10 | All documentation |
| **Team size** | 1 person | Full documentation team |
| **CI gates** | `docs-check.yml` only | All 4 mandatory gates |
| **Templates customized** | 3-5 core templates | All 31 templates |
| **Variables** | Basic product info | Full variable set |
| **Gap detection** | Baseline scan | Weekly automated scans |
| **KPI reporting** | Before/after snapshot | Weekly dashboard with trends |
| **Consolidated reports** | 1 report processed | Weekly automated reports |
| **AI instructions** | Standard `CLAUDE.md` | Customized with company style |
| **Algolia search** | Not included | Optional |
| **API sandbox** | Not included | Optional |
| **Lifecycle management** | Not enabled | Enabled with thresholds |
| **Training** | Self-serve guides | Hands-on team walkthrough |

## When to choose each mode

**Choose the pilot when:**

1. You want to prove value before committing resources.
1. You need a before/after KPI comparison to justify investment.
1. One person can run the evaluation independently.

**Choose full implementation when:**

1. The pilot proved value and the team is ready to scale.
1. Documentation quality is a business priority.
1. You need all CI gates enforcing standards on every pull request.

## How to switch from pilot to full

1. Change the policy pack from `minimal.yml` to your target pack.
1. Enable the remaining 3 CI gates (DoD contract, drift, smoke tests).
1. Expand `docs/_variables.yml` to the full variable set.
1. Customize all templates for your product.
1. Enable scheduled workflows (KPI wall, lifecycle, gap detection).

No data migration is needed. The pilot configuration is a subset of the full configuration.

## Related guides

| Guide | What it covers |
| --- | --- |
| `PILOT_START_HERE.md` | Step-by-step pilot instructions |
| `MINIMAL_MODE.md` | Details on the minimal policy pack |
| `POLICY_PACKS.md` | All five policy packs |
