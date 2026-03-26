# Claude Code instructions for documentation pipeline

Plan scope: Enterprise (full-surface instructions).

## Write documents right the first time

**Claude, you MUST follow ALL these rules to avoid 20 iterations of fixes.**
**Every document you create MUST pass ALL linters on the first try.**

## Project overview

This is an automated documentation pipeline for technical products. When writing or editing documentation, follow these rules strictly to ensure all linting checks pass.

## Mandatory pipeline execution for API docs

The pipeline supports five API protocols: REST (OpenAPI), GraphQL (SDL/introspection), gRPC (Proto/descriptor), AsyncAPI (event-driven specs), and WebSocket (channel/message contracts).

When a user asks to generate or update API contracts from planning notes, you MUST run the appropriate pipeline flow. Do not generate ad-hoc API files without running the flow.

Required behavior:

1. Treat planning notes as source input artifact.
1. Generate the contract from notes using pipeline scripts.
1. For REST-only changes, run the API-first flow (`scripts/run_api_first_flow.py`).
1. For multi-protocol changes, run the multi-protocol contract flow (`scripts/run_multi_protocol_contract_flow.py --runtime-config docsops/config/client_runtime.yml --reports-dir reports`).
1. Run full checks per protocol (contract validation, lint stack, regression, docs generation, quality gates, test assets generation with smart merge, optional TestRail/Zephyr upload).
1. Report results and produced artifact paths.
1. After any contract change, regenerate test assets (`scripts/generate_protocol_test_assets.py`) and check `needs_review_ids` in merge output for stale custom cases.

Hard rules:

- If request intent is `generate OpenAPI`, `API-first`, or `planning notes -> spec`, always use pipeline entry points (`scripts/run_api_first_flow.py` and related scripts), not freeform one-off generation.
- If the request involves GraphQL, gRPC, AsyncAPI, or WebSocket contracts, use the multi-protocol pipeline entry point (`scripts/run_multi_protocol_contract_flow.py`).
- Protocol-specific validators: REST (`scripts/validate_openapi_contract.py`), GraphQL (`scripts/validate_graphql_contract.py`), gRPC (`scripts/validate_proto_contract.py`), AsyncAPI (`scripts/validate_asyncapi_contract.py`), WebSocket (`scripts/validate_websocket_contract.py`).
- After generating or updating any document, run the knowledge module pipeline (extract, validate, rebuild index). See "Knowledge module pipeline (RAG preparation)" section below.

## Stripe-level documentation quality principles

**Quality bar requirement:** every generated document must be equal to or better than Stripe documentation quality (clarity, structure, accuracy, examples, and usability).

### Write for humans first, search engines second

**Every document MUST:**

1. **Start with the user's goal** - What are they trying to achieve?
1. **Provide working code immediately** - Show, don't tell
1. **Explain the why, not just the how** - Context matters
1. **Include realistic examples** - Not "foo/bar" but actual use cases
1. **Anticipate next steps** - What will they need after this?

### The Stripe documentation formula

**Opening paragraph (The Hook):**

- State what the feature/API does in one sentence
- Explain the primary use case
- Set expectations for what they'll learn

**Immediate value (The Code):**

```javascript
// Show a complete, working example within first 100 words
const result = await stripe.charges.create({
  amount: 2000,
  currency: 'usd',
  source: 'tok_visa',
  description: 'My First Test Charge (created for API docs)',
});
```

**Progressive disclosure:**

1. Simple case first (80% of users)
1. Common variations (15% of users)
1. Advanced scenarios (5% of users)

### Quality checklist for every document

**Before saving ANY document, verify:**

- [ ] **First paragraph hooks the reader** - Would YOU keep reading?
- [ ] **Code example in first 200 words** - Can they copy-paste and run?
- [ ] **Every code block is complete** - No placeholder text or partial examples
- [ ] **Examples use realistic data** - Real product names, not "test123"
- [ ] **Error cases are covered** - What could go wrong? How to fix?
- [ ] **Performance is mentioned** - Rate limits? Timeouts? Best practices?
- [ ] **Security is addressed** - Authentication? Permissions? Validation?
- [ ] **Links to next steps** - Where do they go after success?

### Writing tone and style

**DO write like this:**

- "To process payments, create a charge object with the amount and currency."
- "Authentication fails if the API key is invalid. Check your key in the dashboard."
- "This endpoint returns up to 100 results. Use pagination for larger datasets."

**DON'T write like this:**

- "You might want to consider possibly creating a charge object."
- "It should be noted that authentication may fail."
- "Handle large result sets in several ways."

### Code examples that teach

**Bad example:**

```javascript
// Process payment
processPayment(amount, currency);
```

**Stripe-quality example:**

```javascript
// Process a $20.00 payment in USD
// Returns a charge object with status 'succeeded' or throws an error
try {
  const charge = await stripe.charges.create({
    amount: 2000,        // Amount in cents ($20.00)
    currency: 'usd',
    source: 'tok_visa',  // Token from Stripe.js or Elements
    description: 'Order #1234 - Blue T-Shirt (Size: M)',
    metadata: {
      order_id: '1234',
      customer_email: 'customer@example.com'
    }
  });

  console.log('Payment successful:', charge.id);
  // Save charge.id to your database for refunds/disputes
} catch (error) {
  console.error('Payment failed:', error.message);
  // Common errors: card_declined, insufficient_funds, expired_card
}
```

**IMPORTANT:** this pipeline includes comprehensive SEO/GEO optimization with 24 automated checks. All content MUST pass:

- GEO linting (LLM/AI optimization)
- SEO metadata validation
- Structured data requirements
- Search ranking optimization

## Critical rules

### Use templates and snippets when available

**When creating documentation, ensure consistency:**

1. **Check for relevant templates in `templates/` directory:**

- If a matching template exists, use it as base
- Copy it: `cp templates/[template] docs/[section]/[new-file].md`
- Edit content while keeping structure

1. **OR use VS Code snippets from `.vscode/docs.code-snippets`:**

- Type snippet prefix (doc-tutorial, doc-howto, etc.) and press Tab
- Ensures consistent structure across documentation

1. **If no template matches, create one first:**

- Create a new Stripe-quality template with formatting consistent with existing templates in `templates/`
- Save the template to the `templates/` directory with a descriptive name
- Then use the saved template to create the actual document

1. **ALWAYS update `mkdocs.yml` navigation:**

- Add new document to appropriate section in nav
- Use descriptive titles, maintain logical order
- Claude should ALWAYS update mkdocs.yml when adding docs

**Why this matters:** templates and snippets ensure:

- Consistent structure and formatting
- All required sections include necessary content
- Frontmatter is complete and valid
- SEO/GEO optimization rules receive proper attention
- Navigation stays properly maintained

## Original critical rules

### Frontmatter requirements

Every `.md` file in `docs/` MUST have valid frontmatter:

```yaml
---
title: "Descriptive title under 70 characters"
description: "Description between 50-160 characters for SEO. Include key terms."
content_type: tutorial|how-to|concept|reference|troubleshooting|release-note
product: both|cloud|self-hosted
tags:

  - Tag1
  - Tag2

---

```

**Validation rules:**

- `title`: Required, max 70 characters
- `description`: Required, 50-160 characters
- `content_type`: Required, must be one of the allowed values
- `product`: Optional but recommended
- `tags`: Optional, max 8 tags
- `status`: Optional - `active` (default), `deprecated`, `removed`
- `deprecated_since`: Required if status is `deprecated` (for example, "2024-01-15")
- `removal_date`: Required if status is `removed` (for example, "2024-06-01")
- `replacement_url`: Required if deprecated/removed - link to new documentation

**Handling deprecated and removed content:**

For deprecated documents:

```yaml
---
title: "Old API Endpoint (Deprecated)"
description: "This endpoint is deprecated. Use the new /v2/endpoint instead."
status: deprecated
deprecated_since: "2024-01-15"
replacement_url: "/reference/api-v2-endpoint"
---

!!! warning "Deprecated"
    This feature is deprecated since January 15, 2024.
    Please use [new endpoint](/reference/api-v2-endpoint) instead.
```

For removed documents:

```yaml
---
title: "Removed Feature"
description: "This feature has been removed. See migration guide."
status: removed
removal_date: "2024-06-01"
replacement_url: "/migration/feature-migration"
noindex: true  # Prevents search engine indexing
---
```

### GEO optimization for LLM and AI search

**First paragraph rules:**

- Keep under 60 words
- Include a clear definition using "is," "enables," "provides," "allows"
- Answer the implied question directly

**Example:**

```markdown
## Webhook node reference

The Webhook node is a trigger that starts workflows when it receives HTTP requests. It supports GET, POST, PUT, PATCH, DELETE methods and provides built-in authentication options.

```

**Heading rules:**

- Use descriptive headings, NOT generic ones
- BAD: "Overview," "Configuration," "Setup"
- GOOD: "Configure HMAC authentication," "Set up webhook endpoints"

**Fact density:**

- Include concrete facts every 200 words (numbers, code, config values)
- Tables and code blocks count as facts
- Examples: port numbers (8080), timeout values (30 seconds), version numbers (1.2.3)

### Document types using Diátaxis framework

Use these templates based on `content_type`:

| Type | Purpose | Template |
| ------ | --------- | ---------- |
| `tutorial` | Learning-oriented, step-by-step | `doc-tutorial` snippet |
| `how-to` | Task-oriented, specific goals | `doc-howto` snippet |
| `concept` | Understanding-oriented, explanations | `doc-concept` snippet |
| `reference` | Information-oriented, precise specs | `doc-reference` snippet |
| `troubleshooting` | Problem → cause → solution | `doc-troubleshoot` snippet |
| `release-note` | Version changes | `doc-release` snippet |

### Style rules enforced by Vale

**CRITICAL: All documentation MUST pass Vale style checks on first write.**

**Vale Configuration:**

- **American English** - Use American spelling only
- **Style guide** - Primary style guide is configured per project (Google Developer Style Guide or Microsoft Style Guide). Check `.vale.ini` for the active style package.
- **write-good** - Clear, concise writing rules

**Specific Vale Rules to Follow:**

**American English:**

- Use American spelling: "color," "optimize," "analyze," "center"
- NOT British spelling variants
- Use "license" (verb and noun)
- Use "canceled" instead of British spelling

**Google Style Guide Requirements** (when Google is the active style):

- **Acronyms**: Write out on first use: "Application Programming Interface (API)"
- **Contractions**: Avoid them. Use "do not" instead of "don't"
- **Numbers**: Spell out one through nine, use numerals for 10 and above
- **Oxford comma**: Always use it: "red, white, and blue"
- **Headings**: Use sentence case, not Title Case
- **Lists**: Use parallel structure (all items start with same part of speech)

**Microsoft Style Guide Requirements** (when Microsoft is the active style):

- **Acronyms**: Spell out on first mention, then use the acronym: "representational state transfer (REST)"
- **Contractions**: Use them for a conversational tone: "don't," "isn't," "you'll"
- **Numbers**: Use numerals for all numbers, including 1-9
- **Oxford comma**: Always use it
- **Headings**: Use sentence case
- **Bias-free language**: Use gender-neutral terms ("they" instead of "he/she")
- **Active voice**: Required ("Select the menu" not "The menu is selected")

**write-good Rules:**

- **Avoid weasel words**: "many," "various," "extremely," "fairly"
- **No passive voice**: "Configure the setting" NOT "The setting requires configuration"
- **Avoid adverbs**: Be specific instead of using vague adverbs
- **No clichés**: Avoid overused phrases
- **Be specific**: "in 5 seconds" not "quickly"

**DO:**

- Use active voice: "Configure the webhook"
- Use second person: "you" not "the user"
- Use present tense: "This node sends"
- Be direct: "Click Save" not "Please click the Save button"
- Be specific: "Processing takes 2-3 seconds" not "Processing is fast"

**DON'T:**

- Use "simple," "easy," "just" (condescending weasel words)
- Use subjective terms without evidence
- Use passive voice unless necessary
- Use future tense for current features
- Use hedge words: Be precise instead of vague
- Start sentences with wordy constructions

### Markdown formatting

**Code blocks:**

- Always specify language: `javascript`, `bash`, `yaml`
- Use fenced blocks (```) not indented blocks

**Admonitions (MkDocs Material):**

```markdown
!!! info "Title"
    Content here.

!!! warning "Important"
    Warning content.

!!! tip "Pro tip"
    Helpful hint.

```

**Content tabs** (tab names are project-specific, defined in project configuration):

```markdown
=== "Tab A"

    Content for variant A

=== "Tab B"

    Content for variant B

```

Use content tabs when readers need to choose between mutually exclusive variants (deployment modes, operating systems, programming languages, plan tiers). Tab names must match the project's configured variants.

### Allowed tags

Tags are project-specific. Check the `tags` section in `mkdocs.yml` for the list of allowed tags for the current project. Every tag you use in a document's frontmatter MUST exist in that list.

Standard content-type tags available in all projects:

- Tutorial, How-To, Concept, Reference, Troubleshooting

Domain-specific tags (vary by project, check `mkdocs.yml`):

- Examples: API, Architecture, Operations, Quality, Deployment, Security, Webhook, GraphQL, gRPC, AsyncAPI, WebSocket

### File naming

- Use kebab-case: `configure-webhook-trigger.md`
- Be descriptive: `webhook-not-firing.md` not `issue-1.md`
- Match the title (slugified)

## Variables system

**All common values MUST reside in `docs/_variables.yml` and documentation must reference them.**

### Why use variables

- **Single source of truth** - Update once, changes everywhere
- **Consistency** - Same values across all docs
- **Easy updates** - Change port from 5678 to 8080 in one place
- **Product agnostic** - Easy to rebrand for different companies

### How to use variables

```markdown
The default port is {{ default_port }}.
Visit [{{ product_name }} Cloud]({{ cloud_url }}).
Configure {{ product_name }} using environment variable {{ env_vars.port }}.
```

### Available variables in `_variables.yml`

This is a snapshot example. Any project-specific variables can be added to `_variables.yml` as needed. The list below is not restrictive; it shows common categories.

```yaml
# Product info
product_name: "ProductName"
product_full_name: "Product workflow automation"

# Versions
current_version: "1.50.0"
api_version: "v1"

# URLs
cloud_url: "https://app.example.com"
docs_url: "https://docs.example.com"

# Ports and paths
default_port: 5678
default_data_folder: "~/.product"

# Environment variables
env_vars:
  port: "PRODUCT_PORT"
  webhook_url: "WEBHOOK_URL"

# Limits
max_payload_size_mb: 16
rate_limit_requests_per_minute: 60

# Add any project-specific variables here
```

### Examples of proper usage

**GOOD:**

```markdown
Run {{ product_name }} on port {{ default_port }}
The maximum payload size is {{ max_payload_size_mb }} MB
Set the port using {{ env_vars.port }}
```

**BAD:**

```markdown
Run ProductName on port 5678  # Hardcoded values
The maximum payload size is 16 MB  # Should use variable
Set the port using PRODUCT_PORT  # Should use env_vars.port
```

## Pre-commit checks

Before committing, these checks run automatically in order (8 stages):

1. **Stage 0a: normalize_docs.py** (normalizes whitespace, trailing newlines, UTF-8 encoding)
1. **Stage 0: API contract validation** (REST: Spectral + Redocly + swagger-cli + `validate_openapi_contract.py`; GraphQL: `validate_graphql_contract.py`; gRPC: `validate_proto_contract.py`; AsyncAPI: `validate_asyncapi_contract.py`; WebSocket: `validate_websocket_contract.py`)
1. **Stage 1: Vale** (style - American English, Google/Microsoft Style Guide, write-good)
1. **Stage 2: markdownlint** (Markdown formatting)
1. **Stage 3: cspell** (spelling)
1. **Stage 4: validate_frontmatter.py** (YAML frontmatter metadata)
1. **Stage 5: seo_geo_optimizer.py** (comprehensive SEO/GEO optimization)
1. **Stage 6: validate_knowledge_modules.py** (knowledge-retrieval module structure)

**All stages block commits on failure. Write correctly the first time.**

- ALL Vale errors and warnings block commits
- Write correctly the first time to avoid iterations
- Check Vale output carefully: it shows exactly what needs fixing

To run manually:

```bash
# Run all checks at once
npm run lint

# Individual checks
vale docs/path/to/file.md
markdownlint docs/path/to/file.md
npx cspell docs/path/to/file.md
python3 scripts/validate_frontmatter.py
python3 scripts/seo_geo_optimizer.py docs/
python3 scripts/seo_geo_optimizer.py docs/ --fix
python3 scripts/validate_knowledge_modules.py
python3 scripts/normalize_docs.py docs/
python3 scripts/validate_openapi_contract.py docs/assets/protocols/rest/openapi.yaml
```

## Creating new documents

### When to create a new document vs update an existing one

- **Create new** when: a new feature/API/concept has no existing doc; a new content type is needed (for example, tutorial for a feature that only has a reference page); a new version requires a separate migration guide.
- **Update existing** when: code changes affect behavior already documented; a bug fix changes documented steps; an API endpoint adds new parameters or fields; configuration options change.
- **Rule of thumb:** Search `docs/` for the topic first. If a doc exists and covers the subject, update it. If the subject is new or a different content type is needed, create a new doc from a template.

### Terminology governance (mandatory)

For every document generation/update:

1. Read `glossary.yml` first and use preferred terms.
1. If a term already exists in `glossary.yml`, use that preferred term exactly and do not replace it with a synonym.
1. If you introduce a new project term, add marker in the document:
   `<!-- glossary:add: Term | Description | alias-one, alias-two -->`
1. Run:
   `python3 scripts/sync_project_glossary.py --paths docs --glossary glossary.yml --report reports/glossary_sync_report.json --write`
1. Keep marker descriptions concrete and product-specific.

### Use templates and snippets for consistency

**ALWAYS use existing templates and snippets when creating new documentation:**

1. **Check for existing templates first:**

   ```bash
   ls templates/

```bash

   Available templates:

   - `tutorial.md` - Step-by-step learning guides
   - `how-to.md` - Task-oriented guides
   - `concept.md` - Explanations and understanding
   - `reference.md` - Technical specifications
   - `troubleshooting.md` - Problem-solving guides
   - `quickstart.md` - Getting started quickly
   - `api-reference.md` - API documentation
   - `api-endpoint.md` - Single API endpoint reference
   - `webhooks-guide.md` - Webhook-specific docs
   - `admin-guide.md` - Administration guides
   - `architecture-overview.md` - Architecture documentation
   - `authentication-guide.md` - Auth flow documentation
   - `best-practices.md` - Best practices guides
   - `changelog.md` - Changelog entries
   - `configuration-guide.md` - Configuration how-to
   - `configuration-reference.md` - Configuration reference
   - `deployment-guide.md` - Deployment instructions
   - `error-handling-guide.md` - Error handling docs
   - `faq.md` - FAQ pages
   - `glossary-page.md` - Glossary page
   - `integration-guide.md` - Integration guides
   - `migration-guide.md` - Migration guides
   - `plg-persona-guide.md` - PLG persona guide
   - `plg-value-page.md` - PLG value page
   - `release-note.md` - Release notes
   - `sdk-reference.md` - SDK reference docs
   - `security-guide.md` - Security documentation
   - `testing-guide.md` - Testing guides
   - `upgrade-guide.md` - Upgrade instructions
   - `use-case.md` - Use case documentation
   - `user-guide.md` - End-user guides
   - `interactive-diagram.html` - Interactive diagram template
   - `protocols/` - Protocol-specific templates (AsyncAPI, GraphQL, gRPC, WebSocket)
   - `legal/` - Legal templates (LICENSE-COMMERCIAL, NOTICE)

1. **Copy the most relevant template:**

   ```bash
   # Example: Creating a new webhook how-to guide
   cp templates/webhooks-guide.md docs/how-to/your-new-webhook-guide.md

```

1. **OR use VS Code snippets (preferred for consistency):**

- Type the snippet prefix and press Tab
- Available snippets: see the full list in [Snippet prefixes for VS Code](#snippet-prefixes-for-vs-code) below. Common ones:
  - `doc-tutorial` - Full tutorial with all sections
  - `doc-howto` - How-to guide structure
  - `doc-concept` - Concept explanation
  - `doc-reference` - Reference documentation
  - `trouble-guide` - Troubleshooting guide
  - `api-endpoint` - API endpoint block
  - `doc-webhooks` - Webhooks guide
  - `doc-config-guide` - Configuration guide
  - `stripe-perf`, `stripe-errors` - Quick Stripe-style blocks

1. **Determine the correct location:**

- `docs/getting-started/` - Tutorials and quickstarts
- `docs/how-to/` - Step-by-step task guides
- `docs/concepts/` - Understanding and theory
- `docs/reference/` - API, configuration, specifications
- `docs/reference/nodes/` - Node-specific reference
- `docs/troubleshooting/` - Problem resolution
- `docs/` - Top-level pages (index, tags, etc.)

1. **Update navigation in mkdocs.yml:**

   ```yaml
   nav:

     - Getting Started:
       - getting-started/index.md
       - "Your New Tutorial": getting-started/your-new-tutorial.md  # Add here

```text

   **Rules for nav updates:**

   - Add new documents in the appropriate section
   - Use descriptive titles (not just filenames)
   - Maintain alphabetical or logical order within sections
   - For multi-level navigation, create subsections:

     ```yaml

     - Reference:
       - reference/index.md
       - Nodes:
         - Webhook node: reference/nodes/webhook.md
         - HTTP node: reference/nodes/http.md  # New node

```

1. **File naming conventions:**

- Use kebab-case: `configure-webhook-trigger.md`
- Be descriptive: `webhook-hmac-authentication.md` not `auth.md`
- Match the title (slugified)

1. **Content requirements:**

- Fill in all required frontmatter fields
- Keep first paragraph under 60 words
- Include concrete examples and code
- Follow GEO and style rules

1. **Use variables from `_variables.yml`:**

- Never hardcode product names, URLs, ports, versions, or limits
- Use `{{ variable_name }}` syntax (MkDocs macros plugin)
- If a value might change across deployments, add it to `_variables.yml`

1. **Self-verification before saving:**

- Run `vale` on the file and fix all errors/warnings
- Run `markdownlint` and fix formatting issues
- Check frontmatter against `docs-schema.yml`
- Verify all links point to existing files
- Confirm code examples are complete and runnable
- Check for hardcoded values that should use variables

1. **RAG preparation (knowledge module pipeline):**

- Ensure the document has a clear, descriptive `title` and `description` in frontmatter -- these become the module's `title` and `summary` fields
- Use semantic headings (H2/H3) that describe the content (not generic like "Overview") -- headings drive chunking boundaries
- Keep sections focused on a single topic -- the extractor chunks at ~1400 characters per section, splitting on H2/H3 headers first, then paragraphs
- Add `tags` in frontmatter for discoverability -- tags propagate to the knowledge module and are used for retrieval filtering
- Set `content_type` correctly -- it drives automatic intent inference (`tutorial/how-to` -> `configure`, `troubleshooting` -> `troubleshoot`, `reference/concept` -> `integrate`)
- Run the full knowledge pipeline after document changes:

   ```bash
   # 1. Extract modules from docs (auto-chunks, infers intents/audiences)
   python3 scripts/extract_knowledge_modules_from_docs.py \
     --docs-dir docs --modules-dir knowledge_modules \
     --report reports/knowledge_auto_extract_report.json

   # 2. Validate module schema (required fields, no duplicate IDs, no circular deps)
   python3 scripts/validate_knowledge_modules.py

   # 3. Rebuild retrieval index (JSON records for Algolia + FAISS)
   python3 scripts/generate_knowledge_retrieval_index.py
   ```

1. **Validate before committing:**

   ```bash
   # Run all checks
   npm run lint

   # Or individual checks
   python3 scripts/validate_frontmatter.py
   python3 scripts/seo_geo_optimizer.py docs/your-new-file.md
   python3 scripts/validate_knowledge_modules.py

```bash

### Template Selection Guide

| If you're documenting this | Use this template | Location | Snippet |
| --- | --- | --- | --- |
| First-time setup | `quickstart.md` | `docs/getting-started/` | `doc-tutorial` |
| Step-by-step learning | `tutorial.md` | `docs/getting-started/` | `doc-tutorial` |
| Specific task | `how-to.md` | `docs/how-to/` | `doc-howto` |
| Architecture/theory | `concept.md` | `docs/concepts/` | `doc-concept` |
| API endpoints | `api-reference.md` | `docs/reference/` | `doc-reference` |
| Single endpoint | `api-endpoint.md` | `docs/reference/` | `api-endpoint` |
| Node details | `reference.md` | `docs/reference/nodes/` | `doc-reference` |
| Webhook features | `webhooks-guide.md` | Appropriate section | `doc-webhooks` |
| Authentication | `authentication-guide.md` | `docs/how-to/` | `doc-auth` |
| Configuration how-to | `configuration-guide.md` | `docs/how-to/` | `doc-config-guide` |
| Configuration ref | `configuration-reference.md` | `docs/reference/` | `doc-config-ref` |
| Deployment | `deployment-guide.md` | `docs/how-to/` | `deploy-guide` |
| Error handling | `error-handling-guide.md` | `docs/reference/` | `doc-error-guide` |
| Integration guide | `integration-guide.md` | `docs/how-to/` | `doc-integration-guide` |
| Migration | `migration-guide.md` | `docs/how-to/` | `doc-howto` |
| SDK reference | `sdk-reference.md` | `docs/reference/` | `doc-sdk-ref` |
| Security | `security-guide.md` | `docs/reference/` | `doc-security-guide` |
| Testing | `testing-guide.md` | `docs/how-to/` | `doc-testing-guide` |
| FAQ | `faq.md` | `docs/` | `doc-faq` |
| Glossary | `glossary-page.md` | `docs/` | `doc-glossary` |
| Use cases | `use-case.md` | `docs/concepts/` | `doc-usecase` |
| Common problems | `troubleshooting.md` | `docs/troubleshooting/` | `trouble-guide` |
| Version changes | `release-note.md` | `docs/releases/` | `doc-changelog` |
| Upgrade steps | `upgrade-guide.md` | `docs/how-to/` | `doc-howto` |
| Admin guide | `admin-guide.md` | `docs/how-to/` | `doc-howto` |
| Best practices | `best-practices.md` | `docs/concepts/` | `doc-concept` |

### Navigation Update Checklist

When adding a new document:

- [ ] Place file in correct directory based on content type
- [ ] Update `mkdocs.yml` nav section
- [ ] Use descriptive title in nav (not just filename)
- [ ] Maintain logical order (alphabetical or by importance)
- [ ] Test navigation locally: `mkdocs serve`
- [ ] Verify all links work
- [ ] Check that page appears in correct section

### Automated Navigation Management

**How Claude should handle document placement:**

1. **Automatic location selection based on content_type:**

```text
   content_type: tutorial → docs/getting-started/
   content_type: how-to → docs/how-to/
   content_type: concept → docs/concepts/
   content_type: reference → docs/reference/
   content_type: troubleshooting → docs/troubleshooting/

```

1. **Automatic mkdocs.yml update - Claude MUST:**

- Read current mkdocs.yml structure
- Find the appropriate nav section based on content_type
- Add the new document with a descriptive title
- Maintain logical ordering (alphabetical or by complexity)
- Example commit message: "Add webhook authentication guide to how-to section"

1. **Smart placement logic Claude should follow:**

   ```yaml
   # If adding a new webhook how-to:

1. File goes in: docs/how-to/configure-webhook-auth.md
1. Update mkdocs.yml nav section "How-To Guides"
1. Place alphabetically or after related webhook docs
1. Use descriptive title: "Configure webhook authentication"

```yaml

1. **GitHub Actions will verify:**
   - No orphaned pages (files not in nav)
   - Proper categorization
   - Creates issues if navigation needs fixing

1. **Example nav update:**

   ```yaml
   # When adding a new webhook authentication guide:
   nav:

     - How-To Guides:
       - how-to/index.md
       - Configure Webhook triggers: how-to/configure-webhook-trigger.md
       - Authenticate Webhook requests: how-to/authenticate-webhooks.md  # NEW

```

## Quick reference

### Snippet prefixes for VS Code

**Document templates:**

- `doc-tutorial` - Full tutorial template
- `doc-howto` - How-to guide template
- `doc-concept` - Concept explanation template
- `doc-reference` - Reference page template
- `doc-webhooks` - Webhooks guide template
- `doc-auth` - Authentication guide template
- `doc-changelog` - Changelog template
- `doc-config-guide` - Configuration guide template
- `doc-config-ref` - Configuration reference template
- `doc-error-guide` - Error handling guide template
- `doc-faq` - FAQ template
- `doc-glossary` - Glossary page template
- `doc-integration-guide` - Integration guide template
- `doc-sdk-ref` - SDK reference template
- `doc-security-guide` - Security guide template
- `doc-testing-guide` - Testing guide template
- `doc-usecase` - Use case template
- `doc-hook` - Doc hook template
- `doc-quality` - Quality checklist template

**API snippets:**

- `api-endpoint` - API endpoint block
- `api-error` - API error block
- `api-auth` - API authentication block
- `api-pagination` - API pagination block
- `api-webhook` - API webhook block
- `api-ratelimit` - API rate limit block

**Troubleshooting:**

- `trouble-guide` - Troubleshooting guide template
- `trouble-error` - Error troubleshooting block

**Quick inserts:**

- `stripe-perf` - Performance metrics block
- `stripe-errors` - Error handling block
- `stripe-config` - Configuration block
- `stripe-metric` - Single metric block

**Architecture and deployment:**

- `deploy-guide` - Deployment guide block
- `arch-diagram` - Architecture diagram block
- `monitor-dash` - Monitoring dashboard block
- `sdk-example` - SDK example block

**Comparison and decision:**

- `code-output` - Code with output block
- `perf-compare` - Performance comparison block
- `decision-matrix` - Decision matrix table

### Config files

- `.vale.ini` - Vale style linting configuration (selects Google or Microsoft style guide)
- `.markdownlint.yml` - Markdown formatting rules
- `.spectral.yml` - OpenAPI/AsyncAPI contract linting rules (Spectral)
- `cspell.json` - Spelling dictionary and word lists
- `docs-schema.yml` - Frontmatter validation schema
- `glossary.yml` - Terminology glossary (preferred terms and aliases)
- `mkdocs.yml` - MkDocs site configuration, navigation, allowed tags

## Important linting rules to follow

### No emoji or special unicode in code

**NEVER use emoji or special Unicode characters in:**

- Python scripts (causes encoding errors on Windows: cp1251 doesn't support them)
- Use plain ASCII: `->` instead of `→`, text instead of emoji
- Documentation can use ✓ and ✗ for checkmarks if needed
- Avoid all other emoji

### Markdown formatting rules

**Blank lines ensure proper rendering:**

- Before and after ALL lists
- Before and after ALL code blocks
- Before and after ALL headings
- This ensures MkDocs renders everything correctly

**Code blocks:**

- ALWAYS specify language: ```python, ```bash, ```yaml
- Use fenced blocks (```), never indented (4 spaces)
- Exception: MkDocs content tabs may use indentation - that's OK

**Lists:**

- Ordered lists: Use `1.` for ALL items (auto-renumbering)

  ```markdown

1. First item
1. Second item
1. Third item

```javascript

- This allows easy reordering without manual renumbering

**Headings:**

- Only ONE H1 (#) per document - this is the main title
- Use proper hierarchy: # → ## → ###, never skip levels
- Headings need blank lines before and after
- Example structure:

  ```markdown
  # Main Title (only one!)

  ## Section

  ### Subsection

  ## Another Section

```

### YAML files

**Multiline strings in YAML workflows:**

- JavaScript template literals: Use `\n` for line breaks, not actual newlines

  ```yaml
  message = `Line 1\nLine 2\nLine 3`  # ✅
  message = `Line 1
  Line 2`  # ❌ Will break YAML parsing

```yaml

- Python in workflows: Use heredoc or external scripts
- Keep inline code simple to avoid YAML parsing issues

### Windows Compatibility

**Avoid Unicode issues:**

- No emoji or special Unicode characters in print statements
- Use plain ASCII text for console output
- This affects Python scripts that might run on Windows

### File Naming

- Always use absolute paths in tools, not relative paths
- Use kebab-case for file names
- Avoid special characters in file names

## CRITICAL Formatting Rules (ALL documents MUST follow)

**Use templates from `templates/` directory - they already follow these rules!**

### Essential Structure Requirements

**EVERY document MUST have:**

- ✅ **Blank line after frontmatter**
- ✅ **Blank lines before AND after ALL headings**
- ✅ **Blank lines before AND after ALL code blocks**
- ✅ **Blank lines before AND after ALL lists**
- ✅ **All ordered lists use `1.` for EVERY item** (auto-renumbers on render)
- ✅ **Code blocks ALWAYS have language specified** (```python, ```bash, etc.)
- ✅ **Only ONE H1 (#)** - must match the title in frontmatter
- ✅ **First paragraph under 60 words** for SEO/GEO optimization

### Template Usage

**ALWAYS use existing templates:**

1. Check `templates/` directory for matching template
1. Copy the template structure exactly
1. Templates are PRE-VALIDATED to pass all checks
1. DO NOT modify the formatting structure

Available templates in `templates/`:

- tutorial.md
- how-to.md
- concept.md
- reference.md
- troubleshooting.md
- api-reference.md
- quickstart.md
- migration-guide.md
- And more templates.

## Claude's Step-by-Step Process for New Documentation

When user asks to create new documentation, Claude MUST follow all steps in this order:

1. **Determine new vs update:**
   - Search `docs/` for existing coverage of the topic
   - If a doc exists and covers the subject, update it instead of creating a new one
   - If the subject is new or a different content type is needed, create a new doc

1. **Identify document type:**
   - Determine content_type (tutorial, how-to, concept, reference, troubleshooting, etc.)
   - This decides template, location, and style rules
   - Documents are always written in English first; translations are done separately after all checks pass

1. **Read glossary:**
   - Read `glossary.yml` and use preferred terms throughout the document
   - If introducing a new term, add a glossary marker: `<!-- glossary:add: Term | Description | aliases -->`

1. **Select template:**
   - Check `templates/` for matching template (see Template Selection Guide)
   - OR use VS Code snippet (doc-tutorial, doc-howto, etc.)
   - NEVER write from scratch when a suitable template exists; if none exists, create a new template in project format first

1. **Copy template to correct location:**
   - Path: `docs/{locale}/{content_type_dir}/{slug}.md` (for `en`, omit locale prefix)
   - Use kebab-case filename matching the title

1. **Read variables:**
   - Load `docs/_variables.yml`
   - Use `{{ variable_name }}` for all product names, URLs, ports, versions, limits
   - Never hardcode values that exist as variables

1. **Fill template with content:**
   - Follow Stripe-quality standards (hook, code, progressive disclosure)
   - Include realistic, complete code examples (not "foo/bar" but actual use cases)
   - Every code block must be complete and runnable
   - Anticipate next steps: what will the user need after this?

1. **Keep first paragraph under 60 words:**
   - Must include a clear definition using "is," "enables," "provides," "allows"
   - Answer the implied question directly
   - For translations, locale-specific limits apply (ru: 80, de: 70) but that is handled during the translation step

1. **Apply GEO optimization:**
   - Descriptive headings, NOT generic (not "Overview," "Configuration," "Setup")
   - Concrete facts every 200 words (numbers, code, config values)
   - Structured data: tables, code blocks, parameter lists
   - Authoritative citations where applicable

1. **Apply SEO optimization:**
   - Title under 70 characters
   - Description 50-160 characters
   - No bare URLs -- use `[text](url)` format
   - Internal links to related docs
   - No dollar signs before commands in code blocks

1. **Follow formatting rules:**
   - Blank lines around headings, lists, and code blocks
   - Only one H1 (from frontmatter title)
   - Code blocks with language tag (```python, ```bash, etc.)
   - No emoji or special Unicode in Python scripts
   - Ordered lists use `1.` for all items
   - No trailing whitespace

1. **Apply style rules:**
   - American English, active voice, no weasel words
   - Follow configured style guide (Google or Microsoft, per `.vale.ini`)
   - Contractions policy per style guide
   - Second person "you," not "the user" or "users"
   - Present tense for current features
   - Oxford comma in lists, sentence case in headings

1. **Set frontmatter:**
   - Fill all required fields (title, description, content_type, product, tags)
   - Tags must be from the project's allowed set (check `mkdocs.yml`)
   - Title under 70 characters, description 50-160 characters

1. **Scan and replace hardcoded values:**
   - Scan entire document for hardcoded product names, URLs, ports, versions, limits, emails
   - Replace each with the corresponding `{{ variable }}` from `_variables.yml`
   - If a variable does not exist yet, add it to `_variables.yml` first, then use it

1. **Self-verify -- execute code blocks (MANDATORY):**
   - Execute every fenced code block tagged `python`, `javascript`, `bash`, `shell`, `typescript`, `curl`, etc.
   - Compare actual output against documented output; if mismatch, replace with actual output
   - Skip non-executable blocks (`yaml`, `json`, `xml`, `text`, `markdown`, `graphql`, etc.)
   - Skip blocks with `# do-not-execute` or that require external services (mark with `<!-- requires: service-name -->`)

1. **Self-verify -- run shell commands (MANDATORY):**
   - Run every documented shell command and verify exit code and output
   - Read-only commands: execute directly
   - Write commands: execute in temp directory
   - Destructive commands: NEVER execute, verify syntax only
   - Commands with placeholders: skip execution, verify syntax

1. **Self-verify -- fact-check assertions (MANDATORY):**
   - Verify every version number, port number, file path, URL, count, limit
   - Cross-reference with `_variables.yml` and source config files
   - If incorrect, replace with verified correct value

1. **Self-verify -- check internal consistency:**
   - No contradictions within the document (for example, port 5678 in one section and 8080 in another)
   - Code and text must agree (if text says "returns a list" but code shows a dict, fix the text)
   - Cross-reference with other docs if this document links to them

1. **Self-verify -- walk through as user:**
   - Read the document as if you are the user following the instructions step by step
   - If any step is unclear, incomplete, or produces unexpected results, fix it

1. **Update mkdocs.yml:**
   - Add to appropriate nav section
   - Use descriptive title (not just filename)
   - Maintain logical order (alphabetical or by complexity)

1. **Validate (all linters):**
   - Run `npm run lint` (runs all 8 pre-commit stages)
   - Ensure Vale, markdownlint, cspell, frontmatter, SEO/GEO, knowledge modules all pass
   - Fix all errors AND warnings
   - If linting fails, fix issues and re-run (max 5 retries)
   - If all 5 retries fail, log the document as blocked and report to user

1. **RAG preparation (full knowledge module pipeline):**
   - Use semantic headings (H2/H3) that describe the content -- these drive chunk boundaries (extractor splits at ~1400 chars on H2/H3 first)
   - Keep sections focused on a single topic for better chunking -- each chunk becomes a separate knowledge module
   - Ensure `tags` in frontmatter aid discoverability -- tags propagate to knowledge modules for retrieval filtering
   - Set `content_type` correctly -- drives intent inference (`tutorial` -> `configure`, `troubleshooting` -> `troubleshoot`)
   - Run the full extraction + validation + index rebuild:

     ```bash
     python3 scripts/extract_knowledge_modules_from_docs.py \
       --docs-dir docs --modules-dir knowledge_modules \
       --report reports/knowledge_auto_extract_report.json
     python3 scripts/validate_knowledge_modules.py
     python3 scripts/generate_knowledge_retrieval_index.py
     ```

1. **Glossary sync:**
   - Run `python3 scripts/sync_project_glossary.py --paths docs --glossary glossary.yml --report reports/glossary_sync_report.json --write`

1. **Translation (only if user requests non-English version):**
   - Translate only AFTER the English version passes all checks
   - Copy to `docs/{locale}/{content_type_dir}/{slug}.md`
   - Merge `docs/{locale}/_variables.yml` if it exists
   - Set i18n frontmatter: `language`, `translation_of`, `source_hash`
   - Apply locale word limits (ru: 80, de: 70)
   - Run translation quality checklist (active voice, weasel words, terminology, spelling)
   - Apply locale-specific Vale rules if configured
   - Re-run all validation steps on the translated document

1. **Log verification summary (MANDATORY):**

   ```text
   Verification summary:
   - Code blocks: N executed, N passed, N fixed
   - Shell commands: N executed, N passed, N fixed
   - Fact-checks: N assertions, N correct, N fixed
   - Variables: N hardcoded values replaced
   - Consistency: [status]
   - Lint: passed on attempt N
   ```

## Pull Request Reviews

### 🔴 CRITICAL: Fix BOTH Errors AND Warnings

**When reviewing pull requests or fixing linting issues, Claude MUST:**

1. **Fix ALL errors (red)** - These block commits and merges
1. **Fix ALL warnings (yellow)** - These indicate quality issues
1. **Not ignore any linting output** - Both errors and warnings need attention

**Why this matters:**
- Warnings today become technical debt tomorrow
- Clean code has zero warnings, not just zero errors
- Warnings often indicate SEO/GEO optimization issues
- Users expect professional quality with no linting issues at all

**Example workflow when reviewing PR:**
```bash
# Run all checks
npm run lint

# If output shows:
# ❌ ERROR: Missing frontmatter
# ⚠️ WARNING: Passive voice detected
# ⚠️ WARNING: Line too long

# Claude MUST fix ALL three issues, not just the error
```

## Automatic validation

**TWO layers of protection ensure quality:**

1. **Pre-commit hooks** (local) - Run automatically before commit
1. **CI/CD checks** (GitHub) - Same checks run on PR/push

Both use IDENTICAL rules, so if it passes locally, it passes in CI.

## Self-verification layer (post-generation quality gate)

**After generating or editing ANY documentation, Claude MUST run a self-verification pass before committing.**

This verification layer catches errors that linting tools cannot detect: wrong code output, broken commands, incorrect facts, and stale assertions. It replaces the need for manual human verification of technical accuracy.

### Why self-verification matters

- Linters check **style and formatting** -- they cannot verify **technical correctness**
- A code example that passes markdownlint can still produce wrong output
- A shell command that looks valid can fail or produce unexpected results
- A claimed "default port 5678" might have changed to 8080 in the latest release
- Self-verification catches these errors **before** human review, reducing review cycles from 5+ rounds to 1-2

### Step 1: Execute all code examples

**For every fenced code block with a language tag, Claude MUST:**

1. **Identify executable blocks** -- blocks tagged `python`, `javascript`, `bash`, `shell`, `typescript`, `ruby`, `go`, `java`, `curl`
1. **Execute each block** in a sandboxed environment (no network calls, no filesystem writes outside temp)
1. **Capture stdout and stderr** from execution
1. **Compare actual output against documented output** (the `<!-- expected-output: ... -->` comment or output block that follows the code block)
1. **If output mismatches:** replace the documented output with the actual output
1. **If execution fails:** fix the code so it runs, or add a comment explaining why it cannot run in isolation (for example, requires API key)

**Execution rules by language:**

| Language | How to execute | Timeout |
| --- | --- | --- |
| `python` | `python3 -c "<code>"` | 30 seconds |
| `javascript` | `node -e "<code>"` | 30 seconds |
| `typescript` | `npx tsx -e "<code>"` | 30 seconds |
| `bash` / `shell` | Execute in sandboxed shell | 30 seconds |
| `curl` | Execute with `--max-time 10` | 15 seconds |
| `ruby` | `ruby -e "<code>"` | 30 seconds |
| `go` | Write to temp file, `go run` | 30 seconds |

**What to skip:**

- Code blocks tagged with `yaml`, `json`, `xml`, `toml`, `ini`, `sql`, `graphql`, `text`, `markdown`, `diff`, `dockerfile` -- these are configuration/data, not executable
- Code blocks containing `# do-not-execute` comment
- Code blocks that require external services (databases, APIs) -- mark these with `<!-- requires: service-name -->`

**Example verification flow:**

```text
BEFORE verification:
    ```python
    print(2 + 2)
    ```
    Output: `5`

AFTER verification:
    ```python
    print(2 + 2)
    ```
    Output: `4`
```

### Step 2: Verify shell commands and their output

**For every bash/shell command documented, Claude MUST:**

1. **Run the command** (with safe substitutions for destructive commands)
1. **Verify the exit code** matches expectations (0 for success)
1. **Compare output** against what the document claims
1. **Fix discrepancies** -- update the documented output to match reality

**Safe execution rules:**

- **Read-only commands** (`ls`, `cat`, `grep`, `find`, `which`, `--version`, `--help`): execute directly
- **Write commands** (`mkdir`, `cp`, `mv`, `rm`): execute in a temp directory
- **Install commands** (`npm install`, `pip install`): execute with `--dry-run` if supported, otherwise skip and note
- **Destructive commands** (`rm -rf`, `drop table`): NEVER execute -- verify syntax only
- **Commands with placeholders** (`<your-api-key>`, `YOUR_TOKEN`): skip execution, verify syntax

### Step 3: Fact-check concrete assertions

**Claude MUST verify every specific claim in the document:**

1. **Version numbers** -- check against actual installed versions or official documentation
1. **Port numbers** -- verify against default configuration files or `_variables.yml`
1. **File paths** -- verify that referenced files and directories exist in the project
1. **URL paths** -- verify that linked documentation pages exist
1. **Configuration values** -- verify against actual config files (`.vale.ini`, `mkdocs.yml`, `package.json`)
1. **CLI flags and options** -- verify with `--help` output
1. **Error messages** -- verify they match actual error output
1. **Numeric claims** -- verify counts ("supports 5 methods" -- count them)

**Fact-check categories:**

| Claim type | How to verify | Example |
| --- | --- | --- |
| Version number | Run `tool --version` | "Node.js 18.x" -> verify with `node --version` |
| Default value | Check config/source | "Default port 5678" -> check `_variables.yml` |
| File exists | Check filesystem | "Edit `config.yml`" -> verify file exists |
| Link works | Check target exists | `[guide](../how-to/setup.md)` -> verify file exists |
| Count claim | Actually count | "Supports 5 auth methods" -> count listed methods |
| CLI flag | Run `--help` | "`--verbose` flag" -> verify in help output |

### Step 4: Replace mismatches with correct values

**When verification finds a discrepancy, Claude MUST:**

1. **Replace the incorrect value** with the verified correct value
1. **Use placeholders** for environment-specific values:

- API keys: `YOUR_API_KEY`
- Tokens: `YOUR_TOKEN`
- User-specific paths: `~/.config/your-app/`
- Domain names: `your-domain.example.com`
- IP addresses: `192.0.2.1` (documentation range per RFC 5737)
1. **Add a comment** if the original value was intentionally approximate (for example, "approximately 100 ms" does not need exact verification)
1. **Log all changes** -- after verification, list what was corrected:

```text
Verification summary:
- Fixed: print(2+2) output changed from "5" to "4"
- Fixed: Default port updated from 5678 to 8080 (per _variables.yml)
- Verified: 12 code blocks executed, 12 passed
- Skipped: 3 blocks (require external API)
- Fact-checked: 8 assertions, 7 correct, 1 fixed
```

### Step 5: Verify internal consistency

**Claude MUST check that the document does not contradict itself:**

1. **Cross-reference within the document** -- if section 1 says "port 5678" and section 3 says "port 8080," flag and fix
1. **Cross-reference with `_variables.yml`** -- all hardcoded values that exist in variables must use the variable
1. **Cross-reference with other docs** -- if this document links to another, verify the linked content is consistent
1. **Verify code and text agree** -- if text says "returns a list" but code shows a dict, fix the text

### Verification checklist (run after every generation)

**Claude, run this checklist AFTER writing the document but BEFORE committing:**

- [ ] **All code blocks execute** without errors (or are marked as non-executable with reason)
- [ ] **All documented outputs match** actual execution results
- [ ] **All shell commands produce** the documented result
- [ ] **All version numbers are current** and verified
- [ ] **All file paths exist** in the project
- [ ] **All internal links resolve** to existing pages
- [ ] **All configuration values match** `_variables.yml` or source files
- [ ] **No self-contradictions** exist within the document
- [ ] **All numeric claims are accurate** (counts, limits, sizes)
- [ ] **All placeholders use standard format** (`YOUR_API_KEY`, not `<api-key>` or `xxx`)

### When to skip verification

**Skip the full verification pass ONLY when:**

- Editing frontmatter only (title, description, tags)
- Fixing typos in prose text (no code or facts changed)
- Updating navigation in `mkdocs.yml` (no content changes)
- Adding admonitions or formatting changes (no technical content)

**NEVER skip verification when:**

- Any code block is added or modified
- Any shell command is added or modified
- Any specific number, version, port, path, or URL is written
- Any "how to" steps are documented

## Quick checklist for new documents

**Claude, VERIFY each point before saving ANY file:**

**Content & Style (Vale):**

- [ ] **American English spelling** (optimize, color, analyze)
- [ ] **Active voice only** (no passive constructions)
- [ ] **No weasel words** (simple, easy, just, many)
- [ ] **Second person "you"** not "the user" or "users"
- [ ] **Present tense** for current features
- [ ] **Specific facts** not vague claims ("2 seconds" not "quickly")
- [ ] **No contractions** (do not, not don't)
- [ ] **Oxford comma** in lists
- [ ] **Sentence case** in headings

**Formatting (Markdown):**

- [ ] **Blank lines present:**
  - Before/after headings
  - Before/after lists
  - Before/after code blocks
- [ ] **Only ONE H1 (#) heading**
- [ ] **Code blocks have language specified** (```python, not just ```)
- [ ] **Ordered lists use `1.` for all items**
- [ ] **No emoji in Python scripts** (plain ASCII only)
- [ ] **No bare URLs** - use [text](url) format

**Metadata & SEO:**

- [ ] **Frontmatter complete** with all required fields
- [ ] **First paragraph under 60 words** for GEO optimization
- [ ] **No dollar signs before commands** in code blocks
- [ ] **Title under 70 characters**
- [ ] **Description 50-160 characters**

## MANDATORY: Template and snippet enforcement

**Claude MUST ALWAYS start from templates/snippets when available. If no suitable template exists, Claude MUST create a new template in project format first, then generate docs from that template.**

### Why this is mandatory

Templates are pre-validated to pass all linters. When you write from scratch, you introduce formatting errors, missing sections, and inconsistent structure. Templates eliminate this entirely.

### Complete template inventory (38 templates)

Before creating ANY document, check `templates/` for a matching template:

| Document type | Template file | VS Code snippet |
| --- | --- | --- |
| Step-by-step learning | `tutorial.md` | `doc-tutorial` |
| Task-oriented guide | `how-to.md` | `doc-howto` |
| Explanation page | `concept.md` | `doc-concept` |
| Technical specification | `reference.md` | `doc-reference` |
| Problem-solution | `troubleshooting.md` | `trouble-guide` |
| Quick onboarding | `quickstart.md` | `doc-tutorial` |
| API endpoint docs | `api-reference.md` | `doc-reference` |
| Single API endpoint | `api-endpoint.md` | `api-endpoint` |
| Auth patterns | `authentication-guide.md` | `doc-auth` |
| Version upgrade | `migration-guide.md` | `doc-howto` |
| Production setup | `deployment-guide.md` | `deploy-guide` |
| Webhook integration | `webhooks-guide.md` | `doc-webhooks` |
| SDK client library | `sdk-reference.md` | `doc-sdk-ref` |
| Security policy | `security-guide.md` | `doc-security-guide` |
| Config setup | `configuration-guide.md` | `doc-config-guide` |
| Config options table | `configuration-reference.md` | `doc-config-ref` |
| Third-party integration | `integration-guide.md` | `doc-integration-guide` |
| Testing approach | `testing-guide.md` | `doc-testing-guide` |
| Error codes/recovery | `error-handling-guide.md` | `doc-error-guide` |
| System architecture | `architecture-overview.md` | `arch-diagram` |
| Guidelines/patterns | `best-practices.md` | `doc-concept` |
| Business use-case | `use-case.md` | `doc-usecase` |
| Version changelog | `release-note.md` | `doc-changelog` |
| Release notes | `changelog.md` | `doc-changelog` |
| FAQ page | `faq.md` | `doc-faq` |
| Terminology | `glossary-page.md` | `doc-glossary` |
| PLG persona page | `plg-persona-guide.md` | `doc-tutorial` |
| PLG value page | `plg-value-page.md` | `doc-concept` |
| User guide | `user-guide.md` | `doc-howto` |
| Administration guide | `admin-guide.md` | `doc-howto` |
| Upgrade guide | `upgrade-guide.md` | `doc-howto` |
| Interactive diagram | `interactive-diagram.html` | -- |
| GraphQL API reference | `protocols/graphql-reference.md` | `doc-reference` |
| gRPC API reference | `protocols/grpc-reference.md` | `doc-reference` |
| AsyncAPI reference | `protocols/asyncapi-reference.md` | `doc-reference` |
| WebSocket reference | `protocols/websocket-reference.md` | `doc-reference` |
| Protocol snippet pack | `protocols/api-protocol-snippets.md` | -- |
| Commercial license | `legal/LICENSE-COMMERCIAL.template.md` | -- |
| Notice file | `legal/NOTICE.template.md` | -- |

### Template selection process

1. Read the user's request. Identify the document type.
1. Find the matching template from the table above.
1. Copy the template: `cp templates/[template] docs/[section]/[filename].md`
1. Edit the content while preserving the template structure.
1. Do NOT add sections that are not in the template.
1. Do NOT remove required sections from the template.

## MANDATORY: Shared variables for all factual values

**Every value that could change between companies or product versions MUST be a variable in `docs/_variables.yml`.**

### What MUST be a variable

- Product name, company name, tagline
- All URLs (cloud, docs, API, support, status page)
- All port numbers
- All version numbers
- All environment variable names
- All file paths that are product-specific
- All limits (payload size, rate limits, timeouts, max connections)
- All email addresses
- All branding values (copyright year)

### How to use variables in documents

```markdown
Run {{ product_name }} on port {{ default_port }}.
The maximum payload size is {{ max_payload_size_mb }} MB.
Set the port using the {{ env_vars.port }} environment variable.
Visit [{{ product_name }} Cloud]({{ cloud_url }}).
Current version: {{ current_version }}.
```

### Variable naming rules

- Use snake_case: `product_name`, not `productName`.
- Be descriptive and project-scoped: `acme_api_max_payload_size_mb`, not `payload_size`. In multi-project setups, prefix with the project or service name to avoid ambiguity (for example, `billing_api_rate_limit` vs `auth_api_rate_limit`).
- Include units in the name: `request_timeout_seconds`, `rate_limit_requests_per_minute`.
- Group related variables with YAML nesting: `acme.env_vars.port`, `acme.env_vars.api_key`.
- NEVER use generic names: `port` is bad, `default_port` is better, `acme_webhook_listener_port` is best.

### What to do if a variable does not exist

1. Check `docs/_variables.yml` for the value.
1. If it does not exist, add it with a descriptive name.
1. Use the new variable in the document.
1. Document the new variable with a comment in `_variables.yml`.

### Detection of hardcoded values

After writing a document, scan it for hardcoded values that should be variables:

- Port numbers (5678, 8080, 3000)
- Version numbers (1.0.0, 2.5.0)
- URLs (`https://app.example.com`)
- Product names (if they appear literally instead of as `{{ product_name }}`)
- Email addresses

Replace each with the corresponding variable.

## MANDATORY: Auto-correction during verification

**When self-verification finds an error, Claude MUST fix it immediately, not just report it.**

### Auto-correction workflow

```text
Generate document
      |
      v
Execute all code blocks
      |
      v
Does output match documented output?
  YES -> Move to next block
  NO  -> REPLACE documented output with actual output
      |
      v
Run all shell commands
      |
      v
Does command produce expected result?
  YES -> Move to next command
  NO  -> Fix the command OR update documented result
      |
      v
Fact-check all assertions
      |
      v
Is the assertion correct?
  YES -> Move to next assertion
  NO  -> REPLACE incorrect value with verified correct value
      |
      v
Check for hardcoded values
      |
      v
Is the value in _variables.yml?
  YES -> REPLACE hardcoded value with {{ variable_name }}
  NO  -> ADD variable to _variables.yml, THEN replace
      |
      v
Check internal consistency
      |
      v
Do all sections agree?
  YES -> Document is ready
  NO  -> Fix contradictions, ensure single source of truth
```

### What auto-correction looks like in practice

**Before verification:**

```markdown
Run the server on port 5678.
The API version is v1.
```

**After verification (if _variables.yml says port is 8080 and API version is v2):**

```markdown
Run the server on port {{ default_port }}.
The API version is {{ api_version }}.
```

**Before verification (code output wrong):**

```python
result = 2 + 2
print(result)  # Output: 5
```

**After verification:**

```python
result = 2 + 2
print(result)  # Output: 4
```

### Verification summary format

After every document generation, log a summary:

```text
Verification summary:
- Code blocks: 8 executed, 8 passed, 0 fixed
- Shell commands: 3 executed, 2 passed, 1 fixed (npm install path corrected)
- Fact-checks: 12 assertions, 11 correct, 1 fixed (port 5678 -> {{ default_port }})
- Variables: 4 hardcoded values replaced with variables
- Consistency: No contradictions found
```

## Complete AI documentation generation flow

**This is the full step-by-step process Claude MUST follow for every document. Documents are always written in English first; translations are done separately after all checks pass.**

1. **Determine new vs update:** search `docs/` for existing coverage. Update existing docs when possible; create new only when the subject is new or a different content type is needed.
1. **Identify document type:** determine content_type (tutorial, how-to, concept, reference, troubleshooting, etc.) to decide template, location, and style rules.
1. **Read glossary:** read `glossary.yml` and use preferred terms. If introducing a new term, add marker: `<!-- glossary:add: Term | Description | aliases -->`.
1. **Select matching template** from `templates/` (38 templates available); if none exists, create a new template in project format first.
1. **Copy template** to correct location: `docs/{content_type_dir}/{slug}.md`. Use kebab-case filename matching the title.
1. **Read variables:** load `docs/_variables.yml`. Use `{{ variable_name }}` for all product names, URLs, ports, versions, limits. Never hardcode values that exist as variables.
1. **Fill template** with actual content, following Stripe-quality standards (hook, code, progressive disclosure). Include realistic, complete code examples. Anticipate next steps.
1. **Keep first paragraph under 60 words** with a clear definition using "is," "enables," "provides," "allows." Answer the implied question directly.
1. **Apply GEO optimization:** descriptive headings (not generic), concrete facts every 200 words, structured data (tables, code blocks, parameter lists), authoritative citations.
1. **Apply SEO optimization:** title under 70 characters, description 50-160 characters, no bare URLs, internal links to related docs, no dollar signs before commands.
1. **Format correctly:** blank lines around headings, lists, code blocks. One H1 only. Code blocks with language tag. No emoji in Python scripts. Ordered lists use `1.` for all items. No trailing whitespace.
1. **Apply style rules:** American English, active voice, no weasel words. Follow configured style guide (Google or Microsoft, per `.vale.ini`). Second person "you." Present tense. Oxford comma. Sentence case in headings.
1. **Set frontmatter:** fill all required fields (title, description, content_type, product, tags). Tags from the project's allowed set (check `mkdocs.yml`). Title under 70 characters, description 50-160 characters.
1. **Scan and replace hardcoded values:** scan entire document for hardcoded product names, URLs, ports, versions, limits, emails. Replace with `{{ variable }}`. If variable does not exist, add it to `_variables.yml` first.
1. **Self-verify -- execute code blocks (MANDATORY):** run every executable fenced code block, compare output against documented output, fix mismatches. Skip non-executable blocks (yaml, json, xml, text, etc.) and blocks with `# do-not-execute`.
1. **Self-verify -- run shell commands (MANDATORY):** run every documented command, verify exit code and output. Read-only commands: execute directly. Write commands: temp directory. Destructive commands: verify syntax only.
1. **Self-verify -- fact-check assertions (MANDATORY):** verify every version, port, path, URL, count, limit against `_variables.yml` and source configs. Replace incorrect values.
1. **Self-verify -- check internal consistency:** no contradictions within the document. Code and text must agree. Cross-reference with `_variables.yml` and linked docs.
1. **Self-verify -- walk through as user:** read the document step by step as if following the instructions. Fix anything unclear, incomplete, or producing unexpected results.
1. **Update `mkdocs.yml`** navigation with the new page. Descriptive title, logical order.
1. **Run validation:** `npm run lint` (all 8 pre-commit stages). Fix all errors AND warnings. If linting fails, fix and re-run (max 5 retries). If all retries fail, log as blocked and report to user.
1. **RAG preparation:** semantic headings (H2/H3) drive chunk boundaries (~1400 chars). Keep sections single-topic. Set `content_type` for intent inference. Set `tags` for retrieval filtering. Run full pipeline: `python3 scripts/extract_knowledge_modules_from_docs.py --docs-dir docs --modules-dir knowledge_modules --report reports/knowledge_auto_extract_report.json && python3 scripts/validate_knowledge_modules.py && python3 scripts/generate_knowledge_retrieval_index.py`.
1. **Glossary sync:** run `python3 scripts/sync_project_glossary.py --paths docs --glossary glossary.yml --report reports/glossary_sync_report.json --write`.
1. **Translation (only if user requests non-English version):** translate only AFTER English version passes all checks. Copy to `docs/{locale}/{content_type_dir}/{slug}.md`. Merge locale variables. Set i18n frontmatter (`language`, `translation_of`, `source_hash`). Apply locale word limits (ru: 80, de: 70). Run translation quality checklist. Re-run all validation steps.
1. **Log verification summary (MANDATORY):**

   ```text
   Verification summary:
   - Code blocks: N executed, N passed, N fixed
   - Shell commands: N executed, N passed, N fixed
   - Fact-checks: N assertions, N correct, N fixed
   - Variables: N hardcoded values replaced
   - Consistency: [status]
   - Lint: passed on attempt N
   ```

## i18n: Multi-language documentation

### Configuration

Languages are configured in `i18n.yml` (project root). Layout is folder-based: `docs/en/`, `docs/ru/`, etc.

**Key scripts:**

- `npm run i18n:migrate` -- one-time migration from flat to folder layout
- `npm run i18n:sync` -- check translation freshness -> `reports/i18n_sync_report.json`
- `npm run i18n:translate -- --source en/how-to/guide.md --locale ru` -- translate one file
- `npm run i18n:translate:all -- --locale ru` -- translate all missing
- `npm run i18n:translate:stale -- --locale ru` -- re-translate stale only

### Document creation with locale

```bash
# English (default)
python3 scripts/new_doc.py how-to "Configure webhooks" --locale en

# Russian translation from English source
python3 scripts/new_doc.py how-to "Nastroyka vebkhukov" --locale ru \
  --translate-from en/how-to/configure-webhooks.md
```

### i18n frontmatter fields

Translated documents MUST include these frontmatter fields:

```yaml
---
title: "Translated title"
description: "Translated description (50-200 chars)"
content_type: how-to
language: ru
translation_of: en/how-to/configure-webhooks.md
source_hash: "abc123..."
---
```

- `language`: ISO 639-1 code matching the folder (for example, `ru` for `docs/ru/`)
- `translation_of`: path to the source document relative to `docs/`
- `source_hash`: SHA-256 of the source document body at translation time. When the source document changes and `source_hash` no longer matches, all translations are considered stale and MUST be updated.

### Automatic propagation of changes to translations

**When Claude edits the English (source) document, Claude MUST automatically update all its localized versions:**

1. After saving the English document, find all translations by searching for files with `translation_of` pointing to this document.
1. For each translation: apply the same structural and content changes, keeping the translated language.
1. Update `source_hash` in each translation to the new SHA-256 of the updated English document body.
1. Re-run all validation steps (linting, self-verification) on each updated translation.
1. If a change cannot be auto-applied (for example, new prose that requires human translation), mark the translation as stale by leaving the old `source_hash` and adding a comment: `<!-- i18n:needs-update: [description of change] -->`.

### Locale-aware variables

`docs/_variables.yml` is the base (English defaults). Each locale can override values in `docs/{locale}/_variables.yml`:

```yaml
# docs/ru/_variables.yml (only override what differs)
product_tagline: "Platform avtomatizatsii rabochikh protsessov"
```

Technical values (ports, URLs, versions) stay shared. **All localized documents MUST use `{{ variable }}` syntax, not hardcoded values.** Variables resolve from the locale-specific file first, then fall back to the base `_variables.yml`.

## MANDATORY: Quality enforcement for non-English documentation

**Translations are supported for any language** (configured in `i18n.yml`). Russian and German are used as examples below, but the same rules apply to every target language.

**Vale, write-good, proselint, and cspell do NOT support non-English languages.** For English docs these tools enforce quality automatically. For all other languages, **Claude IS the quality linter.** Claude MUST apply equivalent quality rules manually when writing or reviewing non-English documentation.

### What automated tools check per language

| Check | English (`docs/en/`) | Other locales (`docs/ru/`, etc.) |
| --- | --- | --- |
| Vale: Google style guide | Automated | **Claude enforces manually** |
| Vale: write-good | Automated | **Claude enforces manually** |
| Vale: AmericanEnglish | Automated | N/A (use native spelling) |
| Vale: GEO (structure) | Automated | Automated |
| cspell (spelling) | Automated | **Skipped** (Claude checks) |
| markdownlint (formatting) | Automated | Automated |
| frontmatter validation | Automated | Automated |
| SEO/GEO optimizer | Automated (en rules) | Automated (locale rules) |

### Rules Claude MUST enforce for non-English documentation

**When writing or editing ANY non-English document, Claude MUST apply ALL of the following rules.** These are the same rules that Vale, write-good, and proselint enforce for English, adapted for the target language. Examples below use Russian and German for illustration, but Claude MUST apply equivalent rules for any target language.

**1. Active voice (equivalent of write-good passive voice check):**

- Use active voice in the target language
- Russian: "Nastroyte webhook" (active), NOT "Webhook dolzhen byt' nastroyen" (passive)
- German: "Konfigurieren Sie den Webhook" (active), NOT "Der Webhook muss konfiguriert werden" (passive)
- The subject should perform the action, not receive it

**2. No weasel words (equivalent of write-good weasel word check):**

- Do not use vague qualifiers in any language
- Banned in Russian: "prosto" (just/simple), "legko" (easy), "bystro" (quickly), "mnogo" (many/various), "razlichnye" (various), "nekotorye" (some), "obychno" (usually)
- Banned in German: "einfach" (simple), "schnell" (quickly), "verschiedene" (various), "einige" (some)
- Replace with specific values: "za 5 sekund" not "bystro," "3 metoda" not "neskolko metodov."

**3. Direct, imperative style (equivalent of Google style guide):**

- Use second person "you" equivalent: Russian "vy," German "Sie"
- Use present tense for current features
- Be direct: "Nazhmite Sokhranit'" not "Pozhaluysta, nazhmite knopku Sokhranit'"
- No hedge words: be precise, not vague

**4. No contractions (equivalent of Google style guide):**

- Use full word forms in formal documentation
- This applies in languages where colloquial contractions exist

**5. Specific facts, not vague claims:**

- "Obrabotka zanimaet 2-3 sekundy" not "Obrabotka proiskhodit bystro"
- Include numbers, timeouts, limits in all languages

**6. Correct technical terminology:**

- Use the standard accepted technical terms for the target language
- Do NOT transliterate English terms when a native equivalent is standard
- DO keep English terms when they are the accepted standard in the target language (API, HTTP, JSON, webhook, etc.)
- When in doubt, keep the English technical term

**7. Spelling and grammar:**

- Claude MUST check spelling and grammar in the target language
- cspell cannot do this for non-English, so Claude is the only checker
- Pay attention to: declension, case agreement, verb conjugation
- Russian: check grammatical cases, verb aspects
- German: check compound words, article genders, cases

**8. Consistent terminology within a document:**

- If you translate "workflow" as "rabochiy protsess" in paragraph 1, use the same translation throughout
- Do NOT alternate between translations of the same term
- Create a mental glossary and stick to it

### Quality checklist for non-English documents

**Before saving ANY non-English document, Claude MUST verify:**

- [ ] **Active voice used throughout** (no passive constructions)
- [ ] **No weasel words** (no "prosto," "legko," "bystro" equivalents)
- [ ] **Second person "you"** (vy/Sie, not "polzovatel'" / "der Benutzer")
- [ ] **Present tense** for current features
- [ ] **Specific facts** not vague claims (numbers, timeouts, limits)
- [ ] **Correct spelling and grammar** in the target language
- [ ] **Consistent technical terminology** (same term = same translation)
- [ ] **Code blocks untranslated** (code stays in English)
- [ ] **{{ variables }} preserved** (not translated or modified)
- [ ] **Link paths preserved** (only link text translated)
- [ ] **Frontmatter i18n fields set** (language, translation_of, source_hash)
- [ ] **First paragraph under locale word limit** (60 for en, 80 for ru, 70 for de)
- [ ] **All GEO structural rules pass** (heading hierarchy, fact density)
- [ ] **Formatting correct** (blank lines, one H1, code block languages)

### Self-verification for translations

After generating or editing a non-English document, Claude MUST add a verification note:

```text
Translation quality check:
- Language: [locale]
- Active voice: verified (0 passive constructions found)
- Weasel words: verified (0 found)
- Terminology consistency: verified ([N] terms checked)
- Spelling/grammar: verified
- Code blocks preserved: [N] blocks, all untouched
- Variables preserved: [N] {{ }} placeholders, all intact
- Frontmatter i18n fields: language, translation_of, source_hash set
```

## Consolidated report processing and prioritization

**Claude MUST follow this workflow when the user says "Process reports/consolidated_report.json" or hands over the consolidated report.**

### How the consolidated report is generated

In recommended mode, scheduler runs `docsops/scripts/run_weekly_gap_batch.py` in the client repository and:

1. Runs gap analysis (`doc_gaps_report.json`)
1. Runs KPI wall + SLA evaluation (`kpi-wall.json`, `kpi-sla-report.json`)
1. Runs drift checks (`api_sdk_drift_report.json`)
1. Runs `scripts/consolidate_reports.py` to produce `reports/consolidated_report.json`
1. Auto-extracts knowledge modules from docs (`extract_knowledge_modules_from_docs.py`)
1. Validates modules and rebuilds retrieval index (`validate_knowledge_modules.py`, `generate_knowledge_retrieval_index.py`)
1. Runs any enabled `custom_tasks.weekly`

Compatibility mode: GitHub Actions cron can run equivalent jobs via `.github/workflows/weekly-consolidation.yml` and companion workflows.

On-demand local run is still available: `npm run consolidate`

### What is inside the consolidated report

The consolidated report has this structure:

```json
{
  "generated_at": "ISO timestamp",
  "input_reports": {
    "gaps": { "found": true, "total_gaps": 10 },
    "drift": { "found": true, "status": "ok" },
    "kpi": { "found": true, "quality_score": 82 },
    "sla": { "found": true, "status": "ok", "breaches": [] }
  },
  "health_summary": {
    "quality_score": 82,
    "drift_status": "ok",
    "sla_status": "ok",
    "total_action_items": 12
  },
  "action_items": [
    {
      "id": "CONS-001",
      "source_report": "gaps|drift|kpi|sla",
      "title": "...",
      "category": "authentication|api_drift|stale_doc|sla_breach|...",
      "suggested_doc_type": "how-to|reference|null",
      "priority": "high|medium|low",
      "frequency": 240,
      "action_required": "...",
      "related_files": ["..."],
      "context": { "drift_related": false, "sla_breach_related": false }
    }
  ]
}
```

### Step 1: Read the consolidated report

Read `reports/consolidated_report.json`. This is the ONLY file you need. Do NOT read the 4 individual reports separately.

### Step 2: Check health summary

Before processing action items, check `health_summary`:

- If `sla_status` is `"breach"`, warn the user about SLA violations
- If `drift_status` is `"drift"`, flag that API/SDK docs are out of sync
- Report `quality_score` to the user

### Step 3: Prioritize action items into 3 tiers

Read ALL items from `action_items` array and assign each to a tier:

**Tier 1 - Revenue-critical (process first):**

- Items with `source_report: "drift"` (API/SDK drift detected)
- Items with `source_report: "sla"` (SLA breaches)
- Items with `category` in: `breaking_change`, `api_endpoint`, `authentication`

**Tier 2 - Code-driven (process second):**

- Items with `category` in: `signature_change`, `new_function`, `removed_function`, `webhook`, `config_option`, `env_var`, `cli_command`
- Items with `category: "stale_doc"` (documents not updated in over 90 days)

**Tier 3 - Community and search (process last):**

- Items with `source_report: "gaps"` where `context.source` is `"community"` or `"search"`
- All remaining items not matched by Tier 1 or Tier 2

### Step 4: Sort within each tier

Within each tier, sort items by `frequency` field descending. Items that appear more frequently in user queries or code analysis get processed first.

### Step 5: Process each item in tier order

Process ALL Tier 1 items first, then ALL Tier 2, then ALL Tier 3.

For each item, follow this decision tree:

```text
For each action_item:
      |
      v
Does an existing document cover this topic?
  YES -> UPDATE the existing document (add section, fix drift, refresh content)
  NO  -> Does the topic warrant a full new document?
    YES -> CREATE new document using the correct template from templates/
    NO  -> ADD the information to the most relevant existing document
      |
      v
Select template based on suggested_doc_type:
  tutorial    -> templates/tutorial.md    -> docs/getting-started/
  how-to      -> templates/how-to.md     -> docs/how-to/
  concept     -> templates/concept.md    -> docs/concepts/
  reference   -> templates/reference.md  -> docs/reference/
  troubleshooting -> templates/troubleshooting.md -> docs/troubleshooting/
  quickstart  -> templates/quickstart.md -> docs/getting-started/
  integration-guide -> templates/integration-guide.md -> docs/how-to/
  faq         -> templates/faq.md        -> docs/reference/
```

**Special handling by source_report:**

- `"drift"` items: find the reference doc that covers the changed API/SDK files and update it to match current code
- `"sla"` items: SLA threshold breaches (quality score, stale percentage, gap count). These signal urgency -- prioritize fixing the gaps and stale docs that caused the breach
- `"kpi"` items (stale docs): read the file in `related_files` and assess whether content is outdated. If content needs changes, update it. If content is still accurate, only update `last_reviewed` in frontmatter to today's date. Either way, the file stops being stale after `last_reviewed` is set.
- `"gaps"` items: these are missing content -- create or update docs based on `suggested_doc_type`

### Lifecycle management (deprecated and removed documents)

When processing action items that involve **removed features, deprecated endpoints, or replaced functionality**, Claude MUST update the document lifecycle status:

**For deprecated features:**

1. Set frontmatter: `status: deprecated`, `deprecated_since: "YYYY-MM-DD"`, `replacement_url: "/path/to/new-doc"`
1. Add a warning admonition at the top of the document body:

   ```markdown
   !!! warning "Deprecated"
       This feature is deprecated since [date].
       Use [new feature](/path/to/new-doc) instead.
   ```

1. Do NOT delete the document—users may still reference it

**For removed features:**

1. Set frontmatter: `status: removed`, `removal_date: "YYYY-MM-DD"`, `replacement_url: "/path/to/migration"`, `noindex: true`
1. Replace the document body with a redirect notice:

   ```markdown
   !!! danger "Removed"
       This feature was removed on [date].
       See the [migration guide](/path/to/migration) for alternatives.
   ```

1. The `noindex: true` flag prevents search engines from indexing the page
1. The `lifecycle_manager.py` script automatically adds CSS classes and banners for these states

**When to set lifecycle status:**

- Gap report says `category: "removed_function"` → set `status: removed` on the relevant doc
- Drift report shows an endpoint was deleted from OpenAPI spec → set `status: deprecated` or `status: removed`
- Any action_item mentions deprecation, removal, or replacement → update lifecycle accordingly

### Per-document processing loop

For each document (new or updated):

1. Write or update content following all rules in this file
1. **Run self-verification (MANDATORY before linting):**

- Execute every code block in the document and verify the output matches what is documented. If the output differs, fix the documented output to match reality.
- Run every shell command in the document and verify it succeeds. If a command fails, fix the command or update the documented result.
- Fact-check every concrete assertion: version numbers (run `tool --version`), port numbers (check `docs/_variables.yml`), file paths (verify they exist), internal links (verify target files exist), configuration values (check source configs).
- Replace any mismatched values with verified correct values. Use variables from `docs/_variables.yml` instead of hardcoded values.
- Check internal consistency: if the document says "port 5678" in one section and "port 8080" in another, fix the contradiction.
- Walk through the document as if you are the user following the instructions step by step. If any step is unclear, incomplete, or produces unexpected results, fix it.
1. Run `npm run validate:minimal`
1. If linting fails, fix the issues and re-run (max 5 retries)
1. If all 5 retries fail, log the document as blocked and move to the next item
1. Update `mkdocs.yml` navigation if a new document was created
1. Log a verification summary for this document:

   ```text
   [CONS-001] configure-webhook-auth.md:
   - Code blocks: 3 executed, 3 passed, 0 fixed
   - Shell commands: 2 executed, 2 passed, 0 fixed
   - Fact-checks: 5 assertions, 4 correct, 1 fixed (port 5678 -> {{ default_port }})
   - Variables: 2 hardcoded values replaced
   - Lint: passed on attempt 1
   ```

### After all documents are processed

After processing the entire queue:

1. Stage all created and modified files so the user can review with `git diff --staged`:

   ```bash
   git add docs/ mkdocs.yml
   ```

1. Produce a batch summary:

   ```text
   Consolidated report processing summary:
   - Report: reports/consolidated_report.json
   - Quality score: [N] | Drift: [status] | SLA: [status]
   - Total action items: [N]
   - Tier 1 (revenue-critical): [N] processed, [N] blocked
   - Tier 2 (code-driven): [N] processed, [N] blocked
   - Tier 3 (community/search): [N] processed, [N] blocked
   - Documents created: [N]
   - Documents updated: [N]
   - Lint retries used: [N] total across all documents
   - Blocked items (need manual review): [list with CONS-IDs]
   ```

1. Tell the user to review with:

   ```bash
   git diff --staged       # shows all changes including new files
   git diff --staged --stat  # shows summary of changed files
   ```

## Multi-protocol API documentation workflows

The pipeline supports **five API protocols**, each with its own contract format, validator, reference template, test generator, and sandbox mode:

| Protocol | Contract format | Validator | Reference template | Sandbox fallback |
| --- | --- | --- | --- | --- |
| REST | OpenAPI 3.0.3 YAML | `validate_openapi_contract.py` + Spectral + Redocly | `templates/api-reference.md` | Prism / postman-echo.com |
| GraphQL | SDL (`.graphql`) | `validate_graphql_contract.py` | `templates/protocols/graphql-reference.md` | postman-echo.com/post |
| gRPC | Proto3 (`.proto`) | `validate_proto_contract.py` | `templates/protocols/grpc-reference.md` | postman-echo.com/post |
| AsyncAPI | AsyncAPI YAML | `validate_asyncapi_contract.py` | `templates/protocols/asyncapi-reference.md` | echo.websocket.events |
| WebSocket | Channel YAML | `validate_websocket_contract.py` | `templates/protocols/websocket-reference.md` | echo.websocket.events |

**Protocol aliases** (normalized by `scripts/api_protocols.py`): `"openapi"` -> `"rest"`, `"gql"` -> `"graphql"`, `"proto"` -> `"grpc"`, `"events"` -> `"asyncapi"`, `"ws"` -> `"websocket"`.

### Choosing the right entry point

| Scenario | Entry point | Command |
| --- | --- | --- |
| REST-only, API-first (no code yet) | `run_api_first_flow.py` | `python3 scripts/run_api_first_flow.py --project-slug myapi --spec api/openapi.yaml` |
| REST-only, code-first (code exists) | Manual spec + `run_api_first_flow.py` step 1-5 | Write/update spec, then run validation + docs |
| Any non-REST protocol | `run_multi_protocol_contract_flow.py` | `python3 scripts/run_multi_protocol_contract_flow.py --runtime-config docsops/config/client_runtime.yml --reports-dir reports` |
| Multiple protocols at once | `run_multi_protocol_contract_flow.py` | Add `--protocols graphql,grpc,asyncapi,websocket` |

### Multi-protocol contract flow (all protocols)

**Script:** `scripts/run_multi_protocol_contract_flow.py`

This is the **unified orchestrator** for all protocol documentation. It runs these stages in order:

1. **Contract generation from notes** (optional) -- generates protocol specs from planning markdown
1. **Ingest** -- verifies source contract file exists
1. **Contract validation** -- protocol-specific syntax and semantic checks
1. **Server stub generation** -- creates business-logic placeholder handlers via `scripts/generate_protocol_server_stubs.py`
1. **Lint** -- protocol-specific quality linting
1. **Regression** -- detects breaking changes against the snapshot baseline
1. **Docs generation** -- auto-generates reference documentation from the protocol-specific template
1. **Quality gates** -- semantic lint, frontmatter validation, code snippet linting, self-verification against live/mock endpoints
1. **Test assets generation** -- protocol-aware test cases with smart merge (see below)
1. **Upload test assets** (optional) -- push to TestRail or Zephyr Scale
1. **Publish** -- move generated docs to publication target

**Autofix cycle:** the flow supports up to 3 attempts (configurable `autofix_max_attempts`). On failure, it auto-regenerates docs and retries semantic consistency. Fails fast if `strict_mode` is enabled.

**Non-REST endpoint resolution:** if no endpoint is configured, the flow auto-prepares fallback endpoints per protocol:

- GraphQL: `postman-echo.com/post` (echo for payload inspection)
- gRPC: `postman-echo.com/post` (JSON-over-HTTP gateway)
- AsyncAPI: HTTP publish via `postman-echo.com/post`, WS subscribe via `echo.websocket.events`
- WebSocket: `echo.websocket.events` (public WS echo), HTTP bridge via `postman-echo.com/post`

**Self-verification** (`scripts/run_protocol_self_verify.py`) performs runtime validation against live/mock endpoints: GraphQL introspection, gRPC method invocation, AsyncAPI event publish, WebSocket connection and message routing.

### API-first flow (REST-only)

**Script:** `scripts/run_api_first_flow.py`

Use this when designing a new REST API from scratch (no code exists yet). The OpenAPI spec is the single source of truth.

**5-step execution:**

1. **Generate OpenAPI from planning notes** (optional):

   ```bash
   python3 scripts/run_api_first_flow.py \
     --project-slug myapi \
     --notes notes/api-planning.md \
     --spec api/openapi.yaml \
     --spec-tree api/project \
     --verify-user-path \
     --generate-test-assets
   ```

1. **Validate contract** with Spectral + Redocly + swagger-cli + `validate_openapi_contract.py`
1. **Start mock server** -- the primary sandbox mode is **external (Postman)**, which provisions a shared mock server for Try-it panels in public docs. Docker/Prism modes are fallbacks for local development only.
1. **Publish to docs playground** -- copies spec to `docs/assets/api/`, bundles split specs
1. **Quality checks** -- regression testing, code examples smoke tests, test assets generation

**Sandbox modes for REST (ordered by priority):**

```bash
# PRIMARY: Public external mode (Postman mock server, shared, for Try-it in public docs)
API_SANDBOX_EXTERNAL_BASE_URL="https://sandbox-api.example.com/v1" \
bash scripts/api_sandbox_project.sh up myapi ./api/openapi.yaml 4010 external

# Fallback 1: Docker mode (Prism mock server, local dev only)
bash scripts/api_sandbox_project.sh up myapi ./api/openapi.yaml 4010 docker

# Fallback 2: No-Docker local mode (Prism, local dev only)
bash scripts/api_sandbox_project.sh up myapi ./api/openapi.yaml 4010 prism
```

**Default sandbox selection:** when no mode is specified, the pipeline checks for `API_SANDBOX_EXTERNAL_BASE_URL` environment variable first. If set, it uses `external` mode automatically. Otherwise, it falls back to `docker` or `prism` depending on Docker availability.

### Code-first flow (REST-only)

Use this when the API code already exists. The source code (controllers, routes, models) is the source of truth.

1. **Detect undocumented endpoints:** `npm run gaps:code`
1. **Read source code** -- extract endpoints, schemas, auth, rate limits from controllers
1. **Generate or update the OpenAPI spec** -- create `api/openapi.yaml` with `$ref` pointers to per-resource files under `api/paths/` and shared schemas under `api/components/schemas/`
1. **Apply Stripe-quality descriptions** -- active voice, concrete examples, every parameter has description + example, every response code has description + example body
1. **Validate** -- `npx spectral lint api/openapi.yaml --ruleset .spectral.yml` (must pass with zero errors and zero warnings)
1. **Test against real endpoints** -- send actual HTTP requests, compare against spec, fix discrepancies in the spec
1. **Generate reference docs** -- use `templates/api-reference.md`, run `npm run validate:minimal`, run `npm run build`
1. **Generate test assets** -- `python3 scripts/generate_protocol_test_assets.py --protocols rest --source api/openapi.yaml --output-dir reports/api-test-assets`

**Key difference from API-first:** in code-first you test against real running endpoints, not Prism mocks.

### Contract file organization

**REST (OpenAPI):**

```text
api/
  openapi.yaml                    # Root spec - $ref to paths and components
  paths/
    users.yaml                    # All /users endpoints
    orders.yaml                   # All /orders endpoints
  components/
    schemas/
      User.yaml
      Order.yaml
      Error.yaml
      Pagination.yaml             # Shared cursor/offset pagination envelope
      Money.yaml                  # Currency + amount pair
      Address.yaml                # Postal address
      DateRange.yaml              # start_date / end_date pair
    parameters/
      PageSize.yaml               # ?page_size= query parameter
      PageToken.yaml              # ?page_token= cursor parameter
      SortOrder.yaml              # ?sort= asc|desc parameter
      FieldMask.yaml              # ?fields= sparse fieldset parameter
      IdempotencyKey.yaml         # Idempotency-Key header
      AcceptLanguage.yaml         # Accept-Language header
    responses/
      NotFound.yaml               # 404
      Unauthorized.yaml           # 401
      Forbidden.yaml              # 403
      ValidationError.yaml        # 400
      Conflict.yaml               # 409
      RateLimited.yaml            # 429
      InternalError.yaml          # 500
    headers/
      RateLimit.yaml              # X-RateLimit-Limit, -Remaining, -Reset bundle
      RequestId.yaml              # X-Request-Id trace header
      Pagination.yaml             # Link, X-Total-Count pagination headers
    securitySchemes/
      BearerAuth.yaml             # Bearer JWT token
      ApiKeyAuth.yaml             # X-API-Key header
    examples/
      UserExample.yaml            # Realistic User object example
      ErrorExample.yaml           # Realistic Error object example
```

**Rule:** every reusable element (schemas, parameters, responses, headers, security schemes, examples) MUST live in its own file under `components/` and be referenced via `$ref`. Do not inline shared definitions -- duplication causes drift.

**Non-REST protocols:** place contracts under `docs/assets/protocols/`:

```text
docs/assets/protocols/
  rest/openapi.yaml
  graphql/schema.graphql
  grpc/service.proto
  asyncapi/asyncapi.yaml
  websocket/channels.yaml
```

### Protocol-specific validation

Each protocol has a dedicated validator. Claude MUST run the correct validator before generating docs:

```bash
# REST
python3 scripts/validate_openapi_contract.py api/openapi.yaml

# GraphQL
python3 scripts/validate_graphql_contract.py docs/assets/protocols/graphql/schema.graphql

# gRPC
python3 scripts/validate_proto_contract.py --proto docs/assets/protocols/grpc/service.proto

# AsyncAPI
python3 scripts/validate_asyncapi_contract.py docs/assets/protocols/asyncapi/asyncapi.yaml

# WebSocket
python3 scripts/validate_websocket_contract.py docs/assets/protocols/websocket/channels.yaml
```

### Test assets generation and smart merge

**Script:** `scripts/generate_protocol_test_assets.py`

Generates protocol-aware test cases for all five protocols. Claude MUST run this after any contract change.

```bash
python3 scripts/generate_protocol_test_assets.py \
  --protocols graphql,grpc,asyncapi,websocket \
  --source docs/assets/protocols/graphql/schema.graphql \
  --output-dir reports/api-test-assets
```

**Test case types per protocol:**

| Protocol | Test categories |
| --- | --- |
| GraphQL | Happy path query/mutation/subscription, invalid input, auth policy, injection hardening, latency budget |
| gRPC | Positive unary/streaming, status code semantics, deadline/retry, authorization, latency SLO |
| AsyncAPI | Publish contract validation, invalid payload rejection, ordering/idempotency, security policy, throughput |
| WebSocket | Connection/auth, message envelope validation, reconnect behavior, security, concurrency |
| REST | CRUD happy paths, validation errors, auth, rate limiting, pagination |

**Output formats:**

- `api_test_cases.json` -- full case objects with merge stats
- `testrail_test_cases.csv` -- TestRail upload format
- `zephyr_test_cases.json` -- Zephyr Scale upload format
- `test_matrix.json` -- case matrix for test selection
- `fuzz_scenarios.json` -- payload mutation scenarios

### Smart merge: how tests survive API changes

When the contract changes, the test generator uses **signature-based smart merge** to reconcile new auto-generated cases with existing customized and manual cases.

**Source signature:** SHA-256 hash of the contract source file. Every generated test case carries the `spec_signature` of the contract version it was generated from.

**Merge rules:**

| Existing case state | Signature changed? | Action |
| --- | --- | --- |
| Missing (new endpoint) | n/a | ADD new case |
| Auto-generated, not customized | No | REPLACE with regenerated version |
| Auto-generated, not customized | Yes | REPLACE with regenerated version |
| Customized (`customized: true`) | No | PRESERVE custom version |
| Customized (`customized: true`) | Yes | PRESERVE + mark `needs_review: true` |
| Manual (`origin: "manual"`) | Any | NEVER overwrite, always preserve |

**Merge stats in output:**

```json
{
  "merge_stats": {
    "new": 5,
    "updated": 3,
    "preserved_custom": 2,
    "preserved_manual": 1,
    "stale_custom_needs_review": 1
  },
  "needs_review_ids": ["TC-graphql-mutation-create-auth"],
  "source_signature": "abc123..."
}
```

**Claude MUST after every contract change:**

1. Run `generate_protocol_test_assets.py` to regenerate test cases
1. Check `merge_stats` in the output -- report `stale_custom_needs_review` count to the user
1. If `needs_review_ids` is non-empty, list the case IDs and explain that these custom test cases may need updating because the contract signature changed
1. Never modify cases with `origin: "manual"` -- these are human-authored and must be preserved exactly

### When the API changes: full update checklist

When a user modifies any API contract (adds endpoints, changes schemas, removes operations), Claude MUST execute this sequence:

1. **Update the contract** -- edit the spec/schema/proto file
1. **Validate the contract** -- run the protocol-specific validator (see above)
1. **Check for breaking changes** -- the multi-protocol flow runs regression checks automatically; for manual runs: compare against the previous snapshot in `reports/`
1. **Regenerate reference docs** -- run `scripts/generate_protocol_docs.py` or the full flow
1. **Regenerate test assets** -- run `scripts/generate_protocol_test_assets.py`
1. **Review smart merge output** -- check `needs_review_ids`, report stale custom cases
1. **Update navigation** -- if new endpoints/operations were added, update `mkdocs.yml`
1. **Run self-verification** -- `scripts/run_protocol_self_verify.py` against live/mock endpoints
1. **Run full lint** -- `npm run validate:minimal`

## Interactive diagrams

**When a document describes system architecture, data flow, or multi-component interactions, Claude MUST generate an interactive HTML diagram instead of a static Mermaid block.**

Interactive diagrams have clickable components with description panels. They look professional and provide a better experience than static images or basic Mermaid flowcharts.

### When to create an interactive diagram

This applies to **any document type** (how-to, concept, reference, troubleshooting, tutorial) whenever the content describes something multi-component:

- Architecture overviews (system components, infrastructure layers)
- Data flow diagrams (request lifecycle, event processing pipelines)
- Integration diagrams (how services connect to each other)
- Deployment diagrams (infrastructure topology)
- Troubleshooting: request path through multiple services
- How-to: multi-service setup or configuration
- Reference: API gateway routing, webhook delivery chain
- Concept: microservices communication, queue processing

**Rule: if the content describes 6+ interacting components or multiple layers, create an interactive diagram regardless of document type.** For simple linear flows (3-5 steps), a Mermaid diagram is sufficient.

### How to create an interactive diagram

1. Copy the template: `cp templates/interactive-diagram.html docs/diagrams/[name].html`
1. Edit the HTML structure: add/remove layers and components (the `<!-- EDIT THIS SECTION -->` comments mark editable areas)
1. Edit the `descriptions` object in the `<script>` section. Every component MUST have a rich description that appears in the info panel when the user clicks on it:

- `title`: Component name with context (for example, "PostgreSQL Database" not just "Database")
- `desc`: 2-3 sentences with concrete metrics, specific technologies, and how this component connects to others. Write as if explaining to an engineer who needs to understand the system in 30 seconds.
- `tags`: 3-5 technology tags (frameworks, protocols, key specs)

   **Good description:**

   ```
   "Primary database with 2 read replicas. Handles 8,500 queries/sec
   (peak: 12,000). Uses PgBouncer connection pooling (max 500 connections).
   Automated daily backups with 30-day retention and point-in-time recovery."
   ```

   **Bad description:**

   ```
   "The database stores data."
   ```

1. Each component needs a `data-id` attribute that matches a key in `descriptions`
1. Embed in the Markdown document using iframe (see below)
1. **Immediately after creating/editing the diagram and embedding it, run validation:**

```bash
python3 scripts/validate_diagram_content.py docs/diagrams/[name].html docs/[path-to-md]
```

Fix any errors before proceeding. This checks that data-ids match descriptions, component names and metrics match the document text, and descriptions are not orphaned. Do not skip this step — it catches hallucinated metrics, wrong component counts, and name mismatches between diagram and document.

**Embedding:**

**MkDocs embedding:**

```markdown
<div class="interactive-diagram" markdown>
<iframe src="../diagrams/[name].html"></iframe>
</div>
```

The `docs/stylesheets/diagrams.css` handles responsive sizing and styling automatically.

**Docusaurus embedding (in MDX files):**

```jsx
import InteractiveDiagram from '@site/src/components/InteractiveDiagram';

<InteractiveDiagram src="/diagrams/[name].html" title="System architecture" />
```

### Diagram template structure

The template (`templates/interactive-diagram.html`) has:

- Dark theme with CSS custom properties (easy to rebrand)
- Layers with labeled groups (Clients, Edge, Gateway, Services, Data)
- Clickable components with icon, name, and metric
- Animated arrows between layers
- Info panel that shows title, description, and technology tags on click
- Responsive design (works on mobile)

### Files

| File | Purpose |
| --- | --- |
| `templates/interactive-diagram.html` | Template for new diagrams |
| `docs/diagrams/` | Directory for diagram HTML files |
| `docs/stylesheets/diagrams.css` | CSS for iframe embedding in MkDocs |
| `docusaurus/src/components/InteractiveDiagram.jsx` | React wrapper for Docusaurus |
| `scripts/validate_diagram_content.py` | Post-generation validation (run immediately after creating/editing a diagram) |

## OpenAPI spec quality rules

**Every OpenAPI spec in this project MUST meet Stripe-quality standards. These rules apply to both code-first and API-first workflows.**

### Operation rules

| Field | Rule | Example |
| --- | --- | --- |
| `operationId` | Required, camelCase, unique across spec | `listUsers`, `createOrder` |
| `summary` | Required, imperative mood, under 80 characters | `List all users`, `Create an order` |
| `description` | Required, 2-4 sentences, active voice, present tense | Explains what the endpoint does, when to use it, and what it returns |
| `tags` | Required, one tag per operation, PascalCase resource name | `Users`, `Orders`, `Webhooks` |

### Parameter rules

Every parameter (path, query, header) MUST have:

- `description`: What the parameter does, in active voice
- `example`: A realistic example value (not "string" or "123")
- `required`: Explicitly set to `true` or `false` (do not rely on defaults)

### Schema property rules

Every property in every schema MUST have:

- `description`: What the property represents
- `type`: The data type (`string`, `integer`, `boolean`, `array`, `object`)
- `example`: A realistic example value

Use `$ref` to reference shared schemas. Do not duplicate schema definitions.

### Response rules

Every operation MUST define these response codes where applicable:

| Status code | When to use | Required |
| --- | --- | --- |
| `200` | Successful GET, PUT, PATCH | Yes for those methods |
| `201` | Successful POST (resource created) | Yes for POST |
| `204` | Successful DELETE (no content) | Yes for DELETE |
| `400` | Validation error, malformed request | Yes for all |
| `401` | Missing or invalid authentication | Yes for all authenticated endpoints |
| `403` | Authenticated but not authorized | Yes if authorization differs from authentication |
| `404` | Resource not found | Yes for endpoints with path parameters |
| `409` | Conflict (duplicate resource) | Yes for POST if uniqueness constraints exist |
| `429` | Rate limit exceeded | Yes if rate limiting is enabled |
| `500` | Internal server error | Yes for all |

Every response MUST include an `example` body.

### Polymorphism rules

- Use `discriminator` with `propertyName` to distinguish union types
- Define subtypes using `allOf` with a base schema `$ref`
- Document the discriminator field in the base schema description

### File organization

```text
api/
  openapi.yaml                    # Root spec - $ref to paths and components
  paths/
    users.yaml                    # All /users endpoints
    orders.yaml                   # All /orders endpoints
  components/
    schemas/
      User.yaml                   # User schema
      Order.yaml                  # Order schema
      Error.yaml                  # Shared error schema
    responses/
      NotFound.yaml               # 404 response
      Unauthorized.yaml           # 401 response
      ValidationError.yaml        # 400 response
```

### Spectral lint rules

The `.spectral.yml` configuration extends `spectral:oas` and enforces these 18 rules:

**Inherited rules (from spectral:oas):**

| Rule | Severity | What it checks |
| --- | --- | --- |
| `operation-description` | warn | Every operation has a description |
| `operation-operationId` | error | Every operation has an operationId |
| `operation-tags` | warn | Every operation has at least one tag |
| `info-contact` | warn | The info object has contact information |
| `info-description` | error | The info object has a description |
| `info-license` | off | License information (disabled) |
| `no-eval-in-markdown` | error | No eval() in Markdown descriptions |
| `no-script-tags-in-markdown` | error | No script tags in Markdown descriptions |
| `path-params` | error | Path parameters match path template |
| `typed-enum` | warn | Enum values match the declared type |
| `operation-success-response` | error | Every operation has a success response |
| `path-keys-no-trailing-slash` | error | Paths do not end with a slash |
| `path-not-include-query` | error | Paths do not include query strings |

**Custom rules (project-specific):**

| Rule | Severity | What it checks |
| --- | --- | --- |
| `parameter-description` | error | Every parameter has a description |
| `schema-properties-example` | warn | Schema properties have example values |

**Target: zero errors AND zero warnings.**

## Knowledge module pipeline (RAG preparation)

**Every document change triggers the knowledge module pipeline.** This pipeline extracts intent-driven knowledge modules from docs, validates them, builds retrieval indexes, and optionally runs quality evaluations. Claude MUST understand and execute this pipeline after creating or updating documentation.

### Pipeline overview

```text
docs/                               # Source documents
    |
    v
[extract_knowledge_modules_from_docs.py]
    | Parse frontmatter, auto-detect intents/audiences
    | Smart paragraph chunking (~1400 chars, split on H2/H3)
    v
knowledge_modules/                  # YAML knowledge modules
    |
    v
[validate_knowledge_modules.py]
    | Check YAML syntax, validate schema
    | Detect duplicate IDs, check dependency graph (no cycles)
    v
reports/knowledge_modules_report.json
    |
    v
[generate_knowledge_retrieval_index.py]
    | Load active modules, create retrieval records
    | Include metadata (intents, audiences, channels, tags)
    v
docs/assets/knowledge-retrieval-index.json    # JSON index (Algolia + FAISS input)
    |
    v (optional)
[generate_embeddings.py]
    | Embed each module/chunk (text-embedding-3-small, 1536 dims)
    | Normalize vectors (L2), build FAISS IndexFlatIP
    v
docs/assets/retrieval.faiss                   # FAISS binary index
docs/assets/retrieval-metadata.json           # Metadata sidecar
    |
    v (optional)
[run_retrieval_evals.py]
    | Evaluate precision@k, recall@k, hallucination rate
    | Compare against golden dataset (config/retrieval_eval_dataset.yml)
    v
reports/retrieval_evals_report.json
```

### Knowledge module schema

Every module (auto-extracted or manual) follows the schema in `knowledge-module-schema.yml`:

| Field | Required | Constraints |
| --- | --- | --- |
| `id` | Yes | Kebab-case, pattern `^[a-z0-9-]+$`, unique across all modules |
| `title` | Yes | 10-90 characters |
| `summary` | Yes | 30-240 characters (maps to document `description` in frontmatter) |
| `intents` | Yes | Non-empty list: `install`, `configure`, `troubleshoot`, `optimize`, `secure`, `migrate`, `automate`, `compare`, `integrate` |
| `audiences` | Yes | Non-empty list: `beginner`, `practitioner`, `operator`, `developer`, `architect`, `sales`, `support`, `all` |
| `channels` | Yes | Non-empty list: `docs`, `in-product`, `assistant`, `automation`, `field`, `sales` |
| `priority` | Yes | Integer 1-100 |
| `status` | Yes | `active` or `deprecated` |
| `owner` | Yes | 3-120 characters |
| `last_verified` | Yes | Date `YYYY-MM-DD` |
| `dependencies` | No | List of module IDs (acyclic graph enforced) |
| `tags` | No | Max 8 tags |
| `content.docs_markdown` | Yes | Min 80 characters -- the documentation chunk |
| `content.assistant_context` | Yes | Min 60 characters -- LLM context for retrieval |

### How extraction maps documents to modules

The extractor (`extract_knowledge_modules_from_docs.py`) makes these automatic decisions:

**Intent inference from content_type and content:**

| Signal | Inferred intent |
| --- | --- |
| `content_type: tutorial` or `content_type: how-to` | `configure` |
| `content_type: troubleshooting` or content contains "error"/"fix" | `troubleshoot` |
| `content_type: reference` or `content_type: concept` | `integrate` |
| Content contains "secure"/"auth" | `secure` |
| No match | `configure` (fallback) |

**Audience inference from content_type:**

| Content type | Audiences |
| --- | --- |
| `tutorial` | `[beginner, practitioner]` |
| `reference`, `concept` | `[developer, operator]` |
| `troubleshooting` | `[support, operator]` |
| Default | `[practitioner, developer]` |

**Chunking rules:**

- Max chunk size: ~1400 characters
- Split priority: H2 headers first, then H3 headers, then paragraphs
- Each chunk becomes a separate module with ID: `auto-{filename}-{chunk-index}`
- Multi-chunk documents get "Part N" appended to title

### Writing docs for optimal RAG extraction

Claude MUST follow these rules to produce documents that extract into high-quality knowledge modules:

1. **Use descriptive H2/H3 headings** -- they become chunk boundaries. "Configure HMAC authentication" extracts better than "Configuration"
1. **Keep sections under 1400 characters** -- prevents mid-paragraph splitting that degrades retrieval quality
1. **Set `content_type` accurately** -- drives intent inference. A troubleshooting guide tagged as `reference` gets wrong intents
1. **Write informative first paragraphs** -- the document `description` becomes the module `summary` (30-240 chars), used in retrieval ranking
1. **Add specific `tags`** -- tags propagate to modules and enable filtered retrieval queries
1. **Include concrete facts in every section** -- facts (numbers, code, config values) improve both GEO scores and retrieval relevance
1. **One topic per section** -- sections that cover multiple topics produce unfocused chunks that match too many queries

### Running the pipeline

**After every document create/update, Claude MUST run these three commands in order:**

```bash
# Step 1: Extract modules from docs (removes old auto-modules, creates new ones)
python3 scripts/extract_knowledge_modules_from_docs.py \
  --docs-dir docs --modules-dir knowledge_modules \
  --report reports/knowledge_auto_extract_report.json

# Step 2: Validate all modules (schema, uniqueness, dependency graph)
python3 scripts/validate_knowledge_modules.py

# Step 3: Rebuild the retrieval index
python3 scripts/generate_knowledge_retrieval_index.py
```

**Optional advanced steps (run in weekly batch or on-demand):**

```bash
# Build FAISS embeddings (requires OpenAI API key for text-embedding-3-small)
python3 scripts/generate_embeddings.py

# Build knowledge graph (JSON-LD)
python3 scripts/generate_knowledge_graph_jsonld.py \
  --modules-dir knowledge_modules \
  --output docs/assets/knowledge-graph.jsonld \
  --report reports/knowledge_graph_report.json

# Evaluate retrieval quality (precision, recall, hallucination rate)
python3 scripts/run_retrieval_evals.py \
  --index docs/assets/knowledge-retrieval-index.json \
  --report reports/retrieval_evals_report.json \
  --top-k 3 --min-precision 0.5 --min-recall 0.5 --max-hallucination-rate 0.5
```

### Retrieval strategies at runtime

The Ask AI runtime (`runtime/ask-ai-pack/app/retrieval.py`) supports three retrieval strategies. Claude should understand these to write docs that perform well across all modes:

1. **Token-overlap search (baseline fallback):** counts question tokens found in module title + summary + assistant_excerpt + intents. Modules with higher overlap and priority rank higher. Works without embeddings.
1. **Semantic search (FAISS):** embeds the question, finds nearest neighbors in the FAISS index. Optional HyDE (Hypothetical Document Embeddings) generates a hypothetical answer first, then embeds that instead.
1. **Hybrid search (RRF -- Reciprocal Rank Fusion):** combines semantic and token-overlap rankings. Optional cross-encoder reranking refines top candidates.

**Chunk deduplication:** when chunked retrieval is active, only the highest-ranked chunk per parent module is returned (prevents flooding context with chunks from a single document).

### Configuration

RAG pipeline behavior is controlled by `config/ask-ai.yml`:

| Setting | Default | Purpose |
| --- | --- | --- |
| `semantic_retrieval` | `true` | Use FAISS or fall back to token-overlap |
| `max_context_modules` | `6` | Max modules included in LLM context |
| `chunking.max_tokens` | `750` | Per-chunk token limit for embedding |
| `chunking.overlap_tokens` | `100` | Token overlap between consecutive chunks |
| `reranking.enabled` | `true` | Cross-encoder reranking of top candidates |
| `hybrid_search.enabled` | `true` | RRF fusion of semantic + token-overlap |
| `hyde.enabled` | `true` | Hypothetical Document Embeddings |

## Full SEO and GEO optimization rules

**These are the exact 24 checks (8 GEO + 16 SEO) enforced by `scripts/seo_geo_optimizer.py`. Every document MUST pass all of them.**

### GEO rules (LLM and AI search optimization)

GEO rules optimize documents for retrieval by large language models and AI-powered search engines.

**Configuration constants:**

```python
GEO_RULES = {
    "first_para_max_words": 60,
    "max_words_without_fact": 200,
    "meta_desc_min_chars": 50,
    "meta_desc_max_chars": 160,
    "min_heading_words": 3,
    "generic_headings": [
        "overview", "introduction", "configuration", "setup",
        "details", "information", "general", "notes", "summary"
    ],
    "definition_patterns": [
        r"\bis\b", r"\benables?\b", r"\bprovides?\b", r"\ballows?\b",
        r"\bcreates?\b", r"\bprocesses?\b", r"\bexecutes?\b"
    ],
    "fact_patterns": [
        r"\d+", r"`[^`]+`", r"\bdefault\b", r"\bport\b",
        r"\bversion\b", r"\bMB\b", r"\bGB\b", r"\bms\b",
        r"```", r"\bhttp[s]?://\b"
    ]
}
```

**All 8 GEO checks:**

| ID | Rule name | Severity | Threshold | What it checks |
| --- | --- | --- | --- | --- |
| GEO-1 | `meta-description-missing` | error | Must exist | Frontmatter `description` field is present |
| GEO-1b | `meta-description-short` | warning | Min 50 characters | Description is not too short for search snippets |
| GEO-1c | `meta-description-long` | warning | Max 160 characters | Description is not too long (gets truncated in search) |
| GEO-2 | `first-paragraph-too-long` | warning | Max 60 words | First paragraph is concise enough for LLM extraction |
| GEO-3 | `first-paragraph-no-definition` | suggestion | Must contain: is, enables, provides, allows, creates, processes, or executes | First paragraph contains an explicit definition pattern |
| GEO-4 | `heading-generic` | warning | Not in banned list | Headings are descriptive, not generic (banned: overview, introduction, configuration, setup, details, information, general, notes, summary) |
| GEO-5 | `heading-hierarchy-skip` | error | No skipping levels | Heading levels do not skip (H2 to H4 is invalid) |
| GEO-6 | `low-fact-density` | warning | Max 200 words between facts | Content includes concrete facts (numbers, code, config values) at least every 200 words |

### SEO rules (search engine optimization)

SEO rules optimize documents for traditional search engines (Google, Bing).

**Configuration constants:**

```python
SEO_RULES = {
    "title_min_chars": 10,
    "title_max_chars": 70,
    "max_url_depth": 4,
    "min_internal_links": 1,
    "max_image_without_alt_pct": 0,
    "min_content_words": 100,
    "max_line_length_for_mobile": 120,
}
```

**All 14 SEO checks:**

| ID | Rule name | Severity | Threshold | What it checks |
| --- | --- | --- | --- | --- |
| SEO-01 | `seo-title-missing` / `seo-title-short` / `seo-title-long` | error / warning / warning | 10-70 characters | Title exists and is within optimal length |
| SEO-02 | `seo-title-keyword-mismatch` | suggestion | 50% overlap | Title contains keywords from the filename |
| SEO-03 | `seo-url-depth` | warning | Max 4 levels | File path depth does not exceed 4 levels |
| SEO-04 | `seo-url-naming` | warning | Kebab-case only | Filename uses lowercase with hyphens (no underscores or uppercase) |
| SEO-05 | `seo-img-no-alt` | warning | 0% without alt | Every image has alt text |
| SEO-06 | `seo-low-internal-links` | suggestion | Min 1 internal link | Document has at least 1 internal cross-reference |
| SEO-07 | `seo-bare-url` | warning | Zero bare URLs | All URLs use `[descriptive text](url)` format |
| SEO-08 | `seo-path-special-chars` | warning | No special characters | Filename contains only alphanumeric characters and hyphens |
| SEO-09 | `seo-long-lines` | warning | Max 120 characters, max 5 violations | Lines outside code blocks do not exceed 120 characters |
| SEO-10 | `seo-heading-keyword-gap` | suggestion | At least 1 shared keyword | H2 headings share at least one keyword with the title |
| SEO-11 | `seo-no-freshness` | suggestion | Must exist | Frontmatter contains `last_reviewed` or `date` field |
| SEO-12 | `seo-thin-content` | warning | Min 100 words | Document has at least 100 words of content |
| SEO-13 | `seo-duplicate-heading` | warning | Zero duplicates | No two headings have the same text |
| SEO-14 | `seo-no-structured-data` | suggestion | At least 1 element | Document contains structured data markup (tables, code blocks, or lists) |

<!-- VERIOPS_MANAGED_BLOCK:START -->
## VeriOps Managed Local Workflow

When user asks to run documentation automation, ALWAYS:
1. Read `docsops/config/client_runtime.yml`.
1. Read `docsops/policy_packs/selected.yml`.
1. Read `glossary.yml` before generating docs and use preferred terminology.
   If a term already exists in glossary, use the preferred form and do not substitute synonyms.
1. If you introduce a new project term, add a marker in docs:
   `<!-- glossary:add: Term | Description | alias1, alias2 -->`.
1. Run `docsops/scripts/sync_project_glossary.py` when glossary markers are present.
1. Run only scripts from `docsops/scripts/` that are required by enabled modules.
1. Block publish if verification fails.
1. Return a short report: changed files, checks passed/failed, publish targets.

Do not invent ad-hoc pipeline logic outside these files.
<!-- VERIOPS_MANAGED_BLOCK:END -->
