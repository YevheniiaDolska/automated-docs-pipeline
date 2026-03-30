# Start a 10-14 day pilot of this pipeline

## Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.


This guide walks you through a focused 10-14 calendar day pilot (typically 5-10 business days) of the VeriOps on your own repository. By the end, you have working quality gates, automated weekly reporting, and generated documentation.

## Commercial scope (fixed)

- Pilot package: **$5,000**.
- Pilot goal: prove value in one real repository.
- Next package after successful pilot: **full implementation for $15,000**.
- After full implementation: optional monthly retainer.

What is included in pilot:

1. One repository setup and configuration.
1. Core quality gates enabled.
1. One consolidated report cycle.
1. 5-10 generated/updated docs with validation.
1. KPI baseline and handoff/training session.

What is not included in pilot:

1. Multi-repository rollout.
1. Custom feature development.
1. 24/7 SLA support.


## Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

## Prerequisites

You need Git, Node.js 18+, Python 3.11+, and npm installed. On Windows, use `py -3` if `python3` does not work.

## Step 1: Fork the repository

Fork or clone the VeriOps repository:

```bash
git clone <your-fork-url>
cd "VeriOps"
python3 -m pip install -r requirements.txt
npm install
```

## Step 2: Edit `_variables.yml`

Open `docs/_variables.yml` and replace the placeholder values with your product information:

```yaml
product_name: "Your Product"
product_full_name: "Your Product platform"
current_version: "1.0.0"
cloud_url: "https://app.yourproduct.com"
docs_url: "https://docs.yourproduct.com"
support_email: "support@yourcompany.com"
default_port: 8080
```

Every document references these variables. Update them once and all docs reflect your product.

## Step 3: Choose the minimal policy pack

The `minimal.yml` policy pack uses relaxed thresholds suitable for a pilot:

- Minimum quality score: 75 (instead of 82-84)
- Maximum stale percentage: 20% (instead of 10-12%)
- Maximum high-priority gaps: 10 (instead of 5-6)

No workflow changes are needed for local testing. For CI, set the policy pack input:

```yaml
# In workflow files
with:
  policy_pack: policy_packs/minimal.yml
```

## Step 4: Enable weekly automation (recommended)

Provision once and install scheduler:

```bash
python3 scripts/provision_client_repo.py \
  --client profiles/clients/examples/basic.client.yml \
  --client-repo /path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler linux
```

## Step 5: Run the consolidated report now (optional)

Generate a single report that merges gap detection, KPI data, and staleness analysis:

```bash
npm run consolidate
```

This produces a consolidated report in `reports/` that identifies missing documentation, stale pages, and quality issues in priority order.

## Step 6: Process with Claude Code

Feed the consolidated report to Claude Code. The `CLAUDE.md` and `AGENTS.md` files in the repository instruct the AI to:

\11. Select the correct template from `templates/`.
\11. Use variables from `docs/_variables.yml`.
\11. Follow all style and formatting rules.
\11. Self-verify code examples and fact-check assertions.

Generate 5-10 documents from the highest-priority items in the report.

## Step 7: Review results

Run validation on the generated documents:

```bash
npm run validate:minimal
```

Review each document for factual accuracy. The pipeline handles formatting, style, and SEO/GEO optimization. You verify that the technical content is correct for your product.

## Step 8: Decide on full implementation

After the pilot, you have:

\11. A working quality gate system.
\11. A consolidated report showing documentation health.
\11. 5-10 generated documents that pass all linters.
\11. Baseline KPI data for before/after comparison.

To move to full implementation, switch to a stricter policy pack (`api-first.yml` or `plg.yml`), enable all four CI gates, and customize the remaining templates. See `PILOT_VS_FULL_IMPLEMENTATION.md` for details.

## Related guides

| Guide | What it covers |
| --- | --- |
| `PILOT_VS_FULL_IMPLEMENTATION.md` | Comparison of pilot vs full rollout |
| `MINIMAL_MODE.md` | Details on the minimal policy pack |
| `quick-start.md` | 10-step setup for any environment |

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
