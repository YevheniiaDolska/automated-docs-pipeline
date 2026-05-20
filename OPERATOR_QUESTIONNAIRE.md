# Operator questionnaire (Google Form source)

Use two separate forms:

1. Pilot intake form
1. Full implementation intake form

Do not send technical/internal operator questions to clients.

## 1) Pilot intake form (short, evidence-oriented)

Ask these questions:

1. Company legal name
1. Product name
1. Primary docs owner email
1. Technical fallback contact email
1. Weekly run schedule confirmation:
   - default is Monday, 10:00 local client time
   - timezone is auto-resolved by installer
1. Required documentation languages (multi-select):
   - English (default)
   - Additional required locales (for example German, Spanish, French, Japanese)
1. Pilot scope confirmation:
   - pilot duration is 21 days
   - one repository only
   - Ask AI runtime add-on is not included by default
   - external mock provider setup is optional and only if explicitly requested

Optional pilot add-ons (ask only if needed):

1. Enable external public sandbox instead of local prism? (`yes`/`no`)
1. Enable TestRail/Zephyr upload in pilot? (`yes`/`no`)
1. Enable Algolia integration in pilot? (`yes`/`no`)

## 2) Full implementation intake form

### Identity

1. Company legal name
1. Product name
1. Primary docs owner email
1. Technical fallback contact email

### Documentation platform and publishing

1. Site generator (`mkdocs`/`docusaurus`/`sphinx`/`hugo`/`jekyll`)
1. Publish targets (for example `mkdocs`, `readme`, `github`)
1. Preview URL pattern (optional, auto-detected after first publish; fill manually only if detection fails)
1. Production docs URL (optional, auto-detected from site config/publish output; fill manually only if detection fails)

### Quality and style

1. Style guide (`google`/`microsoft`/`hybrid`)
1. Terminology source (glossary file/team owner)
1. Any banned terms or naming restrictions

### Flow mode

1. Docs flow mode (`code-first`/`api-first`/`hybrid`)
1. Should API-first run weekly by default? (`yes`/`no`)

### API sandbox

1. Sandbox backend (`docker`/`prism`/`external`)
1. External mock base URL (if `external`)

### API test management

1. Generate API test assets from OpenAPI? (`yes`/`no`)
1. Upload test assets automatically? (`yes`/`no`)
1. TestRail enabled? (`yes`/`no`)
1. Zephyr Scale enabled? (`yes`/`no`)
1. Target TestRail section/suite IDs (if used)
1. Target Zephyr project/folder (if used)

### Integrations

1. Algolia enabled? (`yes`/`no`)
1. Algolia upload on weekly run? (`yes`/`no`)
1. Ask AI enabled? (`yes`/`no`)
1. Ask AI provider (`openai`/`anthropic`/`azure-openai`/`custom`)
1. Ask AI billing mode (`disabled`/`user-subscription`/`platform-paid`)
1. Ask AI runtime pack install on provision? (`yes`/`no`)

### RAG and knowledge preparation

1. Enable knowledge modules extraction? (`yes`/`no`)
1. Enable retrieval index generation? (`yes`/`no`)
1. Enable JSON-LD graph generation? (`yes`/`no`)
1. Enable retrieval evals? (`yes`/`no`)
1. Retrieval thresholds overrides (if any)

### Modules and controls

1. Any modules to disable explicitly? (provide examples in form help text)
1. Confirm default automation schedule:
   - Monday, 10:00 local time
   - Linux/Windows/macOS scheduler install
1. Enable git sync before weekly run? (`yes`/`no`)

### Governance and security

1. PR auto-fix workflow enabled? (`yes`/`no`)
1. Require PR label for bot changes? (`yes`/`no`)
1. Enable PR auto-merge when all checks are green? (`yes`/`no`)
1. Who approves bot commits?
1. Any compliance constraints:
   - strict-local only
   - no external data egress
   - custom security policy requirements

## Operator-only notes (not for client form)

1. `client_id` slug is auto-generated from company name + product name.
1. Repository/branch/docs-api-sdk path discovery is auto-detected in bootstrap and should not be asked in client form.
1. Weekly schedule defaults to Monday 10:00 local time unless explicitly overridden.
1. Ask AI runtime is a paid add-on and is not enabled by default in SaaS bundles.
