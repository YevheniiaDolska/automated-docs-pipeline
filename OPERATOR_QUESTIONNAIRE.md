# Operator questionnaire (copy-paste)

## Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.


Use this exact checklist to collect all required client inputs in one pass.


## Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

## Pilot fast intake (use this block for pilot-evidence)

Ask only these questions for a fast pilot setup:

1. Company legal name:
1. Product name:
1. Client ID slug:
1. Primary docs owner email:
1. Repository URL + default branch:
1. Docs root path:
1. API root path:
1. SDK root path:
1. Weekly run timezone:
1. Weekly run time (or use default Monday 10:00 local):
1. Engagement scope confirmation:
   - pilot only,
   - no PR auto-fix,
   - no Ask AI/Algolia integrations during pilot,
   - no external mock provider credentials during pilot,
   - no RAG/knowledge automation in pilot (index/graph/retrieval evals off).

Optional pilot add-ons (ask only if needed):

1. Enable external public sandbox instead of local prism? (`yes`/`no`)
1. Enable TestRail/Zephyr upload in pilot? (`yes`/`no`)
1. Enable PR auto-fix in pilot? (`yes`/`no`)

## 1) Identity

1. Company legal name:
1. Product name:
1. Client ID slug (for example `acme-payments`):
1. Primary docs owner email:
1. Technical fallback contact:

## 2) Repository and structure

1. Repository URL:
1. Default branch:
1. Monorepo or single repo:
1. Docs root path:
1. API root path:
1. SDK root path:
1. Planning notes path (for API-first):

## 3) Docs platform and publishing

1. Site generator (`mkdocs`/`docusaurus`/`sphinx`/`hugo`/`jekyll`):
1. Publish targets (comma-separated, for example `mkdocs,readme,github`):
1. Preview URL pattern (if available):
1. Production docs URL (if available):

## 4) Quality and style

1. Style guide (`google`/`microsoft`/`hybrid`):
1. Terminology source (glossary file/team owner):
1. Any banned terms or naming restrictions:
1. Quality threshold target (if custom):

## 5) Flow mode

1. Docs flow mode (`code-first`/`api-first`/`hybrid`):
1. Should API-first run weekly by default? (`yes`/`no`)

## 6) API sandbox

1. Sandbox backend (`docker`/`prism`/`external`):
1. External mock base URL (if `external`):
1. Sync playground endpoint automatically? (`yes`/`no`)
1. Verify API user path automatically? (`yes`/`no`)

## 7) External mock provider (if external sandbox)

1. Provider (`postman`/other):
1. Reuse existing mock server? (`yes`/`no`)
1. Postman workspace ID:
1. Postman collection UID (optional):
1. Postman mock server ID (optional):

## 8) API test management

1. Generate API test assets from OpenAPI? (`yes`/`no`)
1. Upload test assets automatically? (`yes`/`no`)
1. TestRail enabled? (`yes`/`no`)
1. Zephyr Scale enabled? (`yes`/`no`)
1. Target TestRail section/suite IDs (if used):
1. Target Zephyr project/folder (if used):

## 9) Integrations

1. Algolia enabled? (`yes`/`no`)
1. Algolia upload on weekly run? (`yes`/`no`)
1. Ask AI enabled? (`yes`/`no`)
1. Ask AI provider (`openai`/`anthropic`/`azure-openai`/`custom`):
1. Ask AI billing mode (`disabled`/`user-subscription`/`platform-paid`):
1. Ask AI runtime pack install on provision? (`yes`/`no`)

## 10) RAG and knowledge

1. Enable knowledge modules extraction? (`yes`/`no`)
1. Enable retrieval index generation? (`yes`/`no`)
1. Enable JSON-LD graph generation? (`yes`/`no`)
1. Enable retrieval evals? (`yes`/`no`)
1. Retrieval thresholds overrides (if any):

## 11) Modules and tasks

1. Any modules to disable explicitly?
1. Extra weekly task commands to add?
1. Include extra bundle paths (templates/assets/modules)?
1. Include extra scripts beyond defaults?

## 12) Automation schedule

1. Weekly run day:
1. Weekly run time (local):
1. Timezone:
1. Install scheduler on (`linux`/`windows`/`none`):
1. Enable git sync before weekly run? (`yes`/`no`)

## 13) Governance and security

1. Who manages secrets?
1. Should operator have access to secrets? (`usually no`)
1. PR auto-fix workflow enabled? (`yes`/`no`)
1. Require PR label for bot changes? (`yes`/`no`)
1. Enable PR auto-merge when all checks are green? (`yes`/`no`)
1. Who approves bot commits?

## 14) Delivery scope

1. Engagement type (`pilot`/`full implementation`):
1. If pilot, which modules are in scope?
1. If pilot, which modules are intentionally excluded?
1. Pilot acceptance criteria (top 3-5):

## 15) Success metrics (baseline and target)

1. Current time-to-publish:
1. Target time-to-publish:
1. Current doc defect/ticket rate:
1. Target defect/ticket rate:
1. Reporting cadence:

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
