# How to customize the README for your project

## Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.


When you fork or install the VeriOps into a new repository, update the README to reflect your product. This guide covers what to change.


## Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

## Replace product names

Search for "VeriOps" and replace with your product documentation name. Update these fields in the README:

- Project title and description.
- Any references to the pipeline name in badges or links.
- The footer or copyright line.

## Update badges

The pipeline generates SVG badges in `reports/`. Update the badge URLs in your README to point to your repository:

```markdown
![Quality Score](reports/quality-score.svg)
![Stale Docs](reports/stale-docs.svg)
![Gaps](reports/gaps.svg)
```

If you host badges externally, update the image URLs to your hosting location.

## Customize the feature list

The default README lists all pipeline features. Remove features you do not use and add any custom integrations:

- Remove Algolia search if you do not use it.
- Remove API sandbox references if your product has no API.
- Add any custom policy packs or templates you created.

## Add your deployment URL

Replace the default documentation site URL with your own:

```markdown
Live documentation: [docs.yourproduct.com](https://docs.yourproduct.com)
```

Update the `docs_url` in `docs/_variables.yml` to match.

## Update the quick start section

Replace the example commands with your repository URL and product-specific setup steps. Verify that all commands in the README work by running them.

For client delivery, prefer:

```bash
python3 scripts/onboard_client.py
```

Manual operator checks after onboarding:
\11. Review generated profile: `profiles/clients/generated/<client_id>.client.yml`.
\11. Review installed runtime config: `<client-repo>/docsops/config/client_runtime.yml`.
\11. Review installed policy: `<client-repo>/docsops/policy_packs/selected.yml`.
\11. Review env checklist: `<client-repo>/docsops/ENV_CHECKLIST.md`.

## Verify after changes

Run validation to confirm the README does not break any checks:

```bash
npm run validate:minimal
```

## Related guides

| Guide | What it covers |
| --- | --- |
| `quick-start.md` | 10-step setup for any environment |
| `SETUP_FOR_PROJECTS.md` | Full pipeline installation steps |
| `docs/operations/CANONICAL_FLOW.md` | One-page canonical flow for sales + delivery |
| `docs/operations/CENTRALIZED_CLIENT_BUNDLES.md` | Centralized per-client profiles, bundle provisioning, weekly automation |
| `docs/operations/UNIFIED_CLIENT_CONFIG.md` | Full config reference (all keys) |
| `docs/operations/PLAN_TIERS.md` | Plan matrix and ready presets (Basic/Pro/Enterprise) |
| `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md` | Full capabilities list generated from package scripts |

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
