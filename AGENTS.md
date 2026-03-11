# Codex instructions for documentation pipeline

## Write documents right the first time

**Codex, you MUST follow ALL these rules to avoid 20 iterations of fixes.**
**Every document you create MUST pass ALL linters on the first try.**

## Project overview

This is an automated documentation pipeline for technical products. When writing or editing documentation, follow these rules strictly to ensure all linting checks pass.

## Mandatory pipeline execution for API docs

When a user asks to generate or update OpenAPI from planning notes, you MUST run the API-first pipeline flow. Do not generate ad-hoc API files without running the flow.

Required behavior:

\11. Treat planning notes as source input artifact.
\11. Generate OpenAPI from notes using pipeline scripts.
\11. Run full API-first checks (contract validation, lint stack, stub generation, self-verification, sandbox/docs sync).
\11. Report results and produced artifact paths.

Hard rule:

- If request intent is `generate OpenAPI`, `API-first`, or `planning notes -> spec`, always use pipeline entry points (`scripts/run_api_first_flow.py` and related scripts), not freeform one-off generation.

## Stripe-level documentation quality principles

**Quality bar requirement:** every generated document must be equal to or better than Stripe documentation quality (clarity, structure, accuracy, examples, and usability).

### Write for humans first, search engines second

**Every document MUST:**

\11. **Start with the user's goal** - What are they trying to achieve?
\11. **Provide working code immediately** - Show, don't tell
\11. **Explain the why, not just the how** - Context matters
\11. **Include realistic examples** - Not "foo/bar" but actual use cases
\11. **Anticipate next steps** - What will they need after this?

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

\11. Simple case first (80% of users)
\11. Common variations (15% of users)
\11. Advanced scenarios (5% of users)

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

\11. **Check for relevant templates in `templates/` directory:**

- If a matching template exists, use it as base
- Copy it: `cp templates/[template] docs/[section]/[new-file].md`
- Edit content while keeping structure

\11. **OR use VS Code snippets from `.vscode/docs.code-snippets`:**

- Type snippet prefix (doc-tutorial, doc-howto, etc.) and press Tab
- Ensures consistent structure across documentation

\11. **If no template matches, create carefully:**

- Follow the structure from similar existing documents
- Include all required frontmatter fields
- Follow all formatting and SEO/GEO rules

\11. **ALWAYS update `mkdocs.yml` navigation:**

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
=== "Cloud"

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

Before committing, these checks run automatically:

\11. **Vale** (style - American English, Google/Microsoft Style Guide, write-good)
\11. **markdownlint** (formatting)
\11. **cspell** (spelling)
\11. **validate_frontmatter.py** (metadata)
\11. **seo_geo_optimizer.py** (comprehensive SEO/GEO optimization)

**Vale runs with strict configuration - no --no-exit flag.**

- ALL Vale errors and warnings block commits
- Write correctly the first time to avoid iterations
- Check Vale output carefully: it shows exactly what needs fixing

To run manually:

```bash
# Run Vale style checks (MUST pass!)
vale docs/path/to/file.md

# Run all SEO/GEO checks
python3 scripts/seo_geo_optimizer.py docs/

# Run with auto-fix
python3 scripts/seo_geo_optimizer.py docs/ --fix

# Run all checks at once
npm run lint

# Individual checks
markdownlint docs/path/to/file.md
```

## Creating new documents

### Use templates and snippets for consistency

**ALWAYS use existing templates and snippets when creating new documentation:**

\11. **Check for existing templates first:**

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

\11. **Copy the most relevant template:**

   ```bash
   # Example: Creating a new webhook how-to guide
   cp templates/webhooks-guide.md docs/how-to/your-new-webhook-guide.md

```

\11. **OR use VS Code snippets (preferred for consistency):**

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

\11. **Determine the correct location:**

- `docs/getting-started/` - Tutorials and quickstarts
- `docs/how-to/` - Step-by-step task guides
- `docs/concepts/` - Understanding and theory
- `docs/reference/` - API, configuration, specifications
- `docs/reference/nodes/` - Node-specific reference
- `docs/troubleshooting/` - Problem resolution
- `docs/` - Top-level pages (index, tags, etc.)

\11. **Update navigation in mkdocs.yml:**

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

\11. **File naming conventions:**

- Use kebab-case: `configure-webhook-trigger.md`
- Be descriptive: `webhook-hmac-authentication.md` not `auth.md`
- Match the title (slugified)

\11. **Content requirements:**

- Fill in all required frontmatter fields
- Keep first paragraph under 60 words
- Include concrete examples and code
- Follow GEO and style rules

\11. **Validate before committing:**

   ```bash
   # Run all checks
   npm run lint

   # Or individual checks
   python3 scripts/validate_frontmatter.py
   python3 scripts/seo_geo_optimizer.py docs/your-new-file.md

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

\11. **Automatic location selection based on content_type:**

```text
   content_type: tutorial → docs/getting-started/
   content_type: how-to → docs/how-to/
   content_type: concept → docs/concepts/
   content_type: reference → docs/reference/
   content_type: troubleshooting → docs/troubleshooting/

```

\11. **Automatic mkdocs.yml update - Claude MUST:**

- Read current mkdocs.yml structure
- Find the appropriate nav section based on content_type
- Add the new document with a descriptive title
- Maintain logical ordering (alphabetical or by complexity)
- Example commit message: "Add webhook authentication guide to how-to section"

\11. **Smart placement logic Claude should follow:**

   ```yaml
   # If adding a new webhook how-to:

\11. File goes in: docs/how-to/configure-webhook-auth.md
\11. Update mkdocs.yml nav section "How-To Guides"
\11. Place alphabetically or after related webhook docs
\11. Use descriptive title: "Configure webhook authentication"

```yaml

\11. **GitHub Actions will verify:**
   - No orphaned pages (files not in nav)
   - Proper categorization
   - Creates issues if navigation needs fixing

\11. **Example nav update:**

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

\11. First item
\11. Second item
\11. Third item

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

\11. Check `templates/` directory for matching template
\11. Copy the template structure exactly
\11. Templates are PRE-VALIDATED to pass all checks
\11. DO NOT modify the formatting structure

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

\11. **Select template/snippet:**
   - Check `templates/` for matching template
   - OR use VS Code snippet (doc-tutorial, doc-howto, etc.)
   - NEVER write from scratch when a suitable template exists; if none exists, create a new template first

\11. **Choose location:**
   - Based on content_type in frontmatter
   - Place in correct folder (getting-started/, how-to/, etc.)

\11. **Update mkdocs.yml:**
   - Add to appropriate nav section
   - Use descriptive title
   - Maintain logical order

\11. **Follow formatting rules:**
   - Blank lines around headings/lists/code
   - Only one H1
   - Code blocks with language
   - No emoji in Python

\11. **Validate:**
   - Run linting checks
   - Ensure frontmatter complete
   - First paragraph under 60 words

\11. **Self-verify (MANDATORY):**
   - Execute all code blocks and verify output matches
   - Run all shell commands and verify results
   - Fact-check all specific claims (versions, ports, paths, counts)
   - Replace any mismatches with verified correct values
   - Use standard placeholders for environment-specific values
   - Log verification summary (X blocks executed, Y facts checked, Z corrections)

## Pull Request Reviews

### 🔴 CRITICAL: Fix BOTH Errors AND Warnings

**When reviewing pull requests or fixing linting issues, Claude MUST:**

\11. **Fix ALL errors (red)** - These block commits and merges
\11. **Fix ALL warnings (yellow)** - These indicate quality issues
\11. **Not ignore any linting output** - Both errors and warnings need attention

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

\11. **Pre-commit hooks** (local) - Run automatically before commit
\11. **CI/CD checks** (GitHub) - Same checks run on PR/push

Both use IDENTICAL rules, so if it passes locally, it passes in CI.

## Self-verification layer (post-generation quality gate)

**After generating or editing ANY documentation, Codex MUST run a self-verification pass before committing.**

This verification layer catches errors that linting tools cannot detect: wrong code output, broken commands, incorrect facts, and stale assertions. It replaces the need for manual human verification of technical accuracy.

### Why self-verification matters

- Linters check **style and formatting** -- they cannot verify **technical correctness**
- A code example that passes markdownlint can still produce wrong output
- A shell command that looks valid can fail or produce unexpected results
- A claimed "default port 5678" might have changed to 8080 in the latest release
- Self-verification catches these errors **before** human review, reducing review cycles from 5+ rounds to 1-2

### Step 1: Execute all code examples

**For every fenced code block with a language tag, Codex MUST:**

\11. **Identify executable blocks** -- blocks tagged `python`, `javascript`, `bash`, `shell`, `typescript`, `ruby`, `go`, `java`, `curl`
\11. **Execute each block** in a sandboxed environment (no network calls, no filesystem writes outside temp)
\11. **Capture stdout and stderr** from execution
\11. **Compare actual output against documented output** (the `<!-- expected-output: ... -->` comment or output block that follows the code block)
\11. **If output mismatches:** replace the documented output with the actual output
\11. **If execution fails:** fix the code so it runs, or add a comment explaining why it cannot run in isolation (for example, requires API key)

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

**For every bash/shell command documented, Codex MUST:**

\11. **Run the command** (with safe substitutions for destructive commands)
\11. **Verify the exit code** matches expectations (0 for success)
\11. **Compare output** against what the document claims
\11. **Fix discrepancies** -- update the documented output to match reality

**Safe execution rules:**

- **Read-only commands** (`ls`, `cat`, `grep`, `find`, `which`, `--version`, `--help`): execute directly
- **Write commands** (`mkdir`, `cp`, `mv`, `rm`): execute in a temp directory
- **Install commands** (`npm install`, `pip install`): execute with `--dry-run` if supported, otherwise skip and note
- **Destructive commands** (`rm -rf`, `drop table`): NEVER execute -- verify syntax only
- **Commands with placeholders** (`<your-api-key>`, `YOUR_TOKEN`): skip execution, verify syntax

### Step 3: Fact-check concrete assertions

**Codex MUST verify every specific claim in the document:**

\11. **Version numbers** -- check against actual installed versions or official documentation
\11. **Port numbers** -- verify against default configuration files or `_variables.yml`
\11. **File paths** -- verify that referenced files and directories exist in the project
\11. **URL paths** -- verify that linked documentation pages exist
\11. **Configuration values** -- verify against actual config files (`.vale.ini`, `mkdocs.yml`, `package.json`)
\11. **CLI flags and options** -- verify with `--help` output
\11. **Error messages** -- verify they match actual error output
\11. **Numeric claims** -- verify counts ("supports 5 methods" -- count them)

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

**When verification finds a discrepancy, Codex MUST:**

\11. **Replace the incorrect value** with the verified correct value
\11. **Use placeholders** for environment-specific values:

- API keys: `YOUR_API_KEY`
- Tokens: `YOUR_TOKEN`
- User-specific paths: `~/.config/your-app/`
- Domain names: `your-domain.example.com`
- IP addresses: `192.0.2.1` (documentation range per RFC 5737)
\11. **Add a comment** if the original value was intentionally approximate (for example, "approximately 100 ms" does not need exact verification)
\11. **Log all changes** -- after verification, list what was corrected:

```text
Verification summary:
- Fixed: print(2+2) output changed from "5" to "4"
- Fixed: Default port updated from 5678 to 8080 (per _variables.yml)
- Verified: 12 code blocks executed, 12 passed
- Skipped: 3 blocks (require external API)
- Fact-checked: 8 assertions, 7 correct, 1 fixed
```

### Step 5: Verify internal consistency

**Codex MUST check that the document does not contradict itself:**

\11. **Cross-reference within the document** -- if section 1 says "port 5678" and section 3 says "port 8080," flag and fix
\11. **Cross-reference with `_variables.yml`** -- all hardcoded values that exist in variables must use the variable
\11. **Cross-reference with other docs** -- if this document links to another, verify the linked content is consistent
\11. **Verify code and text agree** -- if text says "returns a list" but code shows a dict, fix the text

### Verification checklist (run after every generation)

**Codex, run this checklist AFTER writing the document but BEFORE committing:**

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

**Codex MUST ALWAYS start from templates/snippets when available. If no suitable template exists, Codex MUST create a new template in project format first, then generate docs from that template.**

### Why this is mandatory

Templates are pre-validated to pass all linters. When you write from scratch, you introduce formatting errors, missing sections, and inconsistent structure. Templates eliminate this entirely.

### Complete template inventory (27 templates)

Before creating ANY document, check `templates/` for a matching template:

| Document type | Template file | VS Code snippet |
| --- | --- | --- |
| Step-by-step learning | `tutorial.md` | `doc-tutorial` |
| Task-oriented guide | `how-to.md` | `doc-howto` |
| Explanation page | `concept.md` | `doc-concept` |
| Technical specification | `reference.md` | `doc-reference` |
| Problem-solution | `troubleshooting.md` | `doc-troubleshoot` |
| Quick onboarding | `quickstart.md` | `doc-tutorial` |
| API endpoint docs | `api-reference.md` | `doc-reference` |
| Auth patterns | `authentication-guide.md` | `doc-howto` |
| Version upgrade | `migration-guide.md` | `doc-howto` |
| Production setup | `deployment-guide.md` | `doc-howto` |
| Webhook integration | `webhooks-guide.md` | `doc-howto` |
| SDK client library | `sdk-reference.md` | `doc-reference` |
| Security policy | `security-guide.md` | `doc-reference` |
| Config setup | `configuration-guide.md` | `doc-howto` |
| Config options table | `configuration-reference.md` | `doc-reference` |
| Third-party integration | `integration-guide.md` | `doc-howto` |
| Testing approach | `testing-guide.md` | `doc-howto` |
| Error codes/recovery | `error-handling-guide.md` | `doc-reference` |
| System architecture | `architecture-overview.md` | `doc-concept` |
| Guidelines/patterns | `best-practices.md` | `doc-concept` |
| Business use-case | `use-case.md` | `doc-concept` |
| Version changelog | `release-note.md` | `doc-release` |
| Release notes | `changelog.md` | `doc-release` |
| FAQ page | `faq.md` | `doc-reference` |
| Terminology | `glossary-page.md` | `doc-reference` |
| PLG persona page | `plg-persona-guide.md` | `doc-tutorial` |
| PLG value page | `plg-value-page.md` | `doc-concept` |
| User guide | `user-guide.md` | `doc-howto` |
| Administration guide | `admin-guide.md` | `doc-howto` |
| Upgrade guide | `upgrade-guide.md` | `doc-howto` |
| Single API endpoint | `api-endpoint.md` | `doc-reference` |

### Template selection process

\11. Read the user's request. Identify the document type.
\11. Find the matching template from the table above.
\11. Copy the template: `cp templates/[template] docs/[section]/[filename].md`
\11. Edit the content while preserving the template structure.
\11. Do NOT add sections that are not in the template.
\11. Do NOT remove required sections from the template.

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
- Be descriptive: `max_payload_size_mb`, not `payload_size`.
- Include units in the name: `request_timeout_seconds`, `rate_limit_requests_per_minute`.
- Group related variables with YAML nesting: `env_vars.port`, `env_vars.api_key`.
- NEVER use generic names: `port` is bad, `default_port` is good, `webhook_listener_port` is better.

### What to do if a variable does not exist

\11. Check `docs/_variables.yml` for the value.
\11. If it does not exist, add it with a descriptive name.
\11. Use the new variable in the document.
\11. Document the new variable with a comment in `_variables.yml`.

### Detection of hardcoded values

After writing a document, scan it for hardcoded values that should be variables:

- Port numbers (5678, 8080, 3000)
- Version numbers (1.0.0, 2.5.0)
- URLs (`https://app.example.com`)
- Product names (if they appear literally instead of as `{{ product_name }}`)
- Email addresses

Replace each with the corresponding variable.

## MANDATORY: Auto-correction during verification

**When self-verification finds an error, Codex MUST fix it immediately, not just report it.**

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

**This is the full step-by-step process Codex MUST follow for every document:**

\11. **Identify document type and locale** from user request. Default locale: `en`.
\11. **Select matching template** from `templates/`; if none exists, create a new template in the same project format first.
\11. **Copy template** to correct location: `docs/{locale}/{content_type_dir}/{slug}.md`.
\11. **Read variables** -- use `docs/_variables.yml` merged with `docs/{locale}/_variables.yml` if it exists.
\11. **Fill template** with actual content, following Stripe-quality standards.
\11. **Format correctly**: blank lines around headings, lists, code blocks. One H1 only.
\11. **Apply style rules**:

- English: American English, active voice, no weasel words, no contractions.
- Non-English: apply equivalent rules manually (see "Quality enforcement for non-English documentation").
\11. **Keep first paragraph under locale word limit** (en: 60, ru: 80, de: 70) with a clear definition.
\11. **Set i18n frontmatter fields** if locale is not `en`: `language`, `translation_of`, `source_hash`.
\11. **Execute all code blocks** and verify output matches.
\11. **Run all shell commands** and verify results.
\11. **Fact-check all assertions** (versions, ports, paths, URLs, counts).
\11. **Replace hardcoded values** with variables from `_variables.yml`.
\11. **Check internal consistency** (no contradictions within the document).
\11. **Update `mkdocs.yml`** navigation with the new page.
\11. **Run validation**: `npm run validate:minimal`.
\11. **For non-English docs**: run the translation quality checklist (active voice, weasel words, terminology, spelling).
\11. **Log verification summary** with counts of blocks executed, facts checked, corrections made.

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
- `source_hash`: SHA-256 of the source document body at translation time

### Locale-aware variables

`docs/_variables.yml` is the base (English defaults). Each locale can override values in `docs/{locale}/_variables.yml`:

```yaml
# docs/ru/_variables.yml (only override what differs)
product_tagline: "Platform avtomatizatsii rabochikh protsessov"
```

Technical values (ports, URLs, versions) stay shared.

## MANDATORY: Quality enforcement for non-English documentation

**Vale, write-good, proselint, and cspell do NOT support non-English languages.** For English docs these tools enforce quality automatically. For all other languages, **Codex IS the quality linter.** Codex MUST apply equivalent quality rules manually when writing or reviewing non-English documentation.

### What automated tools check per language

| Check | English (`docs/en/`) | Other locales (`docs/ru/`, etc.) |
| --- | --- | --- |
| Vale: Google style guide | Automated | **Codex enforces manually** |
| Vale: write-good | Automated | **Codex enforces manually** |
| Vale: AmericanEnglish | Automated | N/A (use native spelling) |
| Vale: GEO (structure) | Automated | Automated |
| cspell (spelling) | Automated | **Skipped** (Codex checks) |
| markdownlint (formatting) | Automated | Automated |
| frontmatter validation | Automated | Automated |
| SEO/GEO optimizer | Automated (en rules) | Automated (locale rules) |

### Rules Codex MUST enforce for non-English documentation

**When writing or editing ANY non-English document, Codex MUST apply ALL of the following rules.** These are the same rules that Vale, write-good, and proselint enforce for English, adapted for the target language.

**1. Active voice (equivalent of write-good passive voice check):**

- Use active voice in the target language
- Russian: "Nastroyte webhook" (active), NOT "Webhook dolzhen byt' nastroyen" (passive)
- German: "Konfigurieren Sie den Webhook" (active), NOT "Der Webhook muss konfiguriert werden" (passive)
- The subject should perform the action, not receive it

**2. No weasel words (equivalent of write-good weasel word check):**

- Do not use vague qualifiers in any language
- Banned in Russian: "prosto" (just/simple), "legko" (easy), "bystro" (quickly), "mnogo" (many/various), "razlichnye" (various), "nekotorye" (some), "obychno" (usually)
- Banned in German: "einfach" (simple), "schnell" (quickly), "verschiedene" (various), "einige" (some)
- Replace with specific values: "za 5 sekund" not "bystro," "3 metoda" not "neskolko metodov"

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

- Codex MUST check spelling and grammar in the target language
- cspell cannot do this for non-English, so Codex is the only checker
- Pay attention to: declension, case agreement, verb conjugation
- Russian: check grammatical cases, verb aspects
- German: check compound words, article genders, cases

**8. Consistent terminology within a document:**

- If you translate "workflow" as "rabochiy protsess" in paragraph 1, use the same translation throughout
- Do NOT alternate between translations of the same term
- Create a mental glossary and stick to it

### Quality checklist for non-English documents

**Before saving ANY non-English document, Codex MUST verify:**

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

After generating or editing a non-English document, Codex MUST add a verification note:

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

**Codex MUST follow this workflow when the user says "Process reports/consolidated_report.json" or hands over the consolidated report.**

### How the consolidated report is generated

In recommended mode, scheduler runs `docsops/scripts/run_weekly_gap_batch.py` in the client repository and:

\11. Runs gap analysis (`doc_gaps_report.json`)
\11. Runs KPI wall + SLA evaluation (`kpi-wall.json`, `kpi-sla-report.json`)
\11. Runs drift checks (`api_sdk_drift_report.json`)
\11. Runs `scripts/consolidate_reports.py` to produce `reports/consolidated_report.json`
\11. Auto-extracts knowledge modules from docs (`extract_knowledge_modules_from_docs.py`)
\11. Validates modules and rebuilds retrieval index (`validate_knowledge_modules.py`, `generate_knowledge_retrieval_index.py`)
\11. Runs any enabled `custom_tasks.weekly`

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

When processing action items that involve **removed features, deprecated endpoints, or replaced functionality**, Codex MUST update the document lifecycle status:

**For deprecated features:**

\11. Set frontmatter: `status: deprecated`, `deprecated_since: "YYYY-MM-DD"`, `replacement_url: "/path/to/new-doc"`
\11. Add a warning admonition at the top of the document body:

   ```markdown
   !!! warning "Deprecated"
       This feature is deprecated since [date].
       Use [new feature](/path/to/new-doc) instead.
   ```

\11. Do NOT delete the document—users may still reference it

**For removed features:**

\11. Set frontmatter: `status: removed`, `removal_date: "YYYY-MM-DD"`, `replacement_url: "/path/to/migration"`, `noindex: true`
\11. Replace the document body with a redirect notice:

   ```markdown
   !!! danger "Removed"
       This feature was removed on [date].
       See the [migration guide](/path/to/migration) for alternatives.
   ```

\11. The `noindex: true` flag prevents search engines from indexing the page
\11. The `lifecycle_manager.py` script automatically adds CSS classes and banners for these states

**When to set lifecycle status:**

- Gap report says `category: "removed_function"` → set `status: removed` on the relevant doc
- Drift report shows an endpoint was deleted from OpenAPI spec → set `status: deprecated` or `status: removed`
- Any action_item mentions deprecation, removal, or replacement → update lifecycle accordingly

### Per-document processing loop

For each document (new or updated):

\11. Write or update content following all rules in this file
\11. **Run self-verification (MANDATORY before linting):**

- Execute every code block in the document and verify the output matches what is documented. If the output differs, fix the documented output to match reality.
- Run every shell command in the document and verify it succeeds. If a command fails, fix the command or update the documented result.
- Fact-check every concrete assertion: version numbers (run `tool --version`), port numbers (check `docs/_variables.yml`), file paths (verify they exist), internal links (verify target files exist), configuration values (check source configs).
- Replace any mismatched values with verified correct values. Use variables from `docs/_variables.yml` instead of hardcoded values.
- Check internal consistency: if the document says "port 5678" in one section and "port 8080" in another, fix the contradiction.
- Walk through the document as if you are the user following the instructions step by step. If any step is unclear, incomplete, or produces unexpected results, fix it.
\11. Run `npm run validate:minimal`
\11. If linting fails, fix the issues and re-run (max 5 retries)
\11. If all 5 retries fail, log the document as blocked and move to the next item
\11. Update `mkdocs.yml` navigation if a new document was created
\11. Log a verification summary for this document:

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

\11. Stage all created and modified files so the user can review with `git diff --staged`:

   ```bash
   git add docs/ mkdocs.yml
   ```

\11. Produce a batch summary:

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

\11. Tell the user to review with:

   ```bash
   git diff --staged       # shows all changes including new files
   git diff --staged --stat  # shows summary of changed files
   ```

## Code-first API documentation workflow

**Use this workflow when the API code already exists and you need to generate documentation from it.**

Code-first means the source code (controllers, routes, models) is the source of truth. The OpenAPI spec and reference docs are derived from the code.

### 10-step code-first flow

\11. **Detect undocumented endpoints:**

   ```bash
   npm run gaps:code
   ```

   This runs `python3 -m scripts.gap_detection.cli code` and produces a report of endpoints found in code but missing from documentation.

\11. **Read the source code:**

- Locate controllers, routes, and model files
- Extract endpoint details: HTTP method, path, request body schema, response schema, authentication requirements, rate limits
- Note any middleware (validation, auth, logging)

\11. **Generate or update the OpenAPI spec:**

- Create or update `api/openapi.yaml` as the root spec file
- Use `$ref` pointers to per-resource files under `api/paths/`
- Place shared schemas under `api/components/schemas/`
- Place shared responses under `api/components/responses/`

\11. **Apply Stripe-quality descriptions:**

- Active voice, present tense
- Concrete examples with realistic data
- Every parameter has a description and example
- Every response code has a description and example body
- Follow all rules from the "OpenAPI spec quality rules" section below

\11. **Organize for maintainability:**

   ```text
   api/
     openapi.yaml              # Root spec with $ref to paths and components
     paths/
       users.yaml              # /users endpoints
       orders.yaml             # /orders endpoints
       webhooks.yaml           # /webhooks endpoints
     components/
       schemas/
         User.yaml
         Order.yaml
         Error.yaml
       responses/
         NotFound.yaml
         Unauthorized.yaml
         ValidationError.yaml
   ```

\11. **Use discriminator for polymorphic types:**

- Add `discriminator` with `propertyName` for union types
- Use `allOf` with a base `$ref` for inheritance hierarchies

\11. **Test against real endpoints:**

- Send actual HTTP requests to the running API
- Compare response status codes, headers, and body shapes against the spec
- Fix any mismatches in the spec

\11. **Compare responses with spec descriptions:**

- Verify that every field in the actual response appears in the schema
- Verify that example values match realistic data types
- Fix discrepancies in the spec, not in the code

\11. **Run Spectral lint:**

   ```bash
   npx spectral lint api/openapi.yaml --ruleset .spectral.yml
   ```

   The spec MUST pass with zero errors and zero warnings. See the "OpenAPI spec quality rules" section for all 18 rules.

\11. **Update reference docs and build:**
    - Generate or update reference docs using `templates/api-reference.md`
    - Run `npm run validate:minimal` on all changed docs
    - Run `npm run build` to verify the full site builds

**Key difference from API-first:** In code-first, you test against real running endpoints. You do NOT use a Prism mock server. Prism is only for the API-first workflow when code does not exist yet.

## API-first documentation workflow

**Use this workflow when you are designing a new API from scratch (no code exists yet).**

API-first means the OpenAPI specification is written first, and code is generated from it. The spec is the single source of truth.

### 11-step API-first flow

\11. **Parse the user brief:**

- Extract resources (nouns: users, orders, payments)
- Extract operations (verbs: create, list, update, delete)
- Extract schemas (data shapes, required fields, validation rules)
- Extract constraints (authentication, rate limits, pagination)

\11. **Map operations to HTTP methods:**

   | Operation | HTTP method | Path pattern | Success code |
   | --- | --- | --- | --- |
   | Create | POST | `/resources` | 201 |
   | List | GET | `/resources` | 200 |
   | Get one | GET | `/resources/{id}` | 200 |
   | Update (full) | PUT | `/resources/{id}` | 200 |
   | Update (partial) | PATCH | `/resources/{id}` | 200 |
   | Delete | DELETE | `/resources/{id}` | 204 |

\11. **Generate the root OpenAPI spec:**

- Create `api/openapi.yaml` with full `info` block (title, description, version, contact, license)
- Set `servers` array with at least mock and production URLs
- Define `security` schemes (Bearer token, API key, OAuth2)

\11. **Create per-resource path files:**

- One file per resource under `api/paths/`
- Use `$ref` from root spec to each path file
- Apply `discriminator` for polymorphic types
- Use `allOf` for inheritance

\11. **Apply all quality rules:**

- Follow every rule from the "OpenAPI spec quality rules" section below
- Every operation has `operationId`, `summary`, `description`, `tags`
- Every parameter has `description`, `example`, explicit `required`
- Every schema property has `description`, `type`, `example`
- All possible response codes are defined (200/201, 400, 401, 403, 404, 409, 429, 500)

\11. **Generate endpoint code with OpenAPI Generator:**

- Use the GitHub Actions workflow `.github/workflows/api-first-scaffold.yml`
- Or run locally with Docker:

     ```bash
     docker run --rm -v "${PWD}:/local" \
       openapitools/openapi-generator-cli:v7.7.0 generate \
       -i /local/api/openapi.yaml \
       -g typescript-express-server \
       -o /local/generated/server
     ```

- Generate client SDK:

     ```bash
     docker run --rm -v "${PWD}:/local" \
       openapitools/openapi-generator-cli:v7.7.0 generate \
       -i /local/api/openapi.yaml \
       -g typescript-axios \
       -o /local/generated/client
     ```

\11. **Deploy a Prism mock server:**

   ```bash
   npm run api:sandbox:mock
   ```

   This starts a Prism mock server using `docker-compose.api-sandbox.yml` that serves realistic responses based on the spec examples.

\11. **Test all endpoints against the mock:**

- Send requests to each endpoint
- Verify response status codes match the spec
- Verify response body shapes match schema definitions
- Verify example values are realistic and consistent

\11. **Fix discrepancies:**

- If mock responses do not match spec expectations, fix the spec
- Re-run Prism to confirm fixes
- Stop the mock server when done: `npm run api:sandbox:stop`

\11. **Run Spectral lint and all doc linters:**

    ```bash
    npx spectral lint api/openapi.yaml --ruleset .spectral.yml
    npm run validate:minimal
    ```

    Both MUST pass with zero errors and zero warnings.

\11. **Generate reference docs, build, and publish:**
    - Generate reference docs using `templates/api-reference.md` template
    - Update `mkdocs.yml` navigation
    - Run `npm run build` to verify the full site builds
    - Create a pull request with all changes

## Interactive diagrams

**When a document describes system architecture, data flow, or multi-component interactions, Codex MUST generate an interactive HTML diagram instead of a static Mermaid block.**

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

\11. Copy the template: `cp templates/interactive-diagram.html docs/diagrams/[name].html`
\11. Edit the HTML structure: add/remove layers and components (the `<!-- EDIT THIS SECTION -->` comments mark editable areas)
\11. Edit the `descriptions` object in the `<script>` section. Every component MUST have a rich description that appears in the info panel when the user clicks on it:

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

\11. Each component needs a `data-id` attribute that matches a key in `descriptions`
\11. Embed in the Markdown document using iframe:

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

## Full SEO and GEO optimization rules

**These are the exact 22 checks (8 GEO + 14 SEO) enforced by `scripts/seo_geo_optimizer.py`. Every document MUST pass all of them.**

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
