# Pilot vs full implementation

## Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.


This document compares the two delivery modes for the VeriOps. Both use the same codebase. The difference is configuration scope and team involvement.


## Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

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
