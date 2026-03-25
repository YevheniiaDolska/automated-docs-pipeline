# Pilot service proposal (10-14 days)

## Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.



## Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

## What you get

This pilot is a focused 10-14 calendar day engagement (typically 5-10 business days) that installs the VeriOps on your real repository and delivers measurable results. This is not a demo. You receive a working system, generated documentation, and data that proves the value.

## Deliverables

### 1. Configured pipeline

The pipeline is installed and configured in your repository with:

- Quality gates active in CI (markdownlint, frontmatter validation, SEO/GEO checks, code example smoke tests).
- `minimal.yml` policy pack with relaxed thresholds for initial adoption.
- `docs/_variables.yml` populated with your product information.
- 3-5 templates customized for your product and content model.

### 2. First consolidated report processed

The consolidated report merges gap detection, KPI data, and staleness analysis into one prioritized document. It identifies:

- Missing documentation ranked by business impact.
- Stale pages that need updating.
- Quality issues across existing documentation.
- SEO/GEO optimization opportunities.

### 3. Generated documentation (5-10 pages)

Claude Code processes the consolidated report and generates 5-10 documents from the highest-priority items. Each document:

- Uses a pre-validated template from the 31-template library.
- References shared variables (no hardcoded product names, URLs, or ports).
- Passes all 8-stage quality pipeline (Vale, markdownlint, cspell, frontmatter, SEO/GEO, contract, drift).
- Includes self-verified code examples and fact-checked assertions.

### 4. Before/after KPI comparison

Baseline measurements are captured at kickoff and final measurements are captured at handoff:

- Documentation quality score.
- Stale documentation percentage.
- High-priority gap count.
- Metadata completeness.

### 5. Team training

A 60-90 minute session covering:

- How to create documentation from templates.
- How to run local validation (`npm run validate:minimal`).
- How to read the consolidated report.
- How to use Claude Code with the pipeline instructions.

## What happens after the pilot

If you proceed to full implementation, the pilot foundation stays. You switch to a stricter policy pack, enable all CI gates, and customize all templates. Nothing is thrown away.

If you stop after the pilot, you keep everything: CI checks, templates, analysis scripts, and the baseline report. The quality gates continue enforcing standards on every pull request.

## Timeline

| Phase | Focus |
| --- | --- |
| Kickoff (Days 1-2) | Install pipeline, capture baseline, configure variables |
| Build (Days 3-6) | Customize templates, enable core quality gate, run first consolidation |
| Hardening (Days 7-10) | Generate/fix priority docs, run validations, stabilize outputs |
| Handoff (Days 11-14) | Final measurement, team training, handoff |

## Next step

Book a 15-20 minute discovery call to confirm fit, repository prerequisites, and pilot success criteria before kickoff.

## Related guides

| Guide | What it covers |
| --- | --- |
| `PILOT_START_HERE.md` | Step-by-step self-serve pilot instructions |
| `PILOT_VS_FULL_IMPLEMENTATION.md` | Comparison of pilot vs full rollout |
| `PRICING_STRATEGY_REVISED.md` | Pricing model and packages |

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
