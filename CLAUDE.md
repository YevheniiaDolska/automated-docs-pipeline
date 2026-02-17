# Claude Code instructions for documentation pipeline

## Write documents right the first time

**Claude, you MUST follow ALL these rules to avoid 20 iterations of fixes.**
**Every document you create MUST pass ALL linters on the first try.**

## Project overview

This is an automated documentation pipeline for technical products. When writing or editing documentation, follow these rules strictly to ensure all linting checks pass.

## Stripe-level documentation quality principles

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

**IMPORTANT:** this pipeline includes comprehensive SEO/GEO optimization with 60+ automated checks. All content MUST pass:

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

1. **If no template matches, create carefully:**
   - Follow the structure from similar existing documents
   - Include all required frontmatter fields
   - Follow all formatting and SEO/GEO rules

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
product: both|n8n-cloud|n8n-self-hosted
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
- **Google Developer Style Guide** - Primary style guide for the documentation
- **write-good** - Clear, concise writing rules

**Specific Vale Rules to Follow:**

**American English:**

- Use American spelling: "color," "optimize," "analyze," "center"
- NOT British spelling variants
- Use "license" (verb and noun)
- Use "canceled" instead of British spelling

**Google Style Guide Requirements:**

- **Acronyms**: Write out on first use: "Application Programming Interface (API)"
- **Contractions**: Avoid them. Use "do not" instead of "don't"
- **Numbers**: Spell out one through nine, use numerals for 10 and above
- **Oxford comma**: Always use it: "red, white, and blue"
- **Headings**: Use sentence case, not Title Case
- **Lists**: Use parallel structure (all items start with same part of speech)

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

**Content tabs:**

```markdown
=== "n8n Cloud"

    Cloud-specific content

=== "Self-hosted"

    Self-hosted content

```

### Allowed tags

Use only these tags (defined in `mkdocs.yml`):

- Tutorial, How-To, Concept, Reference, Troubleshooting
- Cloud, Self-hosted
- Webhook, Nodes, AI

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

```yaml
# Product info
product_name: "ProductName"
product_full_name: "Product workflow automation"

# Versions
current_version: "1.50.0"
api_version: "v1"

# URLs
cloud_url: "https://app.n8n.cloud"
docs_url: "https://docs.n8n.io"

# Ports and paths
default_port: 5678
default_data_folder: "~/.n8n"

# Environment variables
env_vars:
  port: "N8N_PORT"
  webhook_url: "WEBHOOK_URL"

# Limits
max_payload_size_mb: 16
rate_limit_requests_per_minute: 60
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
Set the port using N8N_PORT  # Should use env_vars.port
```

## Pre-commit checks

Before committing, these checks run automatically:

1. **Vale** (style - American English, Google/Microsoft Style Guide, write-good)
1. **markdownlint** (formatting)
1. **cspell** (spelling)
1. **validate_frontmatter.py** (metadata)
1. **seo_geo_optimizer.py** (comprehensive SEO/GEO optimization)

**Vale runs with strict configuration - no --no-exit flag.**

- ALL Vale errors and warnings block commits
- Write correctly the first time to avoid iterations
- Check Vale output carefully: it shows exactly what needs fixing

To run manually:

```bash
# Run Vale style checks (MUST pass!)
vale docs/path/to/file.md

# Run all SEO/GEO checks
python scripts/seo_geo_optimizer.py docs/

# Run with auto-fix
python scripts/seo_geo_optimizer.py docs/ --fix

# Run all checks at once
npm run lint

# Individual checks
markdownlint docs/path/to/file.md
```

## Creating new documents

### Use templates and snippets for consistency

**ALWAYS use existing templates and snippets when creating new documentation:**

1. **Check for existing templates first:**

   ```bash
   ls templates/

```bash

   Available templates include:

   - `tutorial.md` - Step-by-step learning guides
   - `how-to.md` - Task-oriented guides
   - `concept.md` - Explanations and understanding
   - `reference.md` - Technical specifications
   - `troubleshooting.md` - Problem-solving guides
   - `quickstart.md` - Getting started quickly
   - `api-reference.md` - API documentation
   - `webhooks-guide.md` - Webhook-specific docs
   - And many more specialized templates

1. **Copy the most relevant template:**

   ```bash
   # Example: Creating a new webhook how-to guide
   cp templates/webhooks-guide.md docs/how-to/your-new-webhook-guide.md

```

1. **OR use VS Code snippets (preferred for consistency):**
   - Type the snippet prefix and press Tab
   - Available snippets:
     - `doc-tutorial` - Full tutorial with all sections
     - `doc-howto` - How-to guide structure
     - `doc-concept` - Concept explanation
     - `doc-reference` - Reference documentation
     - `doc-troubleshoot` - Troubleshooting guide
     - `fm` - Basic frontmatter only
     - `note`, `warning`, `tip` - Admonition blocks
     - `tabs` - Content tabs for cloud and self-hosted versions
     - `mermaid-flow` - Flow diagrams
     - `table-params` - Parameter tables

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

1. **Validate before committing:**

   ```bash
   # Run all checks
   npm run lint

   # Or individual checks
   python scripts/validate_frontmatter.py
   python scripts/seo_geo_optimizer.py docs/your-new-file.md

```bash

### Template Selection Guide

| If you're documenting this | Use this template | Location | Snippet |
| --- | --- | --- | --- |
| First-time setup | `quickstart.md` | `docs/getting-started/` | `doc-tutorial` |
| Step-by-step learning | `tutorial.md` | `docs/getting-started/` | `doc-tutorial` |
| Specific task | `how-to.md` | `docs/how-to/` | `doc-howto` |
| Architecture/theory | `concept.md` | `docs/concepts/` | `doc-concept` |
| API endpoints | `api-reference.md` | `docs/reference/` | `doc-reference` |
| Node details | `reference.md` | `docs/reference/nodes/` | `doc-reference` |
| Webhook features | `webhooks-guide.md` | Appropriate section | `doc-howto` |
| Common problems | `troubleshooting.md` | `docs/troubleshooting/` | `doc-troubleshoot` |
| Version changes | `release-note.md` | `docs/releases/` | `doc-release` |

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

- `doc-tutorial` - Full tutorial template
- `doc-howto` - How-to guide template
- `doc-concept` - Concept explanation template
- `doc-reference` - Reference page template
- `doc-troubleshoot` - Troubleshooting template
- `doc-release` - Release note template
- `fm` - Basic frontmatter
- `note`, `warning`, `tip` - Admonition blocks
- `tabs` - Content tabs
- `mermaid-flow`, `mermaid-seq` - Diagrams
- `table-params`, `table-compare` - Tables

### Config files

- `.vale.ini` - Style linting rules
- `.markdownlint.yml` - Markdown formatting rules
- `cspell.json` - Spelling dictionary
- `docs-schema.yml` - Frontmatter schema
- `glossary.yml` - Terminology glossary
- `mkdocs.yml` - Site configuration

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

When user asks to create new documentation, Claude MUST:

1. **Select template/snippet:**
   - Check `templates/` for matching template
   - OR use VS Code snippet (doc-tutorial, doc-howto, etc.)
   - NEVER write from scratch

1. **Choose location:**
   - Based on content_type in frontmatter
   - Place in correct folder (getting-started/, how-to/, etc.)

1. **Update mkdocs.yml:**
   - Add to appropriate nav section
   - Use descriptive title
   - Maintain logical order

1. **Follow formatting rules:**
   - Blank lines around headings/lists/code
   - Only one H1
   - Code blocks with language
   - No emoji in Python

1. **Validate:**
   - Run linting checks
   - Ensure frontmatter complete
   - First paragraph under 60 words

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
