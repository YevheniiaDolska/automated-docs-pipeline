# Private repository setup

## Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.


The VeriOps works in private GitHub repositories with minimal additional configuration. This guide covers repository settings, secrets, workflow permissions, Algolia with a private index, and local-only AI processing.


## Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

## GitHub Actions permissions

Private repositories require explicit permissions for GitHub Actions:

1. Go to `Settings` > `Actions` > `General`.
1. Under "Actions permissions," select `Allow all actions and reusable workflows`.
1. Under "Workflow permissions," select `Read and write permissions` if you want lifecycle management to create issues automatically. Select `Read repository contents` for minimum access.
1. Click `Save`.

Each workflow file declares its own `permissions` block. The repository-level setting acts as an upper bound.

## Secrets configuration

The core pipeline (quality checks, contract enforcement, drift detection, smoke tests) requires no secrets. It uses only the default `GITHUB_TOKEN`.

For optional integrations, add secrets in `Settings` > `Secrets and variables` > `Actions`:

| Secret | Required for | Purpose |
| --- | --- | --- |
| `ALGOLIA_APP_ID` | Algolia search | Application ID |
| `ALGOLIA_ADMIN_KEY` | Algolia search | Admin API key |
| `ALGOLIA_INDEX_NAME` | Algolia search | Index name |

## Workflow permissions per gate

| Workflow | Minimum permission | Notes |
| --- | --- | --- |
| `docs-check.yml` | `contents: read` | Core quality checks |
| `pr-dod-contract.yml` | `contents: read` | Contract enforcement |
| `api-sdk-drift-gate.yml` | `contents: read` | Drift detection |
| `code-examples-smoke.yml` | `contents: read` | Code example verification |
| `lifecycle-management.yml` | `contents: read`, `issues: write` | Creates issues for stale pages |
| `kpi-wall.yml` | `contents: write` | Commits KPI reports |

## Algolia with a private index

For private documentation sites, configure Algolia to use a private index:

1. Create a separate Algolia index for the private repository.
1. Use a search-only API key (not the admin key) in your documentation site configuration.
1. The admin key goes into GitHub Actions secrets only and is never exposed in the built site.
1. Set `ALGOLIA_INDEX_NAME` to your private index name.

## Local AI processing

Claude Code runs locally on your machine. No documentation content leaves your environment:

1. Claude Code reads the consolidated report from `reports/`.
1. It generates documentation using templates and variables from the local repository.
1. Generated files are written to `docs/` on your local filesystem.
1. You review, commit, and push through your normal Git workflow.

The `CLAUDE.md` and `AGENTS.md` instruction files stay in your repository and are never sent to external services.

## Branch protection

After merging the pipeline to `main`, configure branch protection:

1. Go to `Settings` > `Branches`.
1. Add or edit the rule for `main`.
1. Enable `Require status checks to pass before merging`.
1. Add the 4 mandatory status checks: docs-check, PR DoD contract, API/SDK drift gate, code examples smoke.

## Related guides

| Guide | What it covers |
| --- | --- |
| `SETUP_FOR_PROJECTS.md` | Full pipeline installation steps |
| `SECURITY_OPERATIONS.md` | Secrets management and incident response |
| `MINIMAL_MODE.md` | Running core checks without optional integrations |

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
